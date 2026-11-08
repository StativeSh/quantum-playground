import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from pendulum import simulate


def test_energy_is_conserved():
    g, L = 9.81, 1.0
    _, theta, omega = simulate(g=g, length=L)
    energy = 0.5 * omega**2 - (g / L) * np.cos(theta)
    assert np.ptp(energy) < 1e-6
