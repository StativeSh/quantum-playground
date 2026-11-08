import numpy as np
import pytest

from qplay import integrators, mechanics


def test_pendulum_conserves_energy():
    g, L = 9.81, 1.0
    _, th, w = mechanics.pendulum(theta0=2.0, g=g, length=L, t_max=20)
    assert np.ptp(0.5 * w**2 - (g / L) * np.cos(th)) < 1e-8


def test_pendulum_small_angle_period():
    assert mechanics.pendulum_period(1e-3) == pytest.approx(2 * np.pi * np.sqrt(1 / 9.81), rel=1e-6)


def test_pendulum_returns_after_exact_period():
    T = mechanics.pendulum_period(2.0)
    _, th, w = mechanics.pendulum(theta0=2.0, t_max=T, n=10)
    assert th[-1] == pytest.approx(2.0, abs=1e-6)
    assert w[-1] == pytest.approx(0.0, abs=1e-6)


def test_harmonic_oscillator_analytic():
    t, x, _ = mechanics.harmonic_oscillator(x0=1, omega=2, t_max=5)
    assert np.allclose(x, np.cos(2 * t), atol=1e-8)


def test_damped_oscillator_decays_as_exp():
    gamma, omega = 0.3, 3.0
    t, x, _ = mechanics.harmonic_oscillator(x0=1, v0=-gamma, omega=omega, gamma=gamma, t_max=6)
    wd = np.sqrt(omega**2 - gamma**2)
    assert np.allclose(x, np.exp(-gamma * t) * np.cos(wd * t), atol=1e-8)


def test_projectile_range_in_vacuum():
    v, angle, g = 20.0, 40.0, 9.81
    _, x, y = mechanics.projectile(v, angle, g=g)
    assert x[-1] == pytest.approx(v**2 * np.sin(np.radians(2 * angle)) / g, rel=1e-6)
    assert y[-1] == pytest.approx(0.0, abs=1e-6)


def test_drag_shortens_range():
    _, x0, _ = mechanics.projectile(30, 45)
    _, x1, _ = mechanics.projectile(30, 45, drag=0.02)
    assert x1[-1] < x0[-1]


def test_double_pendulum_conserves_energy():
    _, y = mechanics.double_pendulum([1.5, 1.0, 0.0, 0.0], t_max=10)
    e = mechanics.double_pendulum_energy(y)
    assert np.ptp(e) < 1e-6


def test_circular_orbit_closes():
    t, pos, _ = mechanics.nbody([1.0, 1e-9], [[0, 0], [1, 0]], [[0, 0], [0, 1]], 2 * np.pi, n=50)
    assert np.allclose(pos[-1, 1], [1, 0], atol=1e-5)


def test_figure_eight_is_periodic_and_conserves_energy():
    fe = mechanics.FIGURE_EIGHT
    _, pos, vel = mechanics.nbody(fe["masses"], fe["pos0"], fe["vel0"], fe["period"], n=200)
    assert np.allclose(pos[-1], pos[0], atol=1e-3)
    assert np.ptp(mechanics.nbody_energy(fe["masses"], pos, vel)) < 1e-6


def test_integrator_orders():
    f = lambda t, y: -y  # noqa: E731
    t = np.linspace(0, 1, 101)
    exact = np.exp(-1.0)
    err_euler = abs(integrators.euler(f, [1.0], t)[-1, 0] - exact)
    err_rk4 = abs(integrators.rk4(f, [1.0], t)[-1, 0] - exact)
    assert err_rk4 < 1e-9 < 1e-3 < err_euler


def test_verlet_energy_bounded_over_long_run():
    t = np.linspace(0, 200, 20001)
    x, v = integrators.velocity_verlet(lambda x: -x, [1.0], [0.0], t)
    energy = 0.5 * v[:, 0] ** 2 + 0.5 * x[:, 0] ** 2
    assert np.ptp(energy) < 1e-3
