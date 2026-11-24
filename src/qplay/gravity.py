"""Newtonian gravitational fields in SI units."""
import numpy as np
from numpy.typing import ArrayLike, NDArray
from scipy.constants import G

__all__ = [
    "field", "potential", "escape_speed", "synchronous_radius",
]


def _sources(point, masses, positions):
    displacement = np.asarray(point, float) - np.asarray(positions, float)
    masses = np.atleast_1d(np.asarray(masses, float))
    displacement = np.atleast_2d(displacement)
    if len(displacement) != len(masses):
        raise ValueError("supply one position per mass")
    radius = np.linalg.norm(displacement, axis=1)
    if np.any(radius == 0):
        raise ValueError("point-source field is singular at the source")
    return displacement, masses, radius


def field(point: ArrayLike, masses: ArrayLike, positions: ArrayLike) -> NDArray[np.float64]:
    r"""Acceleration at a point, $\mathbf g=-G\sum_i M_i\mathbf r_i/r_i^3$, with displacement from each source."""
    r, m, distance = _sources(point, masses, positions)
    return -G * ((m / distance**3)[:, None] * r).sum(axis=0)


def potential(point: ArrayLike, masses: ArrayLike, positions: ArrayLike) -> float:
    r"""Potential relative to infinity, $\Phi=-G\sum_i M_i/r_i$, in J/kg."""
    _, m, distance = _sources(point, masses, positions)
    return float(-G * np.sum(m / distance))


def escape_speed(mass: float, radius: float) -> float:
    r"""Minimum escape speed $v=\sqrt{2GM/r}$ from the centre-to-object distance in metres."""
    if mass <= 0 or radius <= 0:
        raise ValueError("mass and radius must be positive")
    return (2 * G * mass / radius)**0.5


def synchronous_radius(mass: float, period: float = 86164.1) -> float:
    r"""Circular orbit radius $r=(GM T^2/4\pi^2)^{1/3}$; prograde equatorial for a stationary satellite."""
    if mass <= 0 or period <= 0:
        raise ValueError("mass and period must be positive")
    return (G * mass * (period / (2 * np.pi))**2)**(1 / 3)
