r"""Electromagnetism: point charges, Laplace's equation, charged-particle motion.

Laplace: $\nabla^2 V = 0$.  Lorentz force: $m\dot{\mathbf v} = q(\mathbf E + \mathbf v\times\mathbf B)$.
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import ArrayLike
from scipy import constants, sparse
from scipy.sparse.linalg import spsolve

from .integrators import solve

__all__ = [
    "K_E", "point_charge_field", "point_charge_potential", "solve_laplace", "particle_trajectory",
    "charged_particle", "rod_emf", "coil_emf", "wire_field", "solenoid_field",
    "selector_speed", "gyroradius", "rod_braking_time",
    "flux_linkage",
]

K_E = 1 / (4 * np.pi * constants.epsilon_0)  # Coulomb constant, N m^2 / C^2


def point_charge_field(charges, positions, X, Y, k=1.0):
    """Electric field ``(Ex, Ey)`` of 2D-placed point charges on the grid ``(X, Y)``.

    Uses the $1/r^2$ law. ``k=1`` gives natural units; pass ``K_E`` for SI.
    """
    Ex = np.zeros_like(X, dtype=float)
    Ey = np.zeros_like(X, dtype=float)
    for q, (px, py) in zip(charges, positions):
        dx, dy = X - px, Y - py
        r3 = (dx**2 + dy**2) ** 1.5
        r3 = np.where(r3 == 0, np.inf, r3)
        Ex += k * q * dx / r3
        Ey += k * q * dy / r3
    return Ex, Ey


def point_charge_potential(charges, positions, X, Y, k=1.0):
    V = np.zeros_like(X, dtype=float)
    for q, (px, py) in zip(charges, positions):
        r = np.hypot(X - px, Y - py)
        V += k * q / np.where(r == 0, np.inf, r)
    return V


def solve_laplace(nx, ny, top=0.0, bottom=0.0, left=0.0, right=0.0):
    """Solve $\\nabla^2 V=0$ on an ``nx`` by ``ny`` grid with Dirichlet edges.

    Edge values are scalars or arrays (length ``nx`` for top/bottom, ``ny`` for left/right).
    Returns ``V`` with shape ``(ny, nx)``; row 0 is the bottom edge.
    """
    top = np.broadcast_to(np.asarray(top, float), (nx,))
    bottom = np.broadcast_to(np.asarray(bottom, float), (nx,))
    left = np.broadcast_to(np.asarray(left, float), (ny,))
    right = np.broadcast_to(np.asarray(right, float), (ny,))
    mx, my = nx - 2, ny - 2

    def lap(m):
        return sparse.diags([np.ones(m - 1), -2 * np.ones(m), np.ones(m - 1)], [-1, 0, 1])

    A = sparse.kron(sparse.identity(my), lap(mx)) + sparse.kron(lap(my), sparse.identity(mx))
    b = np.zeros((my, mx))
    b[0, :] -= bottom[1:-1]
    b[-1, :] -= top[1:-1]
    b[:, 0] -= left[1:-1]
    b[:, -1] -= right[1:-1]
    interior = spsolve(A.tocsc(), b.ravel()).reshape(my, mx)

    V = np.zeros((ny, nx))
    V[0], V[-1], V[:, 0], V[:, -1] = bottom, top, left, right
    V[1:-1, 1:-1] = interior
    return V


def particle_trajectory(
    q: float, m: float, E: ArrayLike, B: ArrayLike, r0: ArrayLike, v0: ArrayLike, t_max: float, n:
    int = 1000,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Non-relativistic motion in uniform fields.

    Return time and a state matrix with columns for x, y, z, vx, vy, vz.
    """
    E = np.asarray(E, float)
    B = np.asarray(B, float)

    def rhs(_, s):
        v = s[3:]
        return np.concatenate([v, (q / m) * (E + np.cross(v, B))])

    t, y = solve(rhs, np.concatenate([r0, v0]), (0, t_max), n)
    return t, y


def charged_particle(q, m, E, B, r0, v0, t_max, n=1000):
    """Compatibility interface. Use :func:`particle_trajectory` for time and a state matrix."""
    warnings.warn("charged_particle is deprecated; use particle_trajectory", DeprecationWarning, stacklevel=2)
    t, y = particle_trajectory(q, m, E, B, r0, v0, t_max, n)
    return t, y[:, :3], y[:, 3:]


def rod_emf(field: float, length: float, speed: float) -> float:
    r"""Motional emf in volts, $\varepsilon=B\ell v$, for mutually perpendicular rod, velocity and field."""
    return field * length * speed


def coil_emf(turns: int, field: float, area: float, omega: float, time: ArrayLike) -> float | np.ndarray:
    r"""Instantaneous volts, $\varepsilon=NBA\omega\sin(\omega t)$, starting at maximum flux."""
    return turns * field * area * omega * np.sin(omega * np.asarray(time))


def wire_field(current: float, radius: float) -> float:
    r"""Azimuthal field (tesla) outside a long straight wire, $B=\mu_0 I/(2\pi r)$."""
    from scipy.constants import mu_0
    if radius <= 0:
        raise ValueError("radius must be positive")
    return mu_0 * current / (2 * np.pi * radius)


def solenoid_field(turns_per_metre: float, current: float) -> float:
    r"""Interior axial field of a long air-core solenoid, $B=\mu_0 nI$ in tesla."""
    from scipy.constants import mu_0
    return mu_0 * turns_per_metre * current


def selector_speed(electric_field: float, magnetic_field: float) -> float:
    r"""Transmitted speed $v=E/B$ in m/s for perpendicular field magnitudes in V/m and T."""
    if electric_field < 0 or magnetic_field <= 0:
        raise ValueError("use a nonnegative electric and positive magnetic field magnitude")
    return electric_field / magnetic_field


def gyroradius(mass: float, charge: float, transverse_speed: float, field: float) -> float:
    r"""Nonrelativistic orbit radius $r=mv_\perp/|qB|$ in m (kg, C, m/s, T)."""
    if mass <= 0 or charge == 0 or field == 0 or transverse_speed < 0:
        raise ValueError("a charged particle needs positive mass, nonzero field and nonnegative speed")
    return mass * transverse_speed / abs(charge * field)


def rod_braking_time(mass: float, resistance: float, field: float, length: float) -> float:
    r"""Time constant $\tau=mR/(BL)^2$ in s for a rod on frictionless rails (kg, Ω, T, m)."""
    if min(mass, resistance, length) <= 0 or field == 0:
        raise ValueError("mass, resistance and length must be positive and field nonzero")
    return mass * resistance / (field * length)**2


def flux_linkage(turns: int, field: float, area: float, angle: float) -> float:
    r"""Flux linkage $N\Phi=NBA\cos\theta$ in Wb-turns for a uniform field (T).

    Supply the coil area in m² and the angle from the field to its normal in radians.
    """
    return float(turns * field * area * np.cos(angle))
