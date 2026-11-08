import numpy as np
import pytest
from scipy import constants

from qplay import quantum, relativity


def test_harmonic_oscillator_levels():
    x = np.linspace(-8, 8, 1601)
    E, _ = quantum.solve_tise(lambda s: 0.5 * s**2, x, n_states=5)
    assert np.allclose(E, np.arange(5) + 0.5, atol=1e-4)


def test_infinite_well_levels_and_normalisation():
    L = 1.0
    x = np.linspace(0, L, 1002)[1:-1]
    E, psi = quantum.solve_tise(np.zeros_like(x), x, n_states=3)
    assert np.allclose(E, quantum.infinite_well_energy([1, 2, 3], L), rtol=1e-4)
    assert np.sum(psi[0] ** 2) * (x[1] - x[0]) == pytest.approx(1.0)


def test_analytic_well_states_are_orthonormal():
    x = np.linspace(0, 1, 5001)
    s1, s2 = quantum.infinite_well_state(1, x), quantum.infinite_well_state(2, x)
    assert np.trapezoid(s1 * s1, x) == pytest.approx(1.0, abs=1e-6)
    assert np.trapezoid(s1 * s2, x) == pytest.approx(0.0, abs=1e-6)


def test_free_packet_spreads_as_predicted():
    x = np.linspace(-40, 40, 2048, endpoint=False)
    dx = x[1] - x[0]
    psi0 = quantum.gaussian_wavepacket(x, sigma=1.0)
    _, psi = quantum.split_step(psi0, x, np.zeros_like(x), dt=0.01, steps=200)
    rho = quantum.probability_density(psi[-1])
    assert np.sum(rho) * dx == pytest.approx(1.0, abs=1e-10)
    width = np.sqrt(np.sum(x**2 * rho) * dx)
    assert width == pytest.approx(np.sqrt(1 + (2 / 2) ** 2), rel=1e-4)  # t = 2


def test_ground_state_is_stationary_under_split_step():
    x = np.linspace(-10, 10, 1024, endpoint=False)
    V = 0.5 * x**2
    _, psi_n = quantum.solve_tise(V, x, n_states=1)
    psi0 = psi_n[0].astype(complex)
    _, psi = quantum.split_step(psi0, x, V, dt=0.005, steps=400)
    assert np.allclose(np.abs(psi[-1]), np.abs(psi0), atol=2e-3)


def test_tunnelling_limits():
    assert quantum.barrier_transmission(0.5, 1.0, 10.0) < 1e-6        # thick barrier
    assert quantum.barrier_transmission(50.0, 1.0, 1.0) > 0.99        # far above the barrier
    below, above = quantum.barrier_transmission([0.999999, 1.000001], 1.0, 1.0)
    assert below == pytest.approx(above, rel=1e-4)                    # continuous at E = V0
    k2 = np.sqrt(2 * (4.0 - 1.0))
    assert quantum.barrier_transmission(4.0, 1.0, np.pi / k2) == pytest.approx(1.0)  # resonance


def test_hydrogen():
    assert quantum.hydrogen_energy_eV(1) == pytest.approx(-13.6057, abs=1e-3)
    assert quantum.hydrogen_wavelength_nm(3, 2) == pytest.approx(656.1, abs=0.5)  # H-alpha


def test_rabi_flip_and_norm():
    omega = 2.0
    psi = quantum.evolve(omega / 2 * quantum.SIGMA_X, [1, 0], np.pi / omega)
    assert np.allclose(quantum.bloch_vector(psi), [0, 0, -1], atol=1e-12)
    assert np.linalg.norm(psi) == pytest.approx(1.0)


def test_velocity_addition_never_exceeds_c():
    c = constants.c
    assert relativity.add_velocities(0.9 * c, 0.9 * c) / c == pytest.approx(1.8 / 1.81)
    assert relativity.add_velocities(c, 0.5 * c) == pytest.approx(c)


def test_time_dilation_and_contraction():
    v = 0.6 * constants.c  # gamma = 1.25
    assert relativity.gamma(v) == pytest.approx(1.25)
    assert relativity.time_dilation(1.0, v) == pytest.approx(1.25)
    assert relativity.length_contraction(1.0, v) == pytest.approx(0.8)


def test_boost_preserves_interval_and_composes():
    event = np.array([3.0, 1.0, 2.0, -1.0])
    boosted = relativity.lorentz_boost(0.8) @ event
    assert relativity.interval(boosted) == pytest.approx(relativity.interval(event))
    b1, b2 = 0.5, 0.7
    combined = relativity.lorentz_boost(b1) @ relativity.lorentz_boost(b2)
    assert np.allclose(combined, relativity.lorentz_boost((b1 + b2) / (1 + b1 * b2)))


def test_doppler_and_kinetic_energy_limits():
    assert relativity.doppler_factor(0.0) == 1.0
    v = 1e3
    assert relativity.kinetic_energy(1.0, v) == pytest.approx(0.5 * v**2, rel=1e-6)
