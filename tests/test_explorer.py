"""Behavioural tests for the interactive explorer (site_src/explorer.html) in a real browser.

They move sliders, read the numbers the page shows, and check them against the Python package
or an analytic result; they also let the animations run and check what they converge to.
Needs Playwright with Chromium (`pip install -e ".[browser]"`, then
`python -m playwright install chromium`). Skipped when that is missing, unless the environment
variable QPLAY_REQUIRE_BROWSER is set (CI sets it, so a broken browser fails the build).
"""
import math
import os
import re
from pathlib import Path

import numpy as np
import pytest

from qplay import mechanics, quantum, statmech

pytestmark = pytest.mark.slow
REQUIRE = bool(os.environ.get("QPLAY_REQUIRE_BROWSER"))
PAGE = (Path(__file__).resolve().parents[1] / "site_src" / "explorer.html").as_uri()

if REQUIRE:
    from playwright.sync_api import sync_playwright
else:
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Exception as err:                       # browser binary missing
            if REQUIRE:
                raise
            pytest.skip(f"Chromium not available: {err}")
        yield b
        b.close()


def open_page(browser, width=1200, height=900, **context_options):
    context = browser.new_context(viewport={"width": width, "height": height}, **context_options)
    page = context.new_page()
    errors = []
    page.on("pageerror", lambda err: errors.append(str(err)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.route(re.compile(r"^https?://"), lambda route: route.abort())   # hermetic: no fonts or CDNs
    page.goto(PAGE)
    page.all_errors = errors
    return page


@pytest.fixture
def page(browser):
    page = open_page(browser)
    yield page
    assert [e for e in page.all_errors if "Failed to load resource" not in e] == []
    page.context.close()


def set_slider(page, element_id, value):
    page.evaluate("([id, v]) => { const el = document.getElementById(id); el.value = v;"
                  " el.dispatchEvent(new Event('input')); }", [element_id, str(value)])
    actual = float(page.eval_on_selector(f"#{element_id}", "el => el.value"))
    assert actual == pytest.approx(value), f"{element_id} snapped to {actual}; pick a value on its step"


def text(page, element_id):
    return page.text_content(f"#{element_id}").strip()


def number(page, element_id):
    match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", text(page, element_id))
    assert match, f"no number in #{element_id}: {text(page, element_id)!r}"
    return float(match.group())


def wait_until(page, js_condition, timeout=20_000):
    page.wait_for_function(js_condition, timeout=timeout)


def canvas_ink(page, element_id):
    """Fraction of the canvas's pixels that are not transparent (0 for a blank canvas)."""
    return page.evaluate("""id => { const c = document.getElementById(id);
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let n = 0; for (let i = 3; i < d.length; i += 4) if (d[i] > 0) n++;
        return n / (c.width * c.height); }""", element_id)


# ---- loading and layout ---------------------------------------------------------------

def test_page_loads_with_every_experiment_drawn(page):
    for h in ("pend-h", "tun-h", "slit-h", "orb-h", "lor-h", "ising-h"):
        assert page.is_visible(f"#{h}")
    for cv in ("pend-curve", "tun-psi", "tun-curve", "slit-curve", "orb-curve", "lor-curve", "ising-curve"):
        assert canvas_ink(page, cv) > 0.005, f"{cv} looks blank"


def test_phone_layout_has_no_horizontal_scroll_and_no_errors(browser):
    page = open_page(browser, width=390, height=800, color_scheme="dark")
    try:
        assert page.evaluate("document.documentElement.scrollWidth") <= 390
        assert [e for e in page.all_errors if "Failed to load resource" not in e] == []
    finally:
        page.context.close()


def test_reduced_motion_starts_paused(browser):
    page = open_page(browser, reduced_motion="reduce")
    try:
        for btn in ("pend-play", "orb-play", "lor-play", "ising-play"):
            assert text(page, btn) == "Play"
            assert page.get_attribute(f"#{btn}", "aria-pressed") == "false"
        page.wait_for_timeout(800)
        assert number(page, "lor-t") == 0.0
        page.click("#lor-play")                      # and the button starts it
        wait_until(page, "+document.getElementById('lor-t').textContent > 0.2")
    finally:
        page.context.close()


# ---- pendulum ---------------------------------------------------------------------------

@pytest.mark.parametrize("degrees,length", [(5, 1.0), (10, 1.0), (60, 1.0), (10, 1.5), (90, 1.0), (170, 0.5)])
def test_pendulum_period_matches_python(page, degrees, length):
    set_slider(page, "pend-amp", degrees)
    set_slider(page, "pend-len", length)
    T = mechanics.pendulum_period(math.radians(degrees), 9.81, length)
    T0 = 2 * math.pi * math.sqrt(length / 9.81)
    assert number(page, "pend-T") == pytest.approx(T, abs=6e-4)
    assert number(page, "pend-T0") == pytest.approx(T0, abs=6e-4)
    assert number(page, "pend-ratio") == pytest.approx(T / T0, abs=6e-4)


def test_pendulum_animation_runs_and_pauses(page):
    t_text = lambda: page.evaluate("document.getElementById('pend-play').textContent")
    assert t_text() == "Pause"
    page.click("#pend-play")
    assert t_text() == "Play" and page.get_attribute("#pend-play", "aria-pressed") == "false"


# ---- tunnelling -------------------------------------------------------------------------

@pytest.mark.parametrize("E,V0,a", [(1.2, 2.0, 1.0), (0.3, 4.0, 2.0), (3.0, 2.0, 1.5), (5.0, 1.0, 0.5)])
def test_tunnelling_transmission_matches_exact_formula(page, E, V0, a):
    set_slider(page, "tun-E", E)
    set_slider(page, "tun-V", V0)
    set_slider(page, "tun-a", a)
    T = quantum.barrier_transmission(E, V0, a)
    shown = number(page, "tun-T")
    if T < 1e-3:
        assert shown == pytest.approx(T, rel=0.01)            # shown in scientific notation
    else:
        assert shown == pytest.approx(T, abs=6e-4)
        assert number(page, "tun-R") == pytest.approx(1 - T, abs=6e-4)
    assert number(page, "tun-lam") == pytest.approx(2 * math.pi / math.sqrt(2 * E), abs=6e-3)
    assert ("tunnelling" in text(page, "tun-regime")) == (E < V0)


# ---- double slit ------------------------------------------------------------------------

# (532, 0.40, 0.08) has d/w = 5 exactly: the 5th-order fringe sits on the envelope zero and must not count.
@pytest.mark.parametrize("lam_nm,d_mm,w_mm,L", [(600, 0.30, 0.05, 2.0), (450, 0.80, 0.03, 1.0), (700, 0.12, 0.08, 3.0), (532, 0.40, 0.08, 1.0)])
def test_double_slit_readouts(page, lam_nm, d_mm, w_mm, L):
    set_slider(page, "slit-lam", lam_nm)
    set_slider(page, "slit-d", d_mm)
    set_slider(page, "slit-w", w_mm)
    set_slider(page, "slit-L", L)
    lam, d, w = lam_nm * 1e-9, d_mm * 1e-3, w_mm * 1e-3
    assert number(page, "slit-dy") == pytest.approx(lam * L / d * 1e3, abs=6e-3)
    assert number(page, "slit-env") == pytest.approx(lam * L / w * 1e3, abs=0.06)
    # bright fringes strictly inside the central envelope: |m| lambda/d < lambda/w
    expected = sum(1 for m in range(-1000, 1001) if abs(m) / d < (1 - 1e-12) / w)
    assert number(page, "slit-n") == expected


# ---- Kepler orbits ----------------------------------------------------------------------

@pytest.mark.parametrize("v", [0.8, 1.0, 1.2])
def test_orbit_elements_and_measured_period(page, v):
    set_slider(page, "orb-v", v)
    a = 1 / (2 - v**2)                        # from the energy v^2/2 - 1 = -1/(2a), GM = r0 = 1
    T = 2 * math.pi * a**1.5
    assert number(page, "orb-e") == pytest.approx(abs(v**2 - 1), abs=6e-4)
    assert number(page, "orb-a") == pytest.approx(a, abs=6e-4)
    assert number(page, "orb-T") == pytest.approx(T, abs=6e-3)
    wait_until(page, "!/waiting/.test(document.getElementById('orb-Tm').textContent)", timeout=30_000)
    assert number(page, "orb-Tm") == pytest.approx(T, rel=0.005)     # simulated in the browser


def test_orbit_escape_at_and_above_root_two(page):
    set_slider(page, "orb-v", 1.45)
    assert "escapes" in text(page, "orb-a")
    assert number(page, "orb-e") == pytest.approx(1.45**2 - 1, abs=6e-4)
    page.wait_for_timeout(1500)
    assert "waiting" in text(page, "orb-Tm")                          # it never comes back


# ---- Lorenz -----------------------------------------------------------------------------

def test_lorenz_chaos_threshold_readout(page):
    for rho, sigma, beta in [(28, 10, 2.67), (20, 14, 1.5)]:
        set_slider(page, "lor-rho", rho)
        set_slider(page, "lor-sigma", sigma)
        set_slider(page, "lor-beta", beta)
        rho_h = sigma * (sigma + beta + 3) / (sigma - beta - 1)
        assert number(page, "lor-rhoH") == pytest.approx(rho_h, abs=6e-3)
        assert ("chaotic" in text(page, "lor-regime")) == (rho > rho_h)


def test_lorenz_separation_grows_when_chaotic_and_shrinks_when_stable(page):
    set_slider(page, "lor-rho", 28)
    wait_until(page, "+document.getElementById('lor-t').textContent >= 8", timeout=40_000)
    chaotic = number(page, "lor-sep")
    set_slider(page, "lor-rho", 15)                                   # below rho_H: a stable fixed point
    assert "fixed point" in text(page, "lor-regime")
    wait_until(page, "+document.getElementById('lor-t').textContent >= 8", timeout=40_000)
    stable = number(page, "lor-sep")
    assert chaotic > 1e-6           # grew by > 100x from 1e-8 (Lyapunov exponent ~0.9)
    assert stable < 1e-8            # shrank


# ---- Ising ------------------------------------------------------------------------------

def test_ising_readouts(page):
    set_slider(page, "ising-T", 2.0)
    assert number(page, "ising-ratio") == pytest.approx(2.0 / statmech.T_CRITICAL, abs=6e-4)
    assert number(page, "ising-exact") == pytest.approx(statmech.onsager_magnetization(2.0), abs=6e-4)
    set_slider(page, "ising-T", 3.0)
    assert number(page, "ising-exact") == 0.0


def test_ising_magnetisation_approaches_onsager(page):
    set_slider(page, "ising-T", 1.8)
    page.click("#ising-cold")
    page.wait_for_timeout(4000)
    exact = float(statmech.onsager_magnetization(1.8))
    assert number(page, "ising-m") == pytest.approx(exact, abs=0.03)

    set_slider(page, "ising-T", 3.5)
    page.click("#ising-hot")
    page.wait_for_timeout(4000)
    assert number(page, "ising-m") < 0.1
    lattice = page.evaluate("""() => { const c = document.getElementById('ising-lattice');
        const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
        let up = 0; for (let i = 0; i < d.length; i += 4) if (d[i] === d[0] && d[i+1] === d[1] && d[i+2] === d[2]) up++;
        return up / (c.width * c.height); }""")
    assert 0.3 < lattice < 0.7                                    # a disordered mix of both colours


def test_python_and_page_use_the_same_critical_temperature():
    assert statmech.T_CRITICAL == pytest.approx(2 / np.log(1 + np.sqrt(2)))
