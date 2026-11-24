"""Time integrators.

Convention: a state history has shape ``(n_times, n_dim)``.
"""

from __future__ import annotations

from collections.abc import Callable
import warnings

import numpy as np
from numpy.typing import ArrayLike
from scipy.integrate import solve_ivp

__all__ = [
    "solve", "euler_trajectory", "euler", "rk4_trajectory", "rk4", "verlet_trajectory",
    "velocity_verlet",
]


def solve(
    f: Callable[[float, np.ndarray], ArrayLike], y0: ArrayLike, t_span: tuple[float, float], n: int
    = 1000, method: str = "DOP853", rtol: float = 1e-10, atol: float = 1e-12, **kwargs,
) -> tuple[np.ndarray, np.ndarray]:
    """Adaptive integration of ``y' = f(t, y)``, sampled at ``n`` evenly spaced times.

    Supply complex initial values for complex dynamics and a method supporting them.
    Returns ``(t, y)`` with ``y.shape == (n, len(y0))``.
    """
    t_eval = np.linspace(t_span[0], t_span[1], n)
    sol = solve_ivp(f, t_span, np.atleast_1d(np.asarray(y0)), t_eval=t_eval,
                    method=method, rtol=rtol, atol=atol, **kwargs)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.t, sol.y.T


def euler_trajectory(
    f: Callable[[float, np.ndarray], ArrayLike], y0: ArrayLike, t: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Explicit Euler (first order). Included to show how badly it behaves.

    Return time and a state matrix with columns for solution components.
    """
    t = np.asarray(t, float)
    y = np.empty((len(t), np.size(y0)))
    y[0] = y0
    for i in range(len(t) - 1):
        y[i + 1] = y[i] + (t[i + 1] - t[i]) * np.asarray(f(t[i], y[i]))
    return t, y


def euler(f, y0, t):
    """Compatibility interface. Use :func:`euler_trajectory` for time and a state matrix."""
    warnings.warn("euler is deprecated; use euler_trajectory", DeprecationWarning, stacklevel=2)
    t, y = euler_trajectory(f, y0, t)
    return y


def rk4_trajectory(
    f: Callable[[float, np.ndarray], ArrayLike], y0: ArrayLike, t: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Classical fourth-order Runge-Kutta on the time grid ``t``.

    Return time and a state matrix with columns for solution components.
    """
    t = np.asarray(t, float)
    y = np.empty((len(t), np.size(y0)))
    y[0] = y0
    for i in range(len(t) - 1):
        h = t[i + 1] - t[i]
        k1 = np.asarray(f(t[i], y[i]))
        k2 = np.asarray(f(t[i] + h / 2, y[i] + h / 2 * k1))
        k3 = np.asarray(f(t[i] + h / 2, y[i] + h / 2 * k2))
        k4 = np.asarray(f(t[i] + h, y[i] + h * k3))
        y[i + 1] = y[i] + h / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return t, y


def rk4(f, y0, t):
    """Compatibility interface. Use :func:`rk4_trajectory` for time and a state matrix."""
    warnings.warn("rk4 is deprecated; use rk4_trajectory", DeprecationWarning, stacklevel=2)
    t, y = rk4_trajectory(f, y0, t)
    return y


def verlet_trajectory(
    accel: Callable[[np.ndarray], ArrayLike], x0: ArrayLike, v0: ArrayLike, t: ArrayLike,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Symplectic velocity-Verlet for ``x'' = accel(x)``.

    Return time and a state matrix with columns for positions then velocities.
    """
    t = np.asarray(t, float)
    x0 = np.atleast_1d(np.asarray(x0, float))
    x = np.empty((len(t), x0.size))
    v = np.empty_like(x)
    x[0], v[0] = x0, v0
    a = np.asarray(accel(x[0]))
    for i in range(len(t) - 1):
        h = t[i + 1] - t[i]
        x[i + 1] = x[i] + v[i] * h + 0.5 * a * h * h
        a_new = np.asarray(accel(x[i + 1]))
        v[i + 1] = v[i] + 0.5 * (a + a_new) * h
        a = a_new
    return t, np.column_stack((x, v))


def velocity_verlet(accel, x0, v0, t):
    """Compatibility interface. Use :func:`verlet_trajectory` for time and a state matrix."""
    warnings.warn("velocity_verlet is deprecated; use verlet_trajectory", DeprecationWarning, stacklevel=2)
    t, y = verlet_trajectory(accel, x0, v0, t)
    return tuple(np.hsplit(y, 2))
