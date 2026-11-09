import numpy as np
import pytest
import sympy as sp
from scipy.integrate import quad

from qplay import complexplane, dynamics, hamiltonian, integrators, linalg, quantum, statmech

# ---- hydrogen ----------------------------------------------------------------

@pytest.mark.parametrize("n,l", [(1, 0), (2, 0), (2, 1), (3, 2), (4, 1)])
def test_hydrogen_radial_normalised_and_mean_radius(n, l):
    norm = quad(lambda r: quantum.hydrogen_radial(n, l, r) ** 2 * r**2, 0, np.inf)[0]
    mean_r = quad(lambda r: quantum.hydrogen_radial(n, l, r) ** 2 * r**3, 0, np.inf)[0]
    assert norm == pytest.approx(1.0, abs=1e-8)
    assert mean_r == pytest.approx((3 * n**2 - l * (l + 1)) / 2, rel=1e-8)


def test_hydrogen_radial_node_count():
    r = np.linspace(1e-3, 60, 20000)
    R = quantum.hydrogen_radial(4, 1, r)
    assert np.count_nonzero(np.diff(np.sign(R))) == 4 - 1 - 1


def test_spherical_harmonics_orthonormal():
    theta = np.linspace(0, np.pi, 400)
    phi = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    T, P = np.meshgrid(theta, phi, indexing="ij")
    dA = np.sin(T) * (theta[1] - theta[0]) * (phi[1] - phi[0])

    def inner(a, b):
        return np.sum(np.conj(quantum.spherical_harmonic(*a, T, P)) * quantum.spherical_harmonic(*b, T, P) * dA)

    assert inner((2, 1), (2, 1)).real == pytest.approx(1.0, abs=2e-3)
    assert inner((2, -1), (2, -1)).real == pytest.approx(1.0, abs=2e-3)
    assert abs(inner((2, 1), (2, -1))) < 1e-3
    assert abs(inner((1, 0), (3, 0))) < 1e-3


def test_y10_matches_closed_form():
    theta = np.linspace(0, np.pi, 7)
    assert np.allclose(quantum.spherical_harmonic(1, 0, theta, 0), np.sqrt(3 / (4 * np.pi)) * np.cos(theta))


def test_p_orbital_has_nodal_plane():
    X, Z, rho = quantum.hydrogen_density_xz(2, 1, 0, points=101)
    assert np.allclose(rho[50, :], 0, atol=1e-12)        # z = 0 row
    assert rho.max() > 0


# ---- 2D quantum ----------------------------------------------------------------

def test_split_step_2d_free_spread_and_norm():
    x = y = np.linspace(-30, 30, 256, endpoint=False)
    dx = x[1] - x[0]
    psi0 = quantum.gaussian_wavepacket_2d(x, y, sigma_x=1.0, sigma_y=2.0)
    _, psi = quantum.split_step_2d(psi0, x, y, np.zeros((256, 256)), dt=0.01, steps=200)
    rho = np.abs(psi[-1]) ** 2
    X, Y = np.meshgrid(x, y)
    assert rho.sum() * dx * dx == pytest.approx(1.0, abs=1e-10)
    width_x = np.sqrt((X**2 * rho).sum() * dx * dx)
    width_y = np.sqrt((Y**2 * rho).sum() * dx * dx)
    t = 2.0
    assert width_x == pytest.approx(np.sqrt(1 + (t / 2) ** 2), rel=1e-4)
    assert width_y == pytest.approx(2 * np.sqrt(1 + (t / 8) ** 2), rel=1e-4)


def test_double_slit_potential_has_two_openings():
    y = np.linspace(-10, 10, 401)
    V = quantum.double_slit_potential(np.array([-1.0, 0.0, 1.0]), y, separation=5, slit_width=1)
    wall = V[:, 1]
    assert np.all(V[:, [0, 2]] == 0)
    openings = np.count_nonzero(np.diff((wall == 0).astype(int)) == 1)
    assert openings == 2


# ---- Ising -------------------------------------------------------------------

def test_ising_energy_ground_state():
    assert statmech.ising_energy(np.ones((8, 8))) / 64 == -2.0
    checker = np.indices((8, 8)).sum(0) % 2 * 2 - 1
    assert statmech.ising_energy(checker) / 64 == 2.0


def test_ising_low_temperature_matches_onsager():
    _, m, _ = statmech.ising(L=32, T=1.5, sweeps=400, seed=1)
    assert np.mean(np.abs(m[100:])) == pytest.approx(statmech.onsager_magnetization(1.5), abs=0.01)


def test_ising_high_temperature_is_disordered():
    _, m, e = statmech.ising(L=32, T=4.0, sweeps=400, start="hot", seed=2)
    assert np.mean(np.abs(m[100:])) < 0.1
    assert -1.0 < np.mean(e[100:]) < -0.4


def test_onsager_limits():
    assert statmech.T_CRITICAL == pytest.approx(2.269185, abs=1e-6)
    assert statmech.onsager_magnetization(0.5) == pytest.approx(1.0, abs=1e-6)
    assert statmech.onsager_magnetization(3.0) == 0.0


# ---- phase planes -------------------------------------------------------------

@pytest.mark.parametrize("A,kind", [
    ([[-1, 0], [0, -2]], "stable node"),
    ([[1, 0], [0, 2]], "unstable node"),
    ([[1, 0], [0, -1]], "saddle"),
    ([[0, 1], [-1, 0]], "center"),
    ([[-0.1, 1], [-1, -0.1]], "stable spiral"),
    ([[1, 1], [-1, 1]], "unstable spiral"),
])
def test_classify_linear_systems(A, kind):
    assert dynamics.classify_fixed_point(np.array(A, float)) == kind


def test_damped_pendulum_fixed_points():
    def f(s):
        return [s[1], -np.sin(s[0]) - 0.3 * s[1]]

    pts = dynamics.fixed_points(f, [(0.1, 0.1), (3.0, 0.0), (-3.0, 0.0)])
    kinds = {round(p[0], 6): dynamics.classify_fixed_point(dynamics.jacobian(f, p)) for p in pts}
    assert kinds[0.0] == "stable spiral"
    assert kinds[round(np.pi, 6)] == "saddle"
    assert kinds[round(-np.pi, 6)] == "saddle"


def test_jacobian_of_known_map():
    J = dynamics.jacobian(lambda s: [s[0] ** 2 * s[1], np.sin(s[1])], [2.0, 0.5])
    assert np.allclose(J, [[2 * 2 * 0.5, 4], [0, np.cos(0.5)]], atol=1e-8)


# ---- Hamiltonian --------------------------------------------------------------

def test_hamilton_equations_harmonic_oscillator():
    q, p, m, k = sp.symbols("q p m k", positive=True)
    qdot, pdot = hamiltonian.hamilton_equations(p**2 / (2 * m) + k * q**2 / 2, [q], [p])
    assert sp.simplify(qdot[0] - p / m) == 0
    assert sp.simplify(pdot[0] + k * q) == 0


def test_legendre_transform_pendulum():
    t, m, l, g = sp.symbols("t m l g", positive=True)
    th = sp.Function("theta")(t)
    L = m * l**2 * sp.diff(th, t) ** 2 / 2 + m * g * l * sp.cos(th)
    H, (q,), (p,) = hamiltonian.legendre_transform(L, [th], t)
    assert sp.simplify(H - (p**2 / (2 * m * l**2) - m * g * l * sp.cos(q))) == 0


def test_hamiltonian_simulation_conserves_energy_and_closes_orbit():
    q, p = sp.symbols("q p")
    H = p**2 / 2 + q**2 / 2
    rhs = hamiltonian.to_numeric_rhs(H, [q], [p])
    energy = hamiltonian.to_numeric_energy(H, [q], [p])
    _, y = integrators.solve(rhs, [1.0, 0.0], (0, 2 * np.pi), n=100)
    assert np.allclose(y[-1], [1.0, 0.0], atol=1e-8)
    assert np.ptp(energy(y)) < 1e-9


# ---- complex plane ------------------------------------------------------------

@pytest.mark.parametrize("f,expected", [
    (lambda z: z**3, 3),
    (lambda z: 1 / z, -1),
    (lambda z: z - 2, 0),
    (lambda z: (z - 0.5) ** 2 / (z + 0.3), 1),
    (np.exp, 0),
])
def test_argument_principle(f, expected):
    assert complexplane.winding_number(f) == expected


def test_domain_coloring_hue_and_range():
    rgb = complexplane.domain_coloring(lambda z: z, n=101)
    assert rgb.shape == (101, 101, 3) and rgb.min() >= 0 and rgb.max() <= 1
    r, g, b = rgb[50, 75]                              # z = +1: arg 0 -> red
    assert r > g and r > b
    assert np.all(complexplane.domain_coloring(lambda z: 1 / z, n=101)[50, 50] == 1.0)  # pole -> white


# ---- linear algebra -----------------------------------------------------------

def test_gram_schmidt_orthonormal_and_drops_dependent():
    B = linalg.gram_schmidt([[1, 1, 0], [1, 0, 1], [2, 1, 1], [0, 0, 3]])
    assert B.shape == (3, 3)
    assert np.allclose(B @ B.T, np.eye(3))


def test_power_iteration_dominant_eigenpair():
    A = np.array([[4.0, 1.0, 0.0], [1.0, 3.0, 1.0], [0.0, 1.0, 2.0]])
    lam, v = linalg.power_iteration(A)
    assert lam == pytest.approx(np.linalg.eigvalsh(A).max(), abs=1e-9)
    assert np.allclose(A @ v, lam * v, atol=1e-5)


def test_unit_circle_image_semi_axes_are_singular_values():
    A = linalg.shear(1.5) @ linalg.rotation(0.4) @ np.diag([2.0, 0.5])
    pts = linalg.unit_circle_image(A, n=20000)
    radii = np.linalg.norm(pts, axis=0)
    sigma, _ = linalg.singular_axes(A)
    assert radii.max() == pytest.approx(sigma[0], rel=1e-6)
    assert radii.min() == pytest.approx(sigma[1], rel=1e-6)
    assert np.linalg.det(linalg.rotation(1.1)) == pytest.approx(1.0)


def test_absorbing_layer_removes_outgoing_packet():
    x = np.linspace(-40, 40, 1024, endpoint=False)
    psi0 = quantum.gaussian_wavepacket(x, x0=0, sigma=2, k0=3)
    _, psi = quantum.split_step(psi0, x, quantum.absorbing_layer(x, width=10), dt=0.01, steps=3000)
    assert np.sum(np.abs(psi[-1]) ** 2) * (x[1] - x[0]) < 1e-3


def test_double_slit_wall_does_not_leak():
    x = np.linspace(-20, 60, 256, endpoint=False)
    y = np.linspace(-40, 40, 256, endpoint=False)
    V = quantum.double_slit_potential(x, y, slit_width=0.0) + quantum.absorbing_layer((x, y), 8.0)
    psi0 = quantum.gaussian_wavepacket_2d(x, y, x0=-8, sigma_x=2.5, sigma_y=8, kx=3.0)
    _, psi = quantum.split_step_2d(psi0, x, y, V, dt=0.02, steps=400)
    dx = x[1] - x[0]
    assert (np.abs(psi[-1][:, x > 1]) ** 2).sum() * dx * dx < 0.01


def test_double_slit_dark_fringes_match_path_difference():
    run = quantum.double_slit_experiment(dt=0.02, t_max=16.0)
    y, screen, L = run["y"], run["screen"], run["screen_x"]
    lam, d = 2 * np.pi / 3.0, 5.0
    path_diff = np.hypot(L, y + d / 2) - np.hypot(L, y - d / 2)
    first_dark = y[(y > 0) & (y < 15)][np.argmin(screen[(y > 0) & (y < 15)])]
    predicted = y[(y > 0) & (y < 15)][np.argmin(np.abs(path_diff[(y > 0) & (y < 15)] - lam / 2))]
    assert first_dark == pytest.approx(predicted, abs=0.6)
    assert screen[np.argmin(np.abs(y))] == pytest.approx(1.0, abs=0.02)   # bright centre
