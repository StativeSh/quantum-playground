"""Basic numerical methods written out in full, for learning."""

from __future__ import annotations

import numpy as np


def bisect(f, a, b, tol=1e-12, max_iter=200):
    """Root of ``f`` in ``[a, b]`` by bisection; ``f(a)`` and ``f(b)`` must differ in sign."""
    fa, fb = f(a), f(b)
    if fa * fb > 0:
        raise ValueError("f(a) and f(b) must have opposite signs")
    for _ in range(max_iter):
        mid = 0.5 * (a + b)
        fm = f(mid)
        if fm == 0 or 0.5 * (b - a) < tol:
            return mid
        if fa * fm < 0:
            b, fb = mid, fm
        else:
            a, fa = mid, fm
    return 0.5 * (a + b)


def newton(f, df, x0, tol=1e-12, max_iter=100):
    """Newton-Raphson root finding with derivative ``df``."""
    x = x0
    for _ in range(max_iter):
        step = f(x) / df(x)
        x -= step
        if abs(step) < tol:
            return x
    raise RuntimeError("Newton iteration did not converge")


def central_difference(f, x, h=1e-5):
    r"""Second-order derivative estimate $(f(x+h)-f(x-h))/2h$."""
    return (f(x + h) - f(x - h)) / (2 * h)


def simpson(f, a, b, n=1000):
    """Composite Simpson's rule with ``n`` (even) intervals."""
    if n % 2:
        n += 1
    x = np.linspace(a, b, n + 1)
    y = f(x)
    return (b - a) / (3 * n) * (y[0] + y[-1] + 4 * y[1:-1:2].sum() + 2 * y[2:-1:2].sum())


def monte_carlo_pi(n=1_000_000, seed=0):
    """Estimate $\\pi$ from the fraction of random points inside the unit quarter-circle."""
    pts = np.random.default_rng(seed).random((n, 2))
    return 4 * np.mean((pts**2).sum(axis=1) <= 1)
