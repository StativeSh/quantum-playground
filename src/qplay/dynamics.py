r"""Phase planes for autonomous 2D systems $\dot{\mathbf x} = \mathbf f(\mathbf x)$.

Near a fixed point the linearisation $\dot{\boldsymbol\delta} = J\boldsymbol\delta$ decides its type
through $\tau = \operatorname{tr}J$ and $\Delta = \det J$: saddle if $\Delta<0$, spiral if
$\tau^2 < 4\Delta$, node otherwise, stable if $\tau < 0$.

Convention: ``f(state)`` takes ``state = [x, y]`` (scalars or arrays) and returns ``[dx, dy]``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import root


def jacobian(f, x, h=1e-6):
    """Central-difference Jacobian of ``f`` at ``x``."""
    x = np.asarray(x, float)
    J = np.empty((len(x), len(x)))
    for j in range(len(x)):
        e = np.zeros_like(x)
        e[j] = h
        J[:, j] = (np.asarray(f(x + e), float) - np.asarray(f(x - e), float)) / (2 * h)
    return J


def classify_fixed_point(J, tol=1e-7):
    """Type of a 2D fixed point from its Jacobian.

    A ``"center"`` is only a center of the linearisation: nonlinear terms decide the real system.
    """
    tau, delta = np.trace(J), np.linalg.det(J)
    if abs(delta) < tol:
        return "degenerate"
    if delta < 0:
        return "saddle"
    if abs(tau) < tol:
        return "center"
    kind = "spiral" if tau**2 < 4 * delta else "node"
    return f"{'stable' if tau < 0 else 'unstable'} {kind}"


def fixed_points(f, guesses, tol=1e-9):
    """Distinct fixed points found by root-finding from each guess."""
    found = []
    for g in guesses:
        sol = root(lambda x: np.asarray(f(x), float), np.asarray(g, float), tol=1e-12)
        if sol.success and np.linalg.norm(f(sol.x)) < tol:
            if not any(np.allclose(sol.x, p, atol=1e-6) for p in found):
                found.append(sol.x)
    return np.array(found)


def phase_portrait(f, xlim, ylim, ax=None, n=30, density=1.2, classify=None, **stream_kw):
    """Streamlines of ``f`` plus labelled fixed points.

    ``classify`` is a list of guesses for :func:`fixed_points`. Returns the axes.
    """
    ax = ax or plt.gca()
    X, Y = np.meshgrid(np.linspace(*xlim, n), np.linspace(*ylim, n))
    U, V = f(np.array([X, Y]))
    speed = np.hypot(U, V)
    ax.streamplot(X, Y, U, V, color=np.log1p(speed), cmap="viridis", density=density,
                  linewidth=0.8, **stream_kw)
    for p in fixed_points(f, classify or []):
        kind = classify_fixed_point(jacobian(f, p))
        ax.plot(*p, "o", ms=7, mfc="w" if "unstable" in kind or kind == "saddle" else "k", mec="k")
        ax.annotate(kind, p, textcoords="offset points", xytext=(6, 6), fontsize=8)
    ax.set(xlim=xlim, ylim=ylim)
    return ax
