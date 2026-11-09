"""Time integrators.

Convention: a state history has shape ``(n_times, n_dim)``.
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp


def solve(f, y0, t_span, n=1000, method="DOP853", rtol=1e-10, atol=1e-12, **kwargs):
    """Adaptive integration of ``y' = f(t, y)``, sampled at ``n`` evenly spaced times.

    Returns ``(t, y)`` with ``y.shape == (n, len(y0))``.
    """
    t_eval = np.linspace(t_span[0], t_span[1], n)
    sol = solve_ivp(f, t_span, np.atleast_1d(np.asarray(y0, float)), t_eval=t_eval,
                    method=method, rtol=rtol, atol=atol, **kwargs)
    if not sol.success:
        raise RuntimeError(sol.message)
    return sol.t, sol.y.T


def euler(f, y0, t):
    """Explicit Euler (first order). Included to show how badly it behaves."""
    t = np.asarray(t, float)
    y = np.empty((len(t), np.size(y0)))
    y[0] = y0
    for i in range(len(t) - 1):
        y[i + 1] = y[i] + (t[i + 1] - t[i]) * np.asarray(f(t[i], y[i]))
    return y


def rk4(f, y0, t):
    """Classical fourth-order Runge-Kutta on the time grid ``t``."""
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
    return y


def velocity_verlet(accel, x0, v0, t):
    """Symplectic velocity-Verlet for ``x'' = accel(x)``. Returns ``(x, v)``.

    Energy error stays bounded over very long runs, unlike Euler or RK4.
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
    return x, v
