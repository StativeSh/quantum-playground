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
    r"""Dominant eigenpair $(\lambda, \mathbf v)$ by repeated multiplication $\mathbf v \leftarrow A\mathbf v/|A\mathbf v|$."""
    A = np.asarray(A, float)
    v = np.random.default_rng(seed).standard_normal(A.shape[0])
    v /= np.linalg.norm(v)
    lam = 0.0
    for _ in range(iters):
        w = A @ v
        v_new = w / np.linalg.norm(w)
        lam_new = v_new @ A @ v_new
        if abs(lam_new - lam) < tol:
            return lam_new, v_new
        v, lam = v_new, lam_new
    return lam, v


def unit_circle_image(A, n=200):
    """Points ``A @ [cos t, sin t]``, shape ``(2, n)``."""
    t = np.linspace(0, 2 * np.pi, n)
    return np.asarray(A, float) @ np.array([np.cos(t), np.sin(t)])


def singular_axes(A):
    """Semi-axes of the image ellipse: returns ``(sigma, U)`` with axes ``sigma[i] * U[:, i]``."""
    U, sigma, _ = np.linalg.svd(np.asarray(A, float))
    return sigma, U
