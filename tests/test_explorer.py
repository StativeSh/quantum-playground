"""Behavioural tests for the interactive explorer (site_src/explorer/) in a real browser.

They move sliders, read the numbers the page shows, and check them against the Python package
or an analytic result; they also let the animations run and check what they converge to.
Needs Playwright with Chromium (`pip install -e ".[browser]"`, then
`python -m playwright install chromium`). Skipped when that is missing, unless the environment
variable QPLAY_REQUIRE_BROWSER is set (CI sets it, so a broken browser fails the build).
"""
import math
import os
import re
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import numpy as np
import pytest

from qplay import mechanics, quantum, statmech

pytestmark = pytest.mark.slow
REQUIRE = bool(os.environ.get("QPLAY_REQUIRE_BROWSER"))
PAGE = None  # assigned the loopback server URL for the duration of this module

if REQUIRE:
    from playwright.sync_api import sync_playwright
else:
    sync_playwright = pytest.importorskip("playwright.sync_api").sync_playwright


@pytest.fixture(scope="module", autouse=True)
def explorer_server():
    global PAGE
    directory = Path(__file__).resolve().parents[1] / "site_src" / "explorer"
    handler = partial(SimpleHTTPRequestHandler, directory=directory)
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        PAGE = f"http://127.0.0.1:{server.server_port}/"
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield
        finally:
            server.shutdown()
            thread.join()
            PAGE = None


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
    page.route(re.compile(r"^https?://"), lambda route: (
        route.continue_() if route.request.url.startswith(PAGE) else route.abort()))
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

def test_double_slit_saved_measurement(page):
    assert page.is_disabled("#slit-save")
    page.click("#slit-mark")
    page.click("#slit-mark")
    first = number(page, "slit-measured")
    assert first == pytest.approx(2.128, rel=0.02)
    page.click("#slit-save")
    reference = text(page, "slit-reference")

    set_slider(page, "slit-d", 0.50)
    assert text(page, "slit-reference") == reference
    assert page.is_disabled("#slit-save")
    assert text(page, "slit-comparison") == ""
    page.click("#slit-mark")
    page.click("#slit-mark")
    ratio = number(page, "slit-measured") / first
    assert ratio == pytest.approx(0.5, abs=0.01)
    assert number(page, "slit-comparison") == pytest.approx(ratio, abs=0.001)
    assert "prediction 0.500" in text(page, "slit-comparison")
    page.click("#slit-save")
    assert text(page, "slit-reference") != reference
    assert number(page, "slit-comparison") == 1


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
@pytest.mark.usefixtures("visible_orbit")
def test_orbit_elements_and_measured_period(page, v):
    set_slider(page, "orb-v", v)
    a = 1 / (2 - v**2)                        # from the energy v^2/2 - 1 = -1/(2a), GM = r0 = 1
    T = 2 * math.pi * a**1.5
    assert number(page, "orb-e") == pytest.approx(abs(v**2 - 1), abs=6e-4)
    assert number(page, "orb-a") == pytest.approx(a, abs=6e-4)
    assert number(page, "orb-T") == pytest.approx(T, abs=6e-3)
    wait_until(page, "!/waiting/.test(document.getElementById('orb-Tm').textContent)", timeout=30_000)
    assert number(page, "orb-Tm") == pytest.approx(T, rel=0.005)     # simulated in the browser


@pytest.mark.usefixtures("visible_orbit")
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


@pytest.mark.usefixtures("visible_lorenz")
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


@pytest.mark.parametrize("angle", [0, 90, 210])
def test_rotating_coil(page, angle):
    from qplay import em
    set_slider(page, "coil-angle", angle)
    expected = em.coil_emf(100, 0.2, 0.01, 10, math.radians(angle)/10)
    assert number(page, "coil-emf") == pytest.approx(expected, abs=.001)
    assert number(page, "coil-flux") == pytest.approx(.2*math.cos(math.radians(angle)), abs=.001)


@pytest.mark.parametrize("density", [400, 800, 1500])
def test_grating_orders(page, density):
    from qplay import waves
    set_slider(page, "grating-density", density)
    angles = [waves.grating_angle(m, 500e-9, 1e-3/density) for m in range(-10, 11)]
    assert number(page, "grating-count") == sum(a is not None for a in angles)
    assert number(page, "grating-angle") == pytest.approx(math.degrees(angles[11]), abs=.006)


def test_every_experiment_at_phone_width(browser):
    page = open_page(browser, width=375, height=800, reduced_motion="reduce", color_scheme="dark")
    try:
        sections = page.locator(".experiment").all()
        links = page.locator(".experiment-index a")
        anchors = links.evaluate_all("links => links.map(a => a.hash.slice(1))")
        assert sections and set(anchors) == {section.get_attribute("id") for section in sections}
        for section in sections:
            anchor = section.get_attribute("id")
            page.locator(f'.experiment-index a[href="#{anchor}"]').first.click()
            assert page.url.endswith(f"#{anchor}")
            assert section.get_by_role("heading").is_visible()
            assert page.evaluate("document.documentElement.scrollWidth") <= 375
            canvases = section.locator("canvas").all()
            assert canvases
            for canvas in canvases:
                assert canvas_ink(page, canvas.get_attribute("id")) > 0
            for button in section.locator("button[aria-pressed]").all():
                assert button.get_attribute("aria-pressed") == "false"
                assert button.inner_text() == "Play"
        assert page.all_errors == []
    finally:
        page.context.close()


def test_frame_time_with_all_simulations_visible(page):
    # Show all experiments so IntersectionObserver enables every playing simulation.
    height = page.evaluate("document.documentElement.scrollHeight")
    page.set_viewport_size({"width": 1200, "height": height})
    buttons = page.locator(".experiment button[aria-pressed]").all()
    assert buttons and all(b.get_attribute("aria-pressed") == "true" for b in buttons)
    intervals = page.evaluate("""() => new Promise(resolve => {
        const samples = [];
        let previous;
        function frame(now) {
            if (previous !== undefined) samples.push(now - previous);
            previous = now;
            if (samples.length === 40) resolve(samples);
            else requestAnimationFrame(frame);
        }
        requestAnimationFrame(frame);
    })""")
    assert np.percentile(intervals, 90) < 100  # allow occasional slow frames on CI
    assert number(page, "lor-t") > 0


def test_offscreen_simulation_suspends_and_resumes(page):
    clock = page.locator("#lor-t")
    wait_until(page, "document.getElementById('lor-t').textContent === '0.0'")
    clock.scroll_into_view_if_needed()
    wait_until(page, "+document.getElementById('lor-t').textContent > 0.2")
    page.locator("h1").scroll_into_view_if_needed()
    page.wait_for_timeout(150)  # allow the intersection callback to run
    paused = clock.inner_text()
    page.wait_for_timeout(350)
    assert clock.inner_text() == paused
    clock.scroll_into_view_if_needed()
    page.wait_for_function("t => +document.getElementById('lor-t').textContent > t", arg=float(paused))


def test_fit_line_and_seeded_sampling(page):
    result = page.evaluate("""async () => {
        const {fitLine, seededRandom} = await import("./core.js");
        const a = seededRandom(42), b = seededRandom(42), c = seededRandom(43);
        const sample = generator => Array.from({length: 16}, generator);
        return [fitLine([-1, 0, 1], [1, 0, 5]), sample(a), sample(b), sample(c)];
    }""")
    fit, first, repeat, different = result
    # y = 2x + 2 with residuals [1, -2, 1]; one residual degree of freedom.
    assert fit == pytest.approx(dict(gradient=2, intercept=2, gradientSE=math.sqrt(3), interceptSE=math.sqrt(2)))
    assert first == repeat and first != different
    assert all(0 <= value < 1 for value in first)


def test_shared_experiment_widgets(page):
    page.evaluate("""async () => {
        const {slider, readout, measureTable, guided, plot} = await import("./core.js");
        const control = slider({id: "distance", label: "Distance", min: 0, max: 5,
                                step: 0.5, value: 1, unit: "m", format: v => v.toFixed(1)});
        const value = readout({id: "area", label: "Area", format: v => v + " m²"});
        control.input.addEventListener("input", () => value.set(control.input.valueAsNumber ** 2));
        const table = measureTable({columns: ["x", "y"]});
        table.addRow([1, 2]);
        const box = guided({question: "Predict the area", steps: ["Square the distance"]});
        const canvas = document.createElement("canvas");
        canvas.id = "widget-plot";
        document.body.append(control.element, value.element, table.element, box, canvas);
        plot(canvas, {xLabel: "x", yLabel: "y", series: [{points: [[0, 0], [1, 2]]}]});
    }""")
    set_slider(page, "distance", 2.5)
    assert page.locator("output[for=distance]").inner_text() == "2.5 m"
    assert text(page, "area") == "6.25 m²"
    assert page.get_by_role("cell").all_text_contents() == ["1", "2"]
    step = page.get_by_text("Square the distance")
    assert not step.is_visible()
    page.get_by_text("Predict the area").click()
    assert step.is_visible()
    assert canvas_ink(page, "widget-plot") > 0


@pytest.fixture
def visible_orbit(page):
    page.locator("#kepler").scroll_into_view_if_needed()


@pytest.fixture
def visible_lorenz(page):
    page.locator("#lorenz").scroll_into_view_if_needed()


def test_offscreen_input_updates_without_scrolling(page):
    before = page.evaluate("window.scrollY")
    set_slider(page, "lor-rho", 15)
    assert "fixed point" in text(page, "lor-regime")
    assert page.evaluate("window.scrollY") == before
    page.wait_for_timeout(200)
    assert number(page, "lor-t") == 0


# ---- projectile launcher ---------------------------------------------------------------

@pytest.mark.parametrize("speed,angle,height", [(15, 30, 0), (30, 45, 0), (20, 65, 4)])
def test_projectile_vacuum(page, speed, angle, height):
    set_slider(page, "projectile-speed", speed)
    set_slider(page, "projectile-angle", angle)
    set_slider(page, "projectile-height", height)
    times, state = mechanics.projectile_trajectory(speed, angle, h0=height)
    assert number(page, "projectile-range") == pytest.approx(state[-1, 0], abs=0.006)
    assert number(page, "projectile-flight") == pytest.approx(times[-1], abs=0.006)


@pytest.mark.parametrize("speed,angle,height", [(10, 15, 5), (30, 45, 0), (40, 80, 10)])
def test_projectile_with_drag(page, speed, angle, height):
    page.check("#projectile-drag")
    set_slider(page, "projectile-speed", speed)
    set_slider(page, "projectile-angle", angle)
    set_slider(page, "projectile-height", height)
    times, state = mechanics.projectile_trajectory(speed, angle, drag=0.02, h0=height, n=1001)
    assert number(page, "projectile-range") == pytest.approx(state[-1, 0], abs=0.006)
    assert number(page, "projectile-flight") == pytest.approx(times[-1], abs=0.006)
    assert number(page, "projectile-peak") == pytest.approx(state[:, 1].max(), abs=0.006)


@pytest.mark.parametrize("frequency,work", [(500, 2.28), (900, 2.28), (1500, 5.6)])
def test_photoelectric_threshold_and_energy(page, frequency, work):
    from scipy.constants import elementary_charge, h
    page.select_option("#photoelectric-metal", str(work))
    set_slider(page, "photoelectric-frequency", frequency)
    energy_ev = max(0, h * frequency * 1e12 / elementary_charge - work)
    assert number(page, "photoelectric-threshold") == pytest.approx(work * elementary_charge / h / 1e12, abs=0.006)
    assert number(page, "photoelectric-energy") == pytest.approx(energy_ev, abs=0.0006)
    assert number(page, "photoelectric-cutoff") == pytest.approx(energy_ev, abs=0.0006)


@pytest.mark.parametrize("frequency,intensity,voltage", [(400, 5, 0), (800, 2, 0), (800, 4, 0.5), (800, 4, 2)])
def test_photoelectric_collector_current(page, frequency, intensity, voltage):
    from scipy.constants import elementary_charge, h
    set_slider(page, "photoelectric-frequency", frequency)
    set_slider(page, "photoelectric-intensity", intensity)
    set_slider(page, "photoelectric-voltage", voltage)
    photon = h * frequency * 1e12
    available = photon - 2.1 * elementary_charge  # caesium
    fraction = max(0, 1 - elementary_charge * voltage / available) if available > 0 else 0
    expected = intensity * 1e-4 / photon * elementary_charge * fraction
    assert number(page, "photoelectric-current") == pytest.approx(expected * 1e6, abs=0.0006)


def prepare_decay(page, initial, probability):
    button = page.locator("#decay-play")
    if button.get_attribute("aria-pressed") == "true":
        button.click()
    set_slider(page, "decay-initial", initial)
    set_slider(page, "decay-probability", probability)


@pytest.mark.parametrize("initial,probability,steps", [(200, 0.1, 5), (600, 0.25, 3), (1000, 0.5, 2)])
def test_decay_sample_and_expected_count(page, initial, probability, steps):
    from qplay import nuclear
    prepare_decay(page, initial, probability)
    for _ in range(steps):
        page.click("#decay-step")
    expected = nuclear.remaining(initial, -math.log1p(-probability), steps)
    sigma = math.sqrt(expected * (1 - expected / initial))  # binomial survivors
    assert number(page, "decay-expected") == pytest.approx(expected, abs=0.006)
    assert number(page, "decay-count") == pytest.approx(expected, abs=4*sigma)
    assert number(page, "decay-time") == steps


@pytest.mark.parametrize("initial,probability", [(500, 0.15), (800, 0.3), (1000, 0.5)])
def test_decay_measured_half_life(page, initial, probability):
    from qplay import nuclear
    prepare_decay(page, initial, probability)
    decay_const = -math.log1p(-probability)
    half = nuclear.half_life(decay_const)
    for _ in range(math.ceil(half) + 3):
        page.click("#decay-step")
    assert number(page, "decay-half") == pytest.approx(half, abs=0.0006)
    # Propagate the binomial count uncertainty at N0/2 through dN/dt = -lambda*N.
    assert number(page, "decay-observed") == pytest.approx(half, abs=4 / (decay_const * math.sqrt(initial)) + 0.1)


@pytest.mark.parametrize("r_kohm,c_uf,supply,t", [(2, 50, 4, 0), (5, 100, 6, 0.5), (10, 200, 12, 3)])
def test_rc_charge(page, r_kohm, c_uf, supply, t):
    from qplay import circuits
    set_slider(page, "rc-resistance", r_kohm)
    set_slider(page, "rc-capacitance", c_uf)
    set_slider(page, "rc-supply", supply)
    set_slider(page, "rc-time", t)
    r, c = r_kohm * 1000, c_uf * 1e-6
    voltage = circuits.rc_charge(t, supply, r, c)
    assert number(page, "rc-voltage") == pytest.approx(voltage, abs=0.0006)
    assert number(page, "rc-current") == pytest.approx((supply-voltage)/r_kohm, abs=0.0006)
    assert number(page, "rc-tau") == pytest.approx(r*c, abs=0.0006)


@pytest.mark.parametrize("r_kohm,c_uf,supply,t", [(1, 20, 3, 0), (4, 50, 8, 0.2), (20, 200, 12, 5)])
def test_rc_discharge(page, r_kohm, c_uf, supply, t):
    from qplay import circuits
    page.select_option("#rc-mode", "discharge")
    set_slider(page, "rc-resistance", r_kohm)
    set_slider(page, "rc-capacitance", c_uf)
    set_slider(page, "rc-supply", supply)
    set_slider(page, "rc-time", t)
    voltage = circuits.rc_discharge(t, supply, r_kohm*1000, c_uf*1e-6)
    assert number(page, "rc-voltage") == pytest.approx(voltage, abs=0.0006)
    assert number(page, "rc-current") == pytest.approx(-voltage/r_kohm, abs=0.0006)
    assert number(page, "rc-energy") == pytest.approx(0.5*c_uf*1e-3*supply**2, abs=0.0006)


def configure_carts(page, m1, m2, u1, u2, restitution):
    for key, value in [("mass1", m1), ("mass2", m2), ("u1", u1), ("u2", u2), ("restitution", restitution)]:
        set_slider(page, f"collisions-{key}", value)
    return mechanics.collision(m1, m2, u1, u2, normal=(1,), restitution=restitution)


@pytest.mark.parametrize("m1,m2,u1,u2,e", [(1, 1, 2, 0, 1), (2, 3, 1, -2, 0), (1, 3, -2, 2, 0.5)])
def test_cart_velocities(page, m1, m2, u1, u2, e):
    v1, v2 = configure_carts(page, m1, m2, u1, u2, e)
    assert number(page, "collisions-v1") == pytest.approx(v1.item(), abs=0.0006)
    assert number(page, "collisions-v2") == pytest.approx(v2.item(), abs=0.0006)


@pytest.mark.parametrize("m1,m2,u1,u2,e", [(1, 2, 3, -1, 1), (2, 0.5, 1, -2, 0.4), (3, 2, 2, 0, 0)])
def test_cart_momentum_and_energy(page, m1, m2, u1, u2, e):
    v1, v2 = configure_carts(page, m1, m2, u1, u2, e)
    momentum = m1*u1 + m2*u2
    for key in ("p-before", "p-after"):
        assert number(page, f"collisions-{key}") == pytest.approx(momentum, abs=0.0006)
    assert number(page, "collisions-k-before") == pytest.approx((m1*u1**2 + m2*u2**2)/2, abs=0.0006)
    final = (m1*v1.item()**2 + m2*v2.item()**2)/2
    assert number(page, "collisions-k-after") == pytest.approx(final, abs=0.0006)


@pytest.mark.parametrize("probe,start,mass,power", [(1, 240, 1, 100), (50, 263, 0.5, 500), (99, 270, 2, 1000)])
def test_heating_temperature_across_phases(page, probe, start, mass, power):
    from qplay import thermal
    set_slider(page, "heating-probe", probe)
    set_slider(page, "heating-start", start)
    set_slider(page, "heating-mass", mass)
    set_slider(page, "heating-power", power)
    total_heat = mass * (2100*(273.15-start) + 334000 + 4200*20)
    supplied = total_heat * probe / 100
    assert number(page, "heating-time") == pytest.approx(supplied/power, abs=0.0006)
    assert number(page, "heating-heat") == pytest.approx(supplied/1000, abs=0.0006)
    assert number(page, "heating-temperature") == pytest.approx(
        thermal.heating_curve(supplied, mass, start, 273.15, 2100, 334000, 4200), abs=0.006)


@pytest.mark.parametrize("material,mass,power,melting,latent", [
    ("water", 0.5, 250, 273.15, 334000), ("water", 1, 500, 273.15, 334000),
    ("gallium", 0.8, 400, 302.91, 80100)])
def test_heating_melting_plateau(page, material, mass, power, melting, latent):
    page.select_option("#heating-material", material)
    set_slider(page, "heating-mass", mass)
    set_slider(page, "heating-power", power)
    assert number(page, "heating-duration") == pytest.approx(mass*latent/power, abs=0.006)
    for probe in (35, 65):
        set_slider(page, "heating-probe", probe)
        assert number(page, "heating-temperature") == pytest.approx(melting, abs=0.006)


@pytest.mark.parametrize("tension,length,density", [(4, 1, 10), (16, 0.8, 5), (64, 2, 20)])
def test_string_fundamental(page, tension, length, density):
    set_slider(page, "strings-tension", tension)
    set_slider(page, "strings-length", length)
    set_slider(page, "strings-density", density)
    expected = math.sqrt(tension/(density*1e-3))/(2*length)
    assert number(page, "strings-fundamental") == pytest.approx(expected, abs=0.0006)


@pytest.mark.parametrize("frequency,n", [(20, 1), (60, 3), (100, 5), (73, None)])
def test_string_modes_and_nodes(page, frequency, n):
    set_slider(page, "strings-tension", 16)
    set_slider(page, "strings-density", 10)
    set_slider(page, "strings-length", 1)
    set_slider(page, "strings-drive", frequency)
    if n is None:
        assert text(page, "strings-mode") == "Between modes"
    else:
        assert number(page, "strings-mode") == n
        assert number(page, "strings-nodes") == n+1


@pytest.mark.parametrize("q,x,y,px,py", [(2, -0.5, 0, 0, 0), (-3, 0.2, 0.5, -0.5, 0.1),
                                        (4, -0.2, -0.7, 0.5, 0.6)])
def test_electric_field_vector(page, q, x, y, px, py):
    from scipy.constants import epsilon_0
    from qplay import em
    for key, val in [("count", 1), ("q0", q), ("x0", x), ("y0", y), ("px", px), ("py", py)]:
        set_slider(page, "efield-"+key, val)
    field = em.point_charge_field([q*1e-9], [(x, y)], px, py, k=1/(4*math.pi*epsilon_0))
    for key, value in zip(("ex", "ey"), field):
        assert number(page, "efield-"+key) == pytest.approx(value, abs=0.0006)


@pytest.mark.parametrize("n,x,y", [(2, 0, 0), (3, 0.3, -0.2), (4, 0.2, 0.4)])
def test_electric_potential_superposition(page, n, x, y):
    from scipy.constants import epsilon_0
    from qplay import em
    set_slider(page, "efield-count", n)
    set_slider(page, "efield-px", x)
    set_slider(page, "efield-py", y)
    positions = [(-0.5, 0), (0.5, 0), (0, 0.5), (0, -0.5)]
    v = em.point_charge_potential([1e-9, -1e-9, 1e-9, -1e-9][:n], positions[:n], x, y,
                                  k=1/(4*math.pi*epsilon_0))
    assert number(page, "efield-v") == pytest.approx(v, abs=0.0006)


@pytest.mark.parametrize("device", ["mouse", "touch"])
def test_drag_charge(page, device):
    canvas = page.locator("#efield-plot")
    canvas.scroll_into_view_if_needed()
    box = canvas.bounding_box()
    y = box["y"] + box["height"]/2
    x, end = (box["x"] + box["width"]*f for f in (0.25, 0.35))
    if device == "mouse":
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(end, y)
        page.mouse.up()
    else:
        session = page.context.new_cdp_session(page)
        for action, points in [("touchStart", [{"x": x, "y": y}]), ("touchMove", [{"x": end, "y": y}]),
                               ("touchEnd", [])]:
            session.send("Input.dispatchTouchEvent", {"type": action, "touchPoints": points})
        session.detach()
    assert float(page.locator("#efield-x0").input_value()) == pytest.approx(-0.3)


@pytest.mark.parametrize("electric,magnetic,speed", [(10, 0.5, 20), (6, 0.2, 30), (5, 0.5, 8)])
def test_crossed_field_selector(page, electric, magnetic, speed):
    set_slider(page, "spectrometer-electric", electric)
    set_slider(page, "spectrometer-magnetic", magnetic)
    set_slider(page, "spectrometer-speed", speed)
    assert number(page, "spectrometer-selected") == pytest.approx(electric/magnetic)
    assert ("Blocked" in text(page, "spectrometer-landing")) == (not math.isclose(speed, electric/magnetic))


@pytest.mark.parametrize("mass,charge,b", [(12, 1, 0.5), (20, 2, 0.2), (24, 1, 1)])
def test_spectrometer_trajectory(page, mass, charge, b):
    from scipy.constants import atomic_mass, elementary_charge
    from qplay import em
    v = 10000/b
    for key, value in [("mass", mass), ("charge", charge), ("magnetic", b), ("speed", v/1000)]:
        set_slider(page, "spectrometer-"+key, value)
    m, q = mass*atomic_mass, charge*elementary_charge
    _, path = em.particle_trajectory(q, m, [0, 0, 0], [0, 0, b], [0, 0, 0], [v, 0, 0], math.pi*m/(q*b))
    assert number(page, "spectrometer-radius") == pytest.approx(1000*m*v/(q*b), abs=0.0006)
    assert number(page, "spectrometer-landing") == pytest.approx(1000*path[-1, 1], abs=0.0006)


@pytest.mark.parametrize("beta", [0, 0.6, 0.866, 0.99])
def test_light_clock_ticks(page, beta):
    from qplay import relativity
    set_slider(page, "lightclock-beta", beta)
    assert number(page, "lightclock-gamma") == pytest.approx(relativity.gamma(beta, c=1), abs=0.00006)
    assert number(page, "lightclock-time") == pytest.approx(relativity.time_dilation(1, beta, c=1), abs=0.00006)


@pytest.mark.parametrize("beta", [0.7, 0.95, 0.999])
def test_muon_survival(page, beta):
    from scipy.constants import c
    from qplay import relativity
    set_slider(page, "lightclock-beta", beta)
    lifetime = relativity.time_dilation(2.197e-6, beta*c)
    assert number(page, "lightclock-fraction") == pytest.approx(math.exp(-10000/(beta*c*lifetime)), abs=6e-7)


@pytest.mark.parametrize("a,z", [(16, 8), (55, 25), (56, 27), (208, 82)])
def test_binding_curve(page, a, z):
    from qplay import nuclear
    set_slider(page, "binding-a", a)
    set_slider(page, "binding-z", z)
    chain = nuclear.binding_energy_per_nucleon(a, np.arange(1, a))
    assert number(page, "binding-energy") == pytest.approx(chain[z-1], abs=0.00006)


@pytest.mark.parametrize("a,z,reaction", [(16, 8, "fusion"), (56, 26, "fission"), (209, 83, "fission")])
def test_binding_reaction_balance(page, a, z, reaction):
    from qplay import nuclear
    set_slider(page, "binding-a", a)
    set_slider(page, "binding-z", z)
    page.select_option("#binding-reaction", reaction)
    def total(mass, protons):
        return mass*nuclear.binding_energy_per_nucleon(mass, protons)
    if reaction == "fusion":
        expected = total(2*a, 2*z)-2*total(a, z)
    else:
        expected = total(a//2, z//2)+total(a-a//2, z-z//2)-total(a, z)
    assert number(page, "binding-release") == pytest.approx(expected, abs=0.0006)


@pytest.mark.parametrize("mass,radius", [(1, 2), (5.9, 6.4), (10, 10)])
def test_planet_surface_speeds(page, mass, radius):
    from qplay import gravity
    set_slider(page, "launch-mass", mass)
    set_slider(page, "launch-radius", radius)
    escape = gravity.escape_speed(mass*1e24, radius*1e6)/1000
    assert number(page, "launch-escape") == pytest.approx(escape, abs=0.00006)
    assert number(page, "launch-circular") == pytest.approx(escape/math.sqrt(2), abs=0.00006)


@pytest.mark.parametrize("speed,angle,fate", [(0.9, 0, "Falls back"), (1, 0, "Orbits"),
                                             (1.2, 45, "Falls back"), (1.42, 90, "Escapes")])
def test_planet_launch_outcome(page, speed, angle, fate):
    from qplay import gravity
    set_slider(page, "launch-speed", speed)
    set_slider(page, "launch-angle", angle)
    vc = gravity.escape_speed(5.9e24, 6.4e6)/math.sqrt(2)
    assert number(page, "launch-velocity") == pytest.approx(speed*vc/1000, abs=0.00006)
    assert text(page, "launch-fate") == fate


def configure_gas(page, n, kelvin, width):
    if page.locator("#gas-play").get_attribute("aria-pressed") == "true":
        page.click("#gas-play")
    for key, value in [("n", n), ("temperature", kelvin), ("width", width)]:
        set_slider(page, "gas-"+key, value)


@pytest.mark.parametrize("n,kelvin,width", [(100, 200, 30), (200, 300, 60), (300, 500, 90)])
def test_gas_wall_impulses(page, n, kelvin, width):
    from scipy.constants import Boltzmann
    configure_gas(page, n, kelvin, width)
    page.click("#gas-sample")
    pressure_kpa = n*Boltzmann*kelvin/(width*60**2*1e-27)/1000
    assert number(page, "gas-ideal") == pytest.approx(pressure_kpa, abs=0.0006)
    # Finite Maxwell sample and finite wall-hit count over 100 ps.
    assert number(page, "gas-pressure") == pytest.approx(pressure_kpa, rel=0.18)
    assert number(page, "gas-time") == pytest.approx(100)


@pytest.mark.parametrize("n,kelvin", [(100, 100), (200, 300), (300, 600)])
def test_gas_maxwell_rms(page, n, kelvin):
    from scipy.constants import atomic_mass, Boltzmann
    from qplay import kinetic
    configure_gas(page, n, kelvin, 60)
    expected = kinetic.rms_speed(Boltzmann*kelvin, 4.002602*atomic_mass)
    most_probable = math.sqrt(2*Boltzmann*kelvin/(4.002602*atomic_mass))
    peak = kinetic.maxwell_boltzmann_speed(most_probable, Boltzmann*kelvin, 4.002602*atomic_mass)
    assert number(page, "gas-density") == pytest.approx(peak, abs=6e-8)
    # Three standard deviations of the rms of 3N Gaussian components.
    tolerance = 3 / math.sqrt(6*n)
    for _ in range(2):
        assert number(page, "gas-rms") == pytest.approx(expected, rel=tolerance)
        page.click("#gas-sample")


def open_mode(page, mode):
    page.locator(f"#{mode} > summary").click()
    page.locator(f"#{mode}-plot").wait_for()


@pytest.mark.parametrize("omega,gamma,drive,t", [(1, 0.1, 0, 1), (2, 0.2, 2, 3), (3, 0.5, 4, 6)])
def test_driven_spring_state(page, omega, gamma, drive, t):
    open_mode(page, "spring")
    for key, value in [("omega", omega), ("gamma", gamma), ("drive", drive), ("time", t)]:
        set_slider(page, "spring-"+key, value)
    _, state = mechanics.oscillator_trajectory(omega=omega, gamma=gamma, drive=1, drive_omega=drive, t_max=t)
    x, v = state[-1]
    assert number(page, "spring-x") == pytest.approx(x, abs=0.00006)
    assert number(page, "spring-v") == pytest.approx(v, abs=0.00006)


@pytest.mark.parametrize("force,gamma,t", [(0, 0.2, 2), (1, 0.1, 0.5), (2, 0.5, 5)])
def test_driven_spring_energy(page, force, gamma, t):
    open_mode(page, "spring")
    for key, value in [("force", force), ("gamma", gamma), ("time", t)]:
        set_slider(page, "spring-"+key, value)
    _, state = mechanics.oscillator_trajectory(omega=2, gamma=gamma, drive=force, drive_omega=2, t_max=t)
    x, v = state[-1]
    assert number(page, "spring-q") == pytest.approx(1/gamma, abs=0.0006)
    assert number(page, "spring-ke") == pytest.approx(v*v/2, abs=0.00006)
    assert number(page, "spring-pe") == pytest.approx(2*x*x, abs=0.00006)


@pytest.mark.parametrize("m,b,length,r,t", [(0.2, 0.5, 0.5, 1, 1), (0.5, 1, 1, 2, 3), (1, 0.2, 0.4, 3, 0)])
def test_braked_rod_velocity(page, m, b, length, r, t):
    open_mode(page, "rod")
    for key, v in [("mass", m), ("field", b), ("length", length), ("resistance", r), ("time", t)]:
        set_slider(page, "rod-"+key, v)
    tau = m*r/(b*length)**2
    assert number(page, "rod-tau") == pytest.approx(tau, abs=0.00006)
    assert number(page, "rod-speed") == pytest.approx(4*math.exp(-t/tau), abs=0.00006)


@pytest.mark.parametrize("initial,t", [(2, 0.5), (4, 2), (8, 10)])
def test_braked_rod_joule_heat(page, initial, t):
    open_mode(page, "rod")
    set_slider(page, "rod-initial", initial)
    set_slider(page, "rod-time", t)
    tau = 0.2/(0.5*0.5)**2
    expected = 0.1*initial**2*(1-math.exp(-2*t/tau))
    for key in ("rod-heat", "rod-lost"):
        assert number(page, key) == pytest.approx(expected, abs=0.00006)


@pytest.mark.parametrize("density", [300, 600, 1100])
def test_white_grating_orders(page, density):
    from qplay import waves
    open_mode(page, "white")
    set_slider(page, "white-density", density)
    for color, nm in [("blue", 450), ("red", 650)]:
        angle = waves.grating_angle(1, nm*1e-9, 1e-3/density)
        assert number(page, "white-"+color) == pytest.approx(math.degrees(angle), abs=0.0006)


@pytest.mark.parametrize("slits,density", [(2, 400), (10, 600), (30, 800)])
def test_grating_peak_width(page, slits, density):
    open_mode(page, "white")
    set_slider(page, "white-slits", slits)
    set_slider(page, "white-density", density)
    width = 2*math.degrees(math.asin(550e-9/(slits*1e-3/density)))
    assert number(page, "white-width") == pytest.approx(width, abs=0.0006)


@pytest.mark.parametrize("speed", [0.7, 0.9, 1.1])
def test_kepler_measurement_axes(page, speed):
    open_mode(page, "kepler-law")
    set_slider(page, "orb-v", speed)
    a = 1/(2-speed**2)
    wait_until(page, "!/Awaiting/.test(document.getElementById('kepler-law-t2').textContent)")
    assert number(page, "kepler-law-a3") == pytest.approx(a**3, abs=0.000006)
    assert number(page, "kepler-law-t2") == pytest.approx(4*math.pi**2*a**3, rel=0.001)


@pytest.mark.parametrize("pair", [(0.6, 0.8), (0.8, 1)])
def test_kepler_repeated_measurements(page, pair):
    open_mode(page, "kepler-law")
    for speed in pair:
        set_slider(page, "orb-v", speed)
        wait_until(page, "!/Awaiting/.test(document.getElementById('kepler-law-t2').textContent)")
        assert number(page, "kepler-law-ratio") == pytest.approx(4*math.pi**2, rel=0.001)
    assert page.locator("#kepler-law tbody tr").count() >= 2


@pytest.mark.parametrize("lam,d,length", [(450, 0.2, 1), (532, 0.4, 2), (650, 0.6, 3)])
def test_photon_fringe_minimum(page, lam, d, length):
    open_mode(page, "photons")
    set_slider(page, "slit-lam", lam)
    set_slider(page, "slit-d", d)
    set_slider(page, "slit-L", length)
    theta = math.asin(lam*1e-9/(2*d*1e-3))
    assert number(page, "photons-width") == pytest.approx(1000*length*math.tan(theta), abs=0.00006)


@pytest.mark.parametrize("d,width", [(0.2, 0.04), (0.4, 0.08), (0.6, 0.03)])
def test_photon_central_counts(page, d, width):
    from scipy.integrate import quad
    open_mode(page, "photons")
    set_slider(page, "slit-d", d)
    set_slider(page, "slit-w", width)
    set_slider(page, "photons-batch", 2000)
    page.get_by_role("button", name="Add photons").click()
    lam = 532e-9
    span = min(0.08, 2.2*lam/(width*1e-3))
    cutoff = math.tan(math.asin(lam/(2*d*1e-3)))
    def intensity(y):
        sin = y/math.hypot(1, y)
        return np.sinc(width*1e-3*sin/lam)**2 * math.cos(math.pi*d*1e-3*sin/lam)**2
    prob = quad(intensity, 0, cutoff)[0]/quad(intensity, 0, span, limit=200)[0]
    assert number(page, "photons-count") == 2000
    assert number(page, "photons-central") == pytest.approx(prob, abs=4*math.sqrt(prob*(1-prob)/2000))


def test_optional_modes_on_phone(browser):
    page = open_page(browser, width=375, height=800, reduced_motion="reduce")
    try:
        for panel in page.locator(".extension").all():
            mode = panel.get_attribute("id")
            open_mode(page, mode)
            assert canvas_ink(page, mode+"-plot") > 0
            assert page.evaluate("document.documentElement.scrollWidth") == 375
        assert page.all_errors == []
    finally:
        page.context.close()
