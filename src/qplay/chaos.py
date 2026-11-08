r"""Chaos and fractals: Lorenz system, logistic map, Mandelbrot and Julia sets.

Logistic map: $x_{n+1} = r x_n (1 - x_n)$.
"""

from __future__ import annotations

import numpy as np

from .integrators import solve


def lorenz(state0=(1.0, 1.0, 1.0), sigma=10.0, rho=28.0, beta=8 / 3, t_max=40.0, n=4000):
    """Lorenz system. Returns ``(t, y)`` with columns ``x, y, z``."""
    def rhs(_, s):
        x, y, z = s
        return [sigma * (y - x), x * (rho - z) - y, x * y - beta * z]

    return solve(rhs, state0, (0, t_max), n, rtol=1e-9, atol=1e-11)


def logistic_map(r, x0=0.5, n=100):
    """First ``n`` iterates (starting with ``x0``) of the logistic map."""
    x = np.empty(n)
    x[0] = x0
    for i in range(n - 1):
        x[i + 1] = r * x[i] * (1 - x[i])
    return x


def bifurcation(r_values, n_transient=500, n_keep=100, x0=0.5):
    """Attractor of the logistic map for each ``r``. Returns flat arrays ``(r, x)`` for scatter plots."""
    r_values = np.asarray(r_values, float)
    x = np.full_like(r_values, x0)
    for _ in range(n_transient):
        x = r_values * x * (1 - x)
    rs, xs = [], []
    for _ in range(n_keep):
        x = r_values * x * (1 - x)
        rs.append(r_values.copy())
        xs.append(x.copy())
    return np.concatenate(rs), np.concatenate(xs)


def lyapunov_logistic(r, n=20000, x0=0.4, n_transient=200):
    r"""Lyapunov exponent $\lambda=\langle\ln|r(1-2x)|\rangle$; positive means chaos."""
    x = x0
    for _ in range(n_transient):
        x = r * x * (1 - x)
    total = 0.0
    for _ in range(n):
        x = r * x * (1 - x)
        total += np.log(abs(r * (1 - 2 * x)) + 1e-300)
    return total / n


def escape_time(c, max_iter=100, z0=0.0):
    """Iterations of $z\\to z^2+c$ before $|z|>2$ (``max_iter`` if it never escapes)."""
    c = np.asarray(c, complex)
    z = np.broadcast_to(np.asarray(z0, complex), c.shape).copy()
    count = np.full(c.shape, max_iter, dtype=int)
    alive = np.ones(c.shape, dtype=bool)
    for i in range(max_iter):
        z[alive] = z[alive] ** 2 + c[alive]
        escaped = alive & (np.abs(z) > 2)
        count[escaped] = i
        alive &= ~escaped
    return count


def _grid(xlim, ylim, width, height):
    X, Y = np.meshgrid(np.linspace(*xlim, width), np.linspace(*ylim, height))
    return X + 1j * Y


def mandelbrot(xlim=(-2.2, 0.8), ylim=(-1.2, 1.2), width=600, height=400, max_iter=100):
    return escape_time(_grid(xlim, ylim, width, height), max_iter)


def julia(c, xlim=(-1.6, 1.6), ylim=(-1.2, 1.2), width=600, height=400, max_iter=100):
    """Julia set for $z\\to z^2 + c$: the grid supplies the starting points $z_0$."""
    z0 = _grid(xlim, ylim, width, height)
    return escape_time(np.full(z0.shape, c, dtype=complex), max_iter, z0=z0)
