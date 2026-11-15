r"""Linear algebra written out for learning (use ``numpy.linalg`` for real work).

A matrix $A$ maps the unit circle to an ellipse whose semi-axes are $\sigma_i \mathbf u_i$,
from the singular value decomposition $A = U\Sigma V^{\mathsf T}$.
"""

from __future__ import annotations

import numpy as np


def rotation(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def shear(k):
    return np.array([[1.0, k], [0.0, 1.0]])


def gram_schmidt(vectors, tol=1e-12):
    """Orthonormal basis (as rows) for the span of the given row vectors (modified Gram-Schmidt)."""
    basis = []
    for v in np.asarray(vectors, float):
        w = v.copy()
        for b in basis:
            w -= (w @ b) * b
        norm = np.linalg.norm(w)
        if norm > tol:
            basis.append(w / norm)
    return np.array(basis)


def power_iteration(A, iters=10_000, tol=1e-12, seed=0, v0=None, restarts=3):
    r"""Dominant eigenpair $(\lambda, \mathbf v)$ by repeated multiplication $\mathbf v \leftarrow A\mathbf v/|A\mathbf v|$.

    The estimate is the Rayleigh quotient $\lambda = \mathbf v^{\mathsf T}A\mathbf v$ (with $|\mathbf v| = 1$).
    It stops when the eigenpair **residual** is small, $|A\mathbf v - \lambda\mathbf v| \le \mathrm{tol}\,\|A\|_F$,
    which checks the vector as well as the value.

    Details that matter numerically:

    - $A$ is divided by its largest entry before iterating (and $\lambda$ multiplied back), so
      norms neither underflow nor overflow for very small or very large matrices.
    - An exactly zero matrix returns $\lambda = 0$.
    - If $A\mathbf v$ is exactly zero, $\mathbf v$ lies in the null space of $A$. That makes
      $(0, \mathbf v)$ *an* eigenpair but says nothing about which eigenvalue dominates
      (e.g. $A = \mathrm{diag}(1, 0)$ with $\mathbf v = (0, 1)$), so the iteration restarts from a
      fresh random vector, up to ``restarts`` times, then raises ``RuntimeError`` ("breakdown").
      A nilpotent matrix breaks down on every start and so raises.
    - Raises ``RuntimeError`` if the residual test is not met within ``iters`` steps. That is
      typical when no single real eigenvalue dominates (a complex pair such as a rotation; or
      $\lambda$ and $-\lambda$, where only special starting vectors converge).

    ``v0`` is the starting vector (random from ``seed`` if omitted). Raises ``ValueError`` for a
    non-square or non-finite matrix.
    """
    A = np.asarray(A, float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"need a square matrix, got shape {A.shape}")
    if not np.all(np.isfinite(A)):
        raise ValueError("matrix has non-finite entries")
    rng = np.random.default_rng(seed)
    n = A.shape[0]
    if not A.any():
        return 0.0, _unit(rng.standard_normal(n))
    s = np.abs(A).max()
    B = A / s                                    # largest entry 1: safe norms
    scale = np.linalg.norm(B)
    v = _unit(np.asarray(v0, float) if v0 is not None else rng.standard_normal(n))
    breakdowns = 0
    for _ in range(iters):
        Bv = B @ v
        if not Bv.any():
            # v is in the null space: (0, v) is an eigenpair, but not necessarily the dominant
            # one, so never accept it as converged. Start again from a fresh random vector.
            breakdowns += 1
            if breakdowns > restarts:
                raise RuntimeError(f"breakdown: the iterate fell into the null space of A {breakdowns} times "
                                   "(A v = 0); the dominant eigenpair could not be found")
            v = _unit(rng.standard_normal(n))
            continue
        lam = v @ Bv
        if np.linalg.norm(Bv - lam * v) <= tol * scale:
            return s * lam, v
        v = _unit(Bv)
    raise RuntimeError(f"power iteration did not converge in {iters} steps; "
                       "the dominant eigenvalue may be complex or not unique in size")


def _unit(x):
    norm = np.linalg.norm(x)
    if norm == 0:
        raise ValueError("starting vector is zero")
    return x / norm


def unit_circle_image(A, n=200):
    """Points ``A @ [cos t, sin t]``, shape ``(2, n)``."""
    t = np.linspace(0, 2 * np.pi, n)
    return np.asarray(A, float) @ np.array([np.cos(t), np.sin(t)])


def singular_axes(A):
    """Semi-axes of the image ellipse: returns ``(sigma, U)`` with axes ``sigma[i] * U[:, i]``."""
    U, sigma, _ = np.linalg.svd(np.asarray(A, float))
    return sigma, U
