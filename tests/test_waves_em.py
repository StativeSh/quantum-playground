import numpy as np
import pytest

from qplay import em, waves


def test_standing_wave_returns_after_one_period():
    x = np.linspace(0, 1, 401)
    t, u = waves.wave_1d(np.sin(np.pi * x), x, c=1.0, t_max=2.0)
    assert np.allclose(u[-1], u[0], atol=1e-3)
    # half a period later the sign has flipped
    half = np.argmin(abs(t - 1.0))
    assert np.allclose(u[half], -u[0], atol=1e-3)


def test_heat_equation_matches_analytic_mode():
    x = np.linspace(0, 1, 201)
    alpha, t_max = 0.1, 0.5
    t, u = waves.heat_1d(np.sin(np.pi * x), x, alpha=alpha, t_max=t_max, nt=400)
    exact = np.sin(np.pi * x) * np.exp(-alpha * np.pi**2 * t_max)
    assert np.allclose(u[-1], exact, atol=1e-4)


def test_square_wave_fourier_coefficients():
    period = 2 * np.pi
    a0, a, b = waves.fourier_coefficients(lambda s: np.sign(np.sin(s)), period, 5, points=[np.pi])
    assert b[0] == pytest.approx(4 / np.pi, abs=1e-6)
    assert b[1] == pytest.approx(0.0, abs=1e-6)
    assert b[2] == pytest.approx(4 / (3 * np.pi), abs=1e-6)
    assert a0 == pytest.approx(0.0, abs=1e-6)


def test_fourier_sum_reconstructs_cosine():
    x = np.linspace(0, 2 * np.pi, 50)
    a0, a, b = waves.fourier_coefficients(np.cos, 2 * np.pi, 3)
    assert np.allclose(waves.fourier_sum(a0, a, b, x, 2 * np.pi), np.cos(x), atol=1e-8)


def test_spectrum_finds_the_tone():
    dt = 1e-3
    t = np.arange(0, 1, dt)
    freqs, amp = waves.spectrum(3 * np.sin(2 * np.pi * 50 * t), dt)
    assert freqs[np.argmax(amp)] == pytest.approx(50.0)
    assert amp.max() == pytest.approx(3.0, rel=1e-6)


def test_laplace_centre_is_quarter_of_edge_voltage():
    V = em.solve_laplace(51, 51, top=1.0)
    assert V[25, 25] == pytest.approx(0.25, abs=1e-9)


def test_laplace_reproduces_linear_solution():
    nx = ny = 41
    ramp = np.linspace(0, 1, nx)
    V = em.solve_laplace(nx, ny, top=ramp, bottom=ramp, left=0.0, right=1.0)
    assert np.allclose(V, np.tile(ramp, (ny, 1)), atol=1e-10)


def test_point_charge_field_inverse_square():
    X, Y = np.array([[1.0, 2.0]]), np.array([[0.0, 0.0]])
    Ex, Ey = em.point_charge_field([1.0], [(0, 0)], X, Y)
    assert Ex[0, 0] / Ex[0, 1] == pytest.approx(4.0)
    assert np.allclose(Ey, 0)


def test_cyclotron_radius():
    q, m, B, v = 1.0, 2.0, 0.5, 3.0
    T = 2 * np.pi * m / (q * B)
    _, r, _ = em.charged_particle(q, m, [0, 0, 0], [0, 0, B], [0, 0, 0], [v, 0, 0], T, n=4001)
    assert np.ptp(r[:, 1]) / 2 == pytest.approx(m * v / (q * B), rel=1e-6)
    assert np.allclose(r[-1], 0, atol=1e-6)
