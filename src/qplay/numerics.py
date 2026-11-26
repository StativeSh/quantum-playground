"""Basic numerical methods written out in full, for learning."""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike

__all__ = [
    "bisect", "newton", "central_difference", "simpson", "monte_carlo_pi",
    "fit_line",
]


def bisect(f, a, b, tol=1e-12, max_iter=200):
    r"""Root of ``f`` in ``[a, b]`` by bisection.

    ``f(a)`` and ``f(b)`` must have opposite signs, or one of them must be exactly zero, in
    which case that endpoint is returned. Each step halves the bracket, keeping the half where
    the sign changes, so after $k$ steps the root is known to within $(b - a)/2^{k+1}$.
    Signs are compared directly rather than by multiplying values, which could underflow to
    zero for very small $f$. Raises ``ValueError`` for a bad bracket or a non-finite value of
    ``f``, and ``RuntimeError`` if ``max_iter`` steps do not reach ``tol``.
    """
    if not a < b:
        a, b = b, a
    fa, fb = _finite(f, a), _finite(f, b)
    if fa == 0:
        return a
    if fb == 0:
        return b
    if np.sign(fa) == np.sign(fb):
        raise ValueError("f(a) and f(b) must have opposite signs")
    for _ in range(max_iter):
        mid = 0.5 * (a + b)
        if 0.5 * (b - a) < tol or mid in (a, b):  # converged, or no float left between a and b
            return mid
        fm = _finite(f, mid)
        if fm == 0:
            return mid
        if np.sign(fm) == np.sign(fa):
            a, fa = mid, fm
        else:
            b = mid
    raise RuntimeError(f"bisection did not reach tol={tol} in {max_iter} steps (bracket now [{a}, {b}])")


def _finite(f, x):
    value = f(x)
    if not np.isfinite(value):
        raise ValueError(f"f({x}) = {value} is not finite")
    return value


def newton(f, df, x0, tol=1e-12, max_iter=100):
    r"""Newton-Raphson root finding, $x \leftarrow x - f(x)/f'(x)$, with derivative ``df``.

    Raises ``ZeroDivisionError`` if $f'(x) = 0$ at some step, ``ValueError`` if the iterate
    stops being finite, and ``RuntimeError`` if it has not converged after ``max_iter`` steps.
    """
    x = x0
    for _ in range(max_iter):
        slope = df(x)
        if slope == 0:
            raise ZeroDivisionError(f"f'(x) = 0 at x = {x}: Newton's method cannot continue")
        step = f(x) / slope
        x -= step
        if not np.isfinite(x):
            raise ValueError("Newton iteration diverged to a non-finite value")
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


def fit_line(x: ArrayLike, y: ArrayLike, *, through_origin: bool = False) -> dict[str, float | None]:
    r"""Fit $y=mx+b$ to paired observations by unweighted ordinary least squares.

    Return gradient, intercept, gradientSE and interceptSE. For an unconstrained
    fit, $S_{xx}=\sum(x_i-\bar x)^2$ and $s^2=\sum r_i^2/(n-2)$, giving
    $SE_m=s/\sqrt{S_{xx}}$ and $SE_b=s\sqrt{1/n+\bar x^2/S_{xx}}$.
    Two points determine the line but give no error estimate (None).
    With through_origin, fix the intercept at zero, use uncentred sums and
    divide the residual sum of squares by $n-1$.
    """
    xs, ys = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if xs.ndim != 1 or ys.shape != xs.shape or xs.size < 2:
        raise ValueError("expected at least two paired one-dimensional observations")
    if not np.all(np.isfinite(xs)) or not np.all(np.isfinite(ys)):
        raise ValueError("observations must be finite")
    x_mean = 0.0 if through_origin else xs.mean()
    y_mean = 0.0 if through_origin else ys.mean()
    dx, dy = xs - x_mean, ys - y_mean
    sxx = dx @ dx
    if sxx == 0:
        raise ValueError("the gradient is undetermined")
    gradient = float((dx @ dy) / sxx)
    intercept = float(y_mean - gradient*x_mean)
    degrees = xs.size - (1 if through_origin else 2)
    gradient_se = intercept_se = None
    if degrees:
        residuals = dy - gradient*dx
        variance = (residuals @ residuals) / degrees
        gradient_se = float(np.sqrt(variance / sxx))
        intercept_se = 0.0 if through_origin else float(np.sqrt(variance * (1/xs.size + x_mean**2/sxx)))
    return dict(gradient=gradient, intercept=intercept, gradientSE=gradient_se, interceptSE=intercept_se)
