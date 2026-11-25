"""Analytic limits and conservation laws for the course models."""
import numpy as np
import pytest
from scipy.constants import G, mu_0

from qplay import circuits, em, gravity, integrators, mechanics, nuclear, thermal, waves


def test_induction_and_fields():
    assert em.rod_emf(.4, .2, 3) == pytest.approx(.24)
    assert em.coil_emf(100, .2, .01, 10, np.pi/20) == pytest.approx(2)
    assert em.coil_emf(100, .2, .01, 10, 0) == 0
    assert em.wire_field(2, .5) * np.pi == pytest.approx(mu_0*2)
    assert em.solenoid_field(2000, .5) == pytest.approx(mu_0*1000)


def test_gravity_symmetry_and_energy():
    m = 1/G
    np.testing.assert_allclose(gravity.field([0, 0], [m, m], [[-2, 0], [2, 0]]), [0, 0])
    assert gravity.potential([2, 0], [m], [[0, 0]]) == pytest.approx(-.5)
    assert gravity.escape_speed(m, 2)**2 / 2 == pytest.approx(.5)
    assert gravity.synchronous_radius(m, 2*np.pi) == pytest.approx(1)


@pytest.mark.parametrize("e", [0., .4, 1.])
@pytest.mark.parametrize("a,b,n", [([3.], [0.], [1.]), ([3., 2.], [0., -1.], [1., 0.])])
def test_collision(e, a, b, n):
    a, b, n = map(np.asarray, (a, b, n))
    v, w = mechanics.collision(2, 1, a, b, n, e)
    np.testing.assert_allclose(2*v + w, 2*a + b)
    assert (w-v)@n == pytest.approx(e*((a-b)@n))
    assert a@a + b@b/2 - v@v - w@w/2 == pytest.approx((1-e**2)*((a-b)@n)**2/3)


def test_optics():
    assert waves.grating_angle(1, 5e-7, 1e-6) == pytest.approx(np.pi/6)
    assert waves.grating_angle(3, 5e-7, 1e-6) is None
    assert waves.slit_envelope(0, 1e-6, 5e-7) == 1
    assert waves.slit_envelope(np.pi/6, 1e-6, 5e-7) < 1e-25
    assert waves.image_distance(.1, .2) == pytest.approx(.2)
    assert np.isinf(waves.image_distance(.1, .1))
    assert waves.refraction(np.pi/6, 1, 1.5) == pytest.approx(np.arcsin(1/3))
    assert waves.refraction(np.pi/3, 1.5, 1) is None


def test_thermal_energy_balance():
    np.testing.assert_allclose(thermal.heating_curve([0, 20, 30, 40, 60], 2, 260, 270, 1, 10, 2),
                               [260, 270, 270, 270, 275])
    assert thermal.cooling(np.log(2), 300, 280, 1) == pytest.approx(290)


def test_binding_energy():
    # Odd A eliminates the pairing term; mirror nuclei isolate the Coulomb term.
    assert nuclear.binding_energy_per_nucleon(27, 13)-nuclear.binding_energy_per_nucleon(27, 14) == pytest.approx(.711*26/(27*3))
    assert nuclear.binding_energy_per_nucleon(56,26) == pytest.approx(8.79, abs=.15)


@pytest.mark.parametrize("old,new,args", [
    (mechanics.pendulum, mechanics.pendulum_trajectory, ()),
    (mechanics.harmonic_oscillator, mechanics.oscillator_trajectory, ()),
    (mechanics.projectile, mechanics.projectile_trajectory, (2,45)),
    (em.charged_particle, em.particle_trajectory, (1,1,[0,0,0],[0,0,1],[0,0,0],[1,0,0],1)),
    (circuits.rc_circuit, circuits.rc_trajectory, (1,1)),
    (circuits.rlc_series, circuits.rlc_trajectory, (1,1,1)),
    (mechanics.nbody, mechanics.nbody_trajectory, ([1],[[0,0]],[[1,1]],1)),
])
def test_legacy_histories(old, new, args):
    t, y = new(*args)
    with pytest.warns(DeprecationWarning):
        legacy_t, *columns = old(*args)
    np.testing.assert_equal(t, legacy_t)
    legacy = np.column_stack([x.reshape(len(t), -1) for x in columns])
    np.testing.assert_allclose(legacy, y[:, :legacy.shape[1]])


@pytest.mark.parametrize("old,new", [(integrators.euler, integrators.euler_trajectory),
                                    (integrators.rk4, integrators.rk4_trajectory)])
def test_grid_compatibility(old, new):
    args = (lambda t,y: -y, [1.], [0, .1])
    with pytest.warns(DeprecationWarning):
        np.testing.assert_equal(old(*args), new(*args)[1])


def test_verlet_compatibility():
    args = (lambda x: -x, [1.], [0.], [0, .1])
    with pytest.warns(DeprecationWarning):
        np.testing.assert_equal(np.column_stack(integrators.velocity_verlet(*args)), integrators.verlet_trajectory(*args)[1])


def test_binding_energy_curve_and_valley_of_stability():
    # Computing a whole curve at once: the most bound isobar is the stable one.
    for A, stable_Z in [(27, 13), (56, 26), (127, 53), (208, 82)]:
        Z = np.arange(1, A)
        assert Z[np.argmax(nuclear.binding_energy_per_nucleon(A, Z))] == stable_Z
    A = np.arange(20, 240, 2)
    Z = np.round(A / (1.98 + 0.0155 * A**(2/3))).astype(int)             # near the stability line
    assert 54 <= A[np.argmax(nuclear.binding_energy_per_nucleon(A, Z))] <= 64   # iron-nickel peak
    assert isinstance(nuclear.binding_energy_per_nucleon(56, 26), float)


@pytest.mark.parametrize("A,Z", [(56.0, 26), (56, 26.0), (56, 0), (56, 56), ([56, 4], [26, 4])])
def test_binding_energy_rejects_impossible_nuclei(A, Z):
    with pytest.raises(ValueError):
        nuclear.binding_energy_per_nucleon(A, Z)


@pytest.mark.parametrize("call", [
    lambda: thermal.heating_curve(1, 0, 260, 270, 1, 10, 2),          # no mass
    lambda: thermal.heating_curve(1, 1, 280, 270, 1, 10, 2),          # starts above melting
    lambda: thermal.heating_curve(-1, 1, 260, 270, 1, 10, 2),         # heat removed
    lambda: thermal.cooling(1, 300, 280, -1),                         # negative rate
    lambda: waves.grating_angle(1, 0, 1e-6),
    lambda: waves.slit_envelope(0, -1e-6, 5e-7),
    lambda: waves.image_distance(0.1, 0),                             # object at the lens
    lambda: waves.image_distance(0, 0.2),                             # zero focal length
    lambda: waves.refraction(0.1, 0, 1.5),
    lambda: waves.refraction(2.0, 1, 1.5),                            # beyond grazing incidence
], ids=["mass", "start", "heat", "rate", "grating", "slit", "object", "focal", "index", "angle"])
def test_course_models_reject_unphysical_input(call):
    with pytest.raises(ValueError):
        call()
