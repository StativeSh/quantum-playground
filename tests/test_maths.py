import numpy as np
import pytest
import sympy as sp

from qplay import chaos, integrators, mechanics, numerics, plotting, symbolic


def test_bisect_and_newton_find_sqrt2():
    assert numerics.bisect(lambda x: x * x - 2, 0, 2) == pytest.approx(np.sqrt(2))
    assert numerics.newton(lambda x: x * x - 2, lambda x: 2 * x, 1.0) == pytest.approx(np.sqrt(2))
    with pytest.raises(ValueError):
        numerics.bisect(lambda x: x * x + 1, -1, 1)


def test_derivative_and_quadrature():
    assert numerics.central_difference(np.sin, 0.7) == pytest.approx(np.cos(0.7), abs=1e-9)
    assert numerics.simpson(np.sin, 0, np.pi) == pytest.approx(2.0, abs=1e-10)


def test_monte_carlo_pi():
    assert numerics.monte_carlo_pi(400_000) == pytest.approx(np.pi, abs=0.02)


def test_logistic_map_fixed_point_and_lyapunov():
    assert chaos.logistic_map(2.5, n=200)[-1] == pytest.approx(0.6)
    assert chaos.lyapunov_logistic(2.5) < 0
    assert chaos.lyapunov_logistic(4.0) == pytest.approx(np.log(2), abs=0.02)


def test_bifurcation_shapes_and_period_two():
    r, x = chaos.bifurcation(np.array([2.5, 3.2]), n_keep=10)
    assert r.shape == x.shape == (20,)
    assert np.allclose(x[r == 2.5], 0.6)
    assert len(np.unique(np.round(x[r == 3.2], 6))) == 2


def test_escape_time():
    counts = chaos.escape_time([0, 1 + 0j, -1, 0.5 + 0.5j], max_iter=50)
    assert counts[0] == counts[2] == 50          # in the set
    assert counts[1] < 5 and counts[3] < 50      # escape


def test_julia_shapes():
    assert chaos.julia(-0.8 + 0.156j, width=40, height=30).shape == (30, 40)


def test_lorenz_sensitive_dependence():
    _, a = chaos.lorenz((1, 1, 1), t_max=40)
    _, b = chaos.lorenz((1, 1, 1 + 1e-9), t_max=40)
    assert np.abs(a[0] - b[0]).max() < 1e-8
    assert np.abs(a[-1] - b[-1]).max() > 1.0


def test_euler_lagrange_pendulum():
    t, m, l, g = sp.symbols("t m l g", positive=True)
    th = sp.Function("theta")(t)
    L = m * l**2 * sp.diff(th, t) ** 2 / 2 + m * g * l * sp.cos(th)
    (acc,) = symbolic.accelerations(L, [th], t)
    x = sp.Symbol("x")
    assert sp.simplify(acc.subs(th, x) + g / l * sp.sin(x)) == 0
    energy = symbolic.energy_function(L, [th], t)
    assert sp.simplify(energy - (m * l**2 * sp.diff(th, t) ** 2 / 2 - m * g * l * sp.cos(th))) == 0


def test_lagrangian_to_simulation_matches_hand_written_double_pendulum():
    t, m1, m2, l1, l2, g = sp.symbols("t m1 m2 l1 l2 g", positive=True)
    a, b = sp.Function("a")(t), sp.Function("b")(t)
    ad, bd = sp.diff(a, t), sp.diff(b, t)
    T = (m1 + m2) * l1**2 * ad**2 / 2 + m2 * l2**2 * bd**2 / 2 + m2 * l1 * l2 * ad * bd * sp.cos(a - b)
    V = -(m1 + m2) * g * l1 * sp.cos(a) - m2 * g * l2 * sp.cos(b)
    rhs = symbolic.to_numeric_rhs(T - V, [a, b], t, {m1: 1, m2: 1, l1: 1, l2: 1, g: 9.81})
    tt, y = integrators.solve(rhs, [1.5, 1.0, 0.0, 0.0], (0, 5), n=200)
    _, ref = mechanics.double_pendulum([1.5, 1.0, 0.0, 0.0], t_max=5, n=200)
    assert np.allclose(y, ref, atol=1e-5)


def test_plotting_save_and_gif(tmp_path):
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    (line,) = ax.plot([0, 1], [0, 1])
    assert plotting.save(fig, "demo", tmp_path).stat().st_size > 0

    fig, ax = plt.subplots(figsize=(2, 2))
    (line,) = ax.plot([0, 1], [0, 1])
    gif = plotting.save_gif(fig, lambda i: line.set_ydata([0, i]), range(3), tmp_path / "a.gif", fps=5)
    assert gif.stat().st_size > 0


# ---- root finding: edge cases -----------------------------------------------------

@pytest.mark.parametrize("a,b,root", [(0, 1, 0.0), (-1, 0, 0.0), (0.5, 3, 0.5), (-2, 0.25, 0.25)])
def test_bisect_returns_an_exact_endpoint_root(a, b, root):
    assert numerics.bisect(lambda x: x - root, a, b) == root


def test_bisect_accepts_reversed_bracket():
    assert numerics.bisect(lambda x: x * x - 2, 2, 0) == pytest.approx(np.sqrt(2))


def test_bisect_is_not_fooled_by_underflow():
    # f(a) * f(m) underflows to -0.0 here, which used to send the search the wrong way.
    assert numerics.bisect(lambda x: 1e-200 * (x - 0.3), 0, 1) == pytest.approx(0.3, abs=1e-11)


def test_bisect_rejects_non_finite_values():
    with pytest.raises(ValueError, match="not finite"):
        numerics.bisect(lambda x: float("nan"), 0, 1)
    with pytest.raises(ValueError, match="not finite"):
        numerics.bisect(lambda x: 1 / (x - 0.5) if x != 0.5 else float("inf"), 0, 1)


def test_bisect_reports_too_few_iterations():
    with pytest.raises(RuntimeError, match="did not reach"):
        numerics.bisect(lambda x: x - 0.3, 0, 1, max_iter=5)


def test_bisect_stops_at_float_resolution_for_tiny_tol():
    root = numerics.bisect(lambda x: x - 1e6 * np.sqrt(2), 0, 2e6, tol=1e-30)
    assert root == pytest.approx(1e6 * np.sqrt(2), rel=1e-15)


def test_newton_flags_zero_derivative_and_divergence():
    with pytest.raises(ZeroDivisionError):
        numerics.newton(lambda x: x * x - 2, lambda x: 2 * x, 0.0)
    with pytest.raises(RuntimeError):
        numerics.newton(lambda x: x * x + 1, lambda x: 2 * x, 0.5, max_iter=50)   # no real root
