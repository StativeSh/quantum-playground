r"""Electromagnetism: point charges, Laplace's equation, charged-particle motion.

Laplace: $\nabla^2 V = 0$.  Lorentz force: $m\dot{\mathbf v} = q(\mathbf E + \mathbf v\times\mathbf B)$.
"""

from __future__ import annotations

import numpy as np
from scipy import constants, sparse
from scipy.sparse.linalg import spsolve

from .integrators import solve

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


def charged_particle(q, m, E, B, r0, v0, t_max, n=1000):
    """Non-relativistic motion in uniform fields. Returns ``(t, r, v)``, each ``(n, 3)`` for r, v."""
    E = np.asarray(E, float)
    B = np.asarray(B, float)

    def rhs(_, s):
        v = s[3:]
        return np.concatenate([v, (q / m) * (E + np.cross(v, B))])

    t, y = solve(rhs, np.concatenate([r0, v0]), (0, t_max), n)
    return t, y[:, :3], y[:, 3:]
