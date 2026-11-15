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


def power_iteration(A, iters=10_000, tol=1e-12, seed=0):
    r"""Dominant eigenpair $(\lambda, \mathbf v)$ by repeated multiplication $\mathbf v \leftarrow A\mathbf v/|A\mathbf v|$.

    The estimate is the Rayleigh quotient $\lambda = \mathbf v^{\mathsf T}A\mathbf v$ (with $|\mathbf v| = 1$).
    It stops when the eigenpair **residual** is small, $|A\mathbf v - \lambda\mathbf v| \le \mathrm{tol}\,\|A\|_F$,
    which checks the vector as well as the value. If $A\mathbf v = 0$ the dominant eigenvalue is
    $0$ and $\mathbf v$ is its eigenvector (from a random start this only happens when every
    eigenvalue is zero). Raises ``ValueError`` for a non-square or non-finite matrix and
    ``RuntimeError`` if it has not converged in ``iters`` steps, which is what happens when no
    single real eigenvalue dominates (a complex pair such as a rotation, or $\lambda$ and $-\lambda$).
    """
    A = np.asarray(A, float)
    if A.ndim != 2 or A.shape[0] != A.shape[1]:
        raise ValueError(f"need a square matrix, got shape {A.shape}")
    if not np.all(np.isfinite(A)):
        raise ValueError("matrix has non-finite entries")
    scale = np.linalg.norm(A)
    v = np.random.default_rng(seed).standard_normal(A.shape[0])
    v /= np.linalg.norm(v)
    if scale == 0:
        return 0.0, v
    for _ in range(iters):
        w = A @ v
        norm = np.linalg.norm(w)
        if norm == 0:
            return 0.0, v
        v = w / norm
        Av = A @ v
        lam = v @ Av
        if np.linalg.norm(Av - lam * v) <= tol * scale:
            return lam, v
    raise RuntimeError(f"power iteration did not converge in {iters} steps; "
                       "the dominant eigenvalue may be complex or not unique in size")


def unit_circle_image(A, n=200):
    """Points ``A @ [cos t, sin t]``, shape ``(2, n)``."""
    t = np.linspace(0, 2 * np.pi, n)
    return np.asarray(A, float) @ np.array([np.cos(t), np.sin(t)])


def singular_axes(A):
    """Semi-axes of the image ellipse: returns ``(sigma, U)`` with axes ``sigma[i] * U[:, i]``."""
    U, sigma, _ = np.linalg.svd(np.asarray(A, float))
    return sigma, U
