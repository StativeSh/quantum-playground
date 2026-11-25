"""Kinetic theory, coherent states, atomic structure, radioactive decay and circuits."""
import numpy as np
import pytest
from scipy import constants, stats
from scipy.integrate import quad

from qplay import atomic, circuits, kinetic, nuclear, quantum

# ---- kinetic theory -----------------------------------------------------------


@pytest.fixture(scope="module")
def gas3d():
    return kinetic.gas_box(n=400, dim=3, radius=0.02, t_max=6, save_every=20, seed=1)


@pytest.mark.parametrize("dim", [2, 3])
def test_maxwell_boltzmann_normalised_with_textbook_moments(dim):
    kT, m = 1.7, 0.6
    norm = quad(lambda v: kinetic.maxwell_boltzmann_speed(v, kT, m, dim), 0, np.inf)[0]
    mean = quad(lambda v: v * kinetic.maxwell_boltzmann_speed(v, kT, m, dim), 0, np.inf)[0]
    msq = quad(lambda v: v**2 * kinetic.maxwell_boltzmann_speed(v, kT, m, dim), 0, np.inf)[0]
    assert norm == pytest.approx(1.0, abs=1e-10)
    textbook_mean = np.sqrt(8 * kT / (np.pi * m)) if dim == 3 else np.sqrt(np.pi * kT / (2 * m))
    assert mean == pytest.approx(textbook_mean, rel=1e-10)
    assert kinetic.mean_speed(kT, m, dim) == pytest.approx(textbook_mean, rel=1e-12)
    assert np.sqrt(msq) == pytest.approx(kinetic.rms_speed(kT, m, dim), rel=1e-10)


def test_gas_conserves_energy_exactly(gas3d):
    energy = 0.5 * gas3d.m * (gas3d.velocities**2).sum(axis=(1, 2))
    assert np.ptp(energy) < 1e-10 * energy[0]
    assert gas3d.collisions[-1] > 5 * gas3d.n_particles     # plenty of collisions happened


def test_gas_relaxes_from_one_speed_to_maxwell_boltzmann(gas3d):
    v = np.linalg.norm(gas3d.velocities, axis=-1)
    ratio = (v**4).mean(1) / (v**2).mean(1) ** 2            # 1 for a single speed, (d+2)/d for MB
    assert ratio[0] == pytest.approx(1.0)
    assert ratio[len(ratio) // 2:].mean() == pytest.approx(5 / 3, rel=0.03)
    speeds = gas3d.speeds(len(gas3d.t) // 2)
    kT = gas3d.temperature()
    assert speeds.mean() == pytest.approx(np.sqrt(8 * kT / (np.pi * gas3d.m)), rel=0.01)
    # Largest gap between the measured and Maxwell-Boltzmann cumulative distributions (KS statistic).
    ks = stats.kstest(speeds / np.sqrt(kT / gas3d.m), stats.chi(3).cdf).statistic
    assert ks < 0.03
    initial = stats.kstest(np.linalg.norm(gas3d.velocities[0], axis=-1) / np.sqrt(kT), stats.chi(3).cdf).statistic
    assert initial > 0.4


def test_gas_pressure_obeys_ideal_gas_law_with_hard_sphere_correction(gas3d):
    eta = gas3d.packing_fraction
    Z = gas3d.pressure() * gas3d.volume / (gas3d.n_particles * gas3d.temperature())
    assert Z == pytest.approx(1 + 4 * eta + 10 * eta**2, rel=0.015)   # Carnahan-Starling virial series


def test_gas_in_2d_matches_disc_virial_series():
    gas = kinetic.gas_box(n=300, dim=2, radius=0.01, t_max=6, save_every=20, seed=0)
    eta = gas.packing_fraction
    Z = gas.pressure() * gas.volume / (gas.n_particles * gas.temperature())
    assert Z == pytest.approx(1 + 2 * eta + 3.128 * eta**2, rel=0.02)
    v = gas.speeds(len(gas.t) // 2)
    assert (v**4).mean() / (v**2).mean() ** 2 == pytest.approx(2.0, rel=0.04)


def test_gas_refuses_impossible_packing():
    with pytest.raises(ValueError):
        kinetic.gas_box(n=40, dim=2, radius=0.2, t_max=0.1)


# ---- harmonic oscillator and coherent states ---------------------------------------

def test_harmonic_states_match_finite_difference_eigenstates():
    omega = 1.3
    x = np.linspace(-10, 10, 2001)
    E, psi = quantum.solve_tise(0.5 * omega**2 * x**2, x, n_states=6)
    assert np.allclose(E, (np.arange(6) + 0.5) * omega, rtol=1e-4)
    for n in range(6):
        exact = quantum.harmonic_state(n, x, omega)
        assert abs(np.sum(exact * psi[n]) * (x[1] - x[0])) == pytest.approx(1.0, abs=1e-5)


def test_harmonic_states_are_orthonormal_at_high_n():
    x = np.linspace(-15, 15, 6001)
    dx = x[1] - x[0]
    states = np.array([quantum.harmonic_state(n, x) for n in (0, 7, 30, 31)])
    assert np.allclose(states @ states.T * dx, np.eye(4), atol=1e-10)


def test_coherent_state_is_poisson_superposition_of_number_states():
    x = np.linspace(-12, 12, 4001)
    alpha = 1.2 - 0.7j
    from math import factorial
    series = sum(np.exp(-abs(alpha) ** 2 / 2) * alpha**n / np.sqrt(float(factorial(n))) * quantum.harmonic_state(n, x)
                 for n in range(60))
    assert np.allclose(quantum.coherent_state(x, alpha), series, atol=1e-12)


def test_coherent_state_has_minimum_width_and_right_centre():
    omega, m = 2.0, 1.5
    x = np.linspace(-10, 10, 4001)
    x0, p0 = 1.4, -2.2
    psi = quantum.coherent_state(x, quantum.coherent_alpha(x0, p0, omega, m), omega, m)
    mean = quantum.expectation(x, psi, x)
    width = np.sqrt(quantum.expectation((x - mean) ** 2, psi, x))
    momentum = np.real(np.sum(np.conj(psi) * -1j * np.gradient(psi, x)) * (x[1] - x[0]))
    assert mean == pytest.approx(x0, abs=1e-8)
    assert width == pytest.approx(np.sqrt(1 / (2 * m * omega)), rel=1e-6)
    assert momentum == pytest.approx(p0, rel=1e-4)


def test_coherent_state_follows_classical_orbit_without_spreading():
    omega = 1.0
    x = np.linspace(-20, 20, 1024, endpoint=False)
    alpha = quantum.coherent_alpha(3.0, 1.0, omega)
    times, psi = quantum.split_step(quantum.coherent_state(x, alpha, omega), x, 0.5 * omega**2 * x**2,
                                    dt=0.005, steps=2000, save_every=100)
    dx = x[1] - x[0]
    for t, p in zip(times, psi):
        exact = quantum.coherent_state(x, alpha * np.exp(-1j * omega * t), omega) * np.exp(-0.5j * omega * t)
        assert abs(np.sum(np.conj(exact) * p) * dx) == pytest.approx(1.0, abs=1e-6)
        assert quantum.expectation(x, p, x) == pytest.approx(3.0 * np.cos(t) + 1.0 * np.sin(t), abs=1e-4)


# ---- atomic structure ------------------------------------------------------------

@pytest.mark.parametrize("j", [0.5, 1, 1.5, 2])
def test_angular_momentum_algebra(j):
    Jx, Jy, Jz = atomic.angular_momentum(j)
    assert np.allclose(Jx @ Jy - Jy @ Jx, 1j * Jz)
    assert np.allclose(Jx @ Jx + Jy @ Jy + Jz @ Jz, j * (j + 1) * np.eye(int(2 * j + 1)))


def test_spin_half_matrices_are_half_the_pauli_matrices():
    for J, sigma in zip(atomic.angular_momentum(0.5), quantum.PAULI):
        assert np.allclose(J, sigma / 2)


@pytest.mark.parametrize("l", [1, 2, 3])
def test_zero_field_gives_j_multiplets(l):
    xi = 0.37
    E = atomic.zeeman_levels(l, xi, [0.0])[0]
    lower, upper = l - 0.5, l + 0.5
    expected = np.sort([atomic.spin_orbit_energy(l, lower, xi)] * int(2 * lower + 1)
                       + [atomic.spin_orbit_energy(l, upper, xi)] * int(2 * upper + 1))
    assert np.allclose(E, expected)
    assert atomic.spin_orbit_energy(l, upper, xi) == pytest.approx(xi * l / 2)


@pytest.mark.parametrize("l", [1, 2])
def test_weak_field_splitting_follows_lande_g(l):
    xi, B = 1.0, 1e-5
    E0 = atomic.zeeman_levels(l, xi, [0.0])[0]
    E1 = atomic.zeeman_levels(l, xi, [B])[0]
    expected = []
    for j in (l - 0.5, l + 0.5):
        for mj in np.arange(-j, j + 1):
            expected.append(atomic.spin_orbit_energy(l, j, xi) + atomic.lande_g(l, j) * mj * B)
    assert np.allclose(E1, np.sort(expected), atol=1e-9)
    assert not np.allclose(E0, E1)
    assert atomic.lande_g(1, 1.5) == pytest.approx(4 / 3)
    assert atomic.lande_g(1, 0.5) == pytest.approx(2 / 3)


def test_strong_field_reaches_paschen_back_limit():
    l, xi, B = 1, 1e-3, 10.0
    E = atomic.zeeman_levels(l, xi, [B])[0]
    expected = np.sort([B * (ml + 2 * ms) + xi * ml * ms for ml, ms in atomic.basis_labels(l)])
    assert np.allclose(E, expected, atol=1e-6)


def test_hydrogen_fine_structure_agrees_with_dirac_and_experiment():
    for n, j in [(1, 0.5), (2, 0.5), (2, 1.5), (3, 2.5)]:
        assert atomic.hydrogen_fine_structure_eV(n, j) == pytest.approx(atomic.dirac_energy_eV(n, j), rel=2e-8)
    split_eV = atomic.hydrogen_fine_structure_eV(2, 1.5) - atomic.hydrogen_fine_structure_eV(2, 0.5)
    split_GHz = split_eV * constants.e / constants.h / 1e9
    assert split_GHz == pytest.approx(10.969, rel=0.01)       # measured 2P3/2 - 2P1/2 interval


# ---- radioactive decay ------------------------------------------------------------

def test_half_life_and_decay_constant_round_trip():
    assert nuclear.decay_constant(5730) == pytest.approx(1.2097e-4, rel=1e-4)   # carbon-14, per year
    assert nuclear.half_life(nuclear.decay_constant(3.7)) == pytest.approx(3.7)
    assert nuclear.remaining(1000, nuclear.decay_constant(2.0), 4.0) == pytest.approx(250)


def test_bateman_matches_matrix_exponential_and_conserves_nuclei():
    lambdas = [0.9, 0.3, 0.05, 0.0]
    t = np.linspace(0, 60, 25)
    N = nuclear.bateman(1000, lambdas, t)
    assert np.allclose(N, nuclear.decay_chain(1000, lambdas, t), rtol=1e-9, atol=1e-9)
    assert np.allclose(N.sum(axis=1), 1000)


def test_two_member_chain_daughter_peak():
    l1, l2 = 0.2, 1.1
    t_peak = np.log(l2 / l1) / (l2 - l1)                 # dN2/dt = 0
    t = np.linspace(0, 10, 100001)
    N2 = nuclear.bateman(1.0, [l1, l2], t)[:, 1]
    assert t[np.argmax(N2)] == pytest.approx(t_peak, abs=1e-3)


def test_secular_and_transient_equilibrium():
    t = np.array([200.0])
    secular = nuclear.bateman(1.0, [1e-4, 0.5], t)[0]
    assert 1e-4 * secular[0] == pytest.approx(0.5 * secular[1], rel=1e-3)       # equal activities
    transient = nuclear.bateman(1.0, [0.05, 0.2], t)[0]
    assert transient[1] / transient[0] == pytest.approx(0.05 / (0.2 - 0.05), rel=1e-6)


def test_decay_chain_handles_equal_constants():
    lam = 0.4
    t = np.linspace(0, 10, 11)
    N = nuclear.decay_chain(1.0, [lam, lam], t)
    assert np.allclose(N[:, 1], lam * t * np.exp(-lam * t))
    with pytest.raises(ValueError):
        nuclear.bateman(1.0, [lam, lam], t)


def test_monte_carlo_decay_is_binomial_around_exponential():
    N0, lam = 2000, 0.3
    t = np.linspace(0, 8, 41)
    N = nuclear.simulate_decay(N0, lam, t, trials=400, seed=3)
    p = np.exp(-lam * t)
    assert np.allclose(N.mean(axis=0), N0 * p, rtol=0.01, atol=2)
    var = N0 * p * (1 - p)
    assert np.allclose(N.var(axis=0)[1:], var[1:], rtol=0.2)


# ---- circuits ----------------------------------------------------------------------

def test_rc_numerics_match_exponentials():
    R, C, V0 = 2e3, 50e-6, 9.0
    t, state = circuits.rc_trajectory(R, C, V=V0, t_max=0.5)
    q, I = state.T
    assert np.allclose(q / C, circuits.rc_charge(t, V0, R, C), atol=1e-8)
    assert np.allclose(I, V0 / R * np.exp(-t / (R * C)), atol=1e-10)
    t, state = circuits.rc_trajectory(R, C, q0=C * V0, t_max=0.5)
    q = state[:, 0]
    assert np.allclose(q / C, circuits.rc_discharge(t, V0, R, C), atol=1e-8)
    assert circuits.rc_discharge(R * C, 1.0, R, C) == pytest.approx(np.exp(-1))     # 37% after one tau


def test_lc_circuit_conserves_energy_and_oscillates_at_omega0():
    L, C = 0.2, 5e-6
    w0 = circuits.resonant_frequency(L, C)
    t, state = circuits.rlc_trajectory(0.0, L, C, q0=1e-5, t_max=4 * 2 * np.pi / w0, n=2000)
    q, I = state.T
    energy = q**2 / (2 * C) + 0.5 * L * I**2
    assert np.ptp(energy) < 1e-6 * energy[0]
    assert np.allclose(q, 1e-5 * np.cos(w0 * t), atol=1e-12)


def test_critical_damping_and_quality_factor():
    L, C = 0.1, 1e-4
    Rc = 2 * np.sqrt(L / C)
    t, state = circuits.rlc_trajectory(Rc, L, C, q0=1.0, t_max=0.2, n=4000)
    q = state[:, 0]
    a = Rc / (2 * L)
    assert np.allclose(q, (1 + a * t) * np.exp(-a * t), atol=1e-8)
    assert q.min() > -1e-12                              # no overshoot
    assert circuits.quality_factor(Rc, L, C) == pytest.approx(0.5)


def test_driven_rlc_steady_state_and_bandwidth():
    R, L, C, V0 = 10.0, 0.05, 2e-6, 1.0
    w0 = circuits.resonant_frequency(L, C)
    for w in (0.8 * w0, w0, 1.25 * w0):
        t, state = circuits.rlc_trajectory(R, L, C, V=lambda t, w=w: V0 * np.cos(w * t), t_max=0.25, n=20000)
        I = state[:, 1]
        late = t > 0.2
        assert np.abs(I[late]).max() == pytest.approx(circuits.current_amplitude(w, V0, R, L, C), rel=2e-3)
    Q = circuits.quality_factor(R, L, C)
    half_power = 1 / np.sqrt(2) * circuits.current_amplitude(w0, V0, R, L, C)
    w = np.linspace(0.5 * w0, 1.5 * w0, 400001)
    above = w[circuits.current_amplitude(w, V0, R, L, C) >= half_power]
    assert above[-1] - above[0] == pytest.approx(w0 / Q, rel=1e-4)
    assert circuits.impedance(w0, R, L, C) == pytest.approx(R)


def test_decay_chain_from_daughter_only_is_a_single_exponential():
    t = np.linspace(0, 5, 6)
    N = nuclear.decay_chain([0.0, 100.0, 0.0], [0.5, 0.9, 0.0], t)
    assert np.allclose(N[:, 0], 0)
    assert np.allclose(N[:, 1], 100 * np.exp(-0.9 * t))
    assert np.allclose(N[:, 1] + N[:, 2], 100)


def test_bateman_nearly_equal_rates_with_stable_product():
    t = np.array([0., 1., 3.])
    N = nuclear.bateman(1, [1, 1 + 1e-9, 1 + 2e-9, 0], t)
    # The first three populations approach the equal-rate Poisson solution.
    expected = np.exp(-t[:, None]) * np.column_stack((np.ones_like(t), t, t**2 / 2))
    np.testing.assert_allclose(N[:, :3], expected, atol=2e-9, rtol=0)
    np.testing.assert_array_equal(N[0], [1, 0, 0, 0])
    np.testing.assert_allclose(N.sum(axis=1), 1, atol=1e-13, rtol=0)
    assert np.all(N >= 0)
