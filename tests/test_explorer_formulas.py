"""Independent limiting cases and reference data for the explorer's public oracles."""
import ast
from pathlib import Path

import numpy as np
import pytest

from qplay import chaos, circuits, em, gravity, nuclear, numerics, quantum, waves


def test_fixed_string_and_interference():
    # 40 m/s on a 2 m string; allowed wavelengths are 4/n metres.
    assert waves.string_harmonic(3, 2, 16, 0.01) == pytest.approx(30)
    assert waves.fringe_spacing(500e-9, 2, 0.5e-3) == pytest.approx(0.002)


def test_einstein_photoelectric_law():
    # A 1 PHz photon carries 4.135667697 eV.
    assert quantum.photoelectron_energy_eV(1e15, 2) == pytest.approx(2.135667697)
    assert quantum.photoelectron_energy_eV(1e14, 2) == 0
    assert quantum.threshold_frequency(2) == pytest.approx(4.83597848e14)


def test_capacitor_and_reaction_energy():
    assert circuits.capacitor_energy(2e-6, -3) == pytest.approx(9e-6)
    # D + T -> He-4 + n, total binding energies in MeV.
    assert nuclear.reaction_energy([2.2246, 8.4818], [28.2957, 0]) == pytest.approx(17.5893)
    assert nuclear.reaction_energy([28.2957], [2.2246, 8.4818]) == pytest.approx(-17.5893)


def test_field_balances():
    v = em.selector_speed(10000, 0.5)
    assert 2e-19 * 10000 == pytest.approx(2e-19 * v * 0.5, abs=1e-25)
    # Magnetic and centripetal forces balance, independent of charge sign.
    r = em.gyroradius(3e-26, -2e-19, 40000, 0.5)
    assert 3e-26 * 40000**2/r == pytest.approx(2e-19 * 40000 * 0.5, abs=1e-25)
    assert em.rod_braking_time(0.5, 4, 2, 0.5) == pytest.approx(2)


def test_lorenz_stability_boundary():
    assert chaos.lorenz_hopf_threshold(10, 8/3) == pytest.approx(470/19)


@pytest.mark.parametrize("fn,args", [
    (waves.string_harmonic, (0, 1, 1, 1)), (waves.fringe_spacing, (1, 1, 0)),
    (quantum.threshold_frequency, (-1,)), (quantum.photoelectron_energy_eV, (-1, 1)),
    (circuits.capacitor_energy, (-1, 1)), (em.selector_speed, (1, 0)),
    (em.gyroradius, (1, 0, 1, 1)), (em.rod_braking_time, (1, 1, 0, 1)),
    (chaos.lorenz_hopf_threshold, (1, 1)),
])
def test_invalid_parameters(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


def test_fit_line_reference_data():
    # Residuals [1, -2, 1] have RSS 6 and one residual degree of freedom.
    assert numerics.fit_line([-1, 0, 1], [1, 0, 5]) == pytest.approx(
        dict(gradient=2, intercept=2, gradientSE=np.sqrt(3), interceptSE=np.sqrt(2)))
    fit = numerics.fit_line([1, 1], [1, 3], through_origin=True)
    assert fit == pytest.approx(dict(gradient=2, intercept=0, gradientSE=1, interceptSE=0))
    assert numerics.fit_line([2, 4], [4, 10]) == dict(gradient=3, intercept=-2, gradientSE=None, interceptSE=None)


@pytest.mark.parametrize("x,y", [([1], [2]), ([1, 1], [2, 3]), ([1, 2], [1, np.nan]), ([[0, 1]], [[2, 3]])])
def test_invalid_fit(x, y):
    with pytest.raises(ValueError):
        numerics.fit_line(x, y)


def test_documented_compatibility_interfaces():
    root = Path(__file__).resolve().parents[1]
    removal = (root / "docs/migration.md").read_text().split("## Removal in 2.0\n", 1)[1].split("\n## ", 1)[0]
    for module in (root / "src/qplay").glob("*.py"):
        for node in ast.walk(ast.parse(module.read_text())):
            if isinstance(node, ast.FunctionDef) and (ast.get_docstring(node) or "").startswith("Compatibility interface"):
                assert f"| `{module.stem}.{node.name}` |" in removal


def test_orbits_flux_and_matter_wavelength():
    from scipy.constants import G, h
    assert gravity.circular_speed(1/G, 4) == pytest.approx(0.5)
    assert gravity.orbital_period(4, 1) == pytest.approx(16*np.pi)
    assert em.flux_linkage(4, 0.5, 2, np.pi) == pytest.approx(-4)
    assert quantum.de_broglie_wavelength(h / 1e-9) == pytest.approx(1e-9, abs=1e-20)
    with pytest.raises(ValueError):
        gravity.orbital_period(-1, 1)
    with pytest.raises(ValueError):
        quantum.de_broglie_wavelength(0)
