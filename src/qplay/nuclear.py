r"""Radioactive decay: single nuclides, decay chains and Monte Carlo decay.

Single nuclide: $\dfrac{dN}{dt} = -\lambda N \Rightarrow N = N_0 e^{-\lambda t}$, with
$t_{1/2} = \ln 2/\lambda$ and activity $A = \lambda N$.

Chain $1 \to 2 \to \dots \to k$: $\dfrac{dN_i}{dt} = \lambda_{i-1}N_{i-1} - \lambda_i N_i$. Starting
from pure parent, the Bateman solution is

$$N_k(t) = N_0\left(\prod_{i=1}^{k-1}\lambda_i\right)\sum_{i=1}^{k}
\frac{e^{-\lambda_i t}}{\prod_{j\ne i}(\lambda_j - \lambda_i)} .$$
"""

from __future__ import annotations

import numpy as np
from scipy.linalg import expm


def decay_constant(half_life):
    r"""$\lambda = \ln 2 / t_{1/2}$."""
    return np.log(2) / np.asarray(half_life, float)


def half_life(decay_const):
    r"""$t_{1/2} = \ln 2 / \lambda$."""
    return np.log(2) / np.asarray(decay_const, float)


def remaining(N0, lam, t):
    r"""$N = N_0 e^{-\lambda t}$."""
    return N0 * np.exp(-lam * np.asarray(t, float))


def bateman(N0, lambdas, t):
    r"""Bateman solution for a chain that starts as ``N0`` parent nuclei and nothing else.

    ``lambdas`` are the decay constants in order; use 0 for a stable end product. They must be
    distinct (use :func:`decay_chain` otherwise). Returns ``N`` of shape ``(len(t), len(lambdas))``.
    """
    lam = np.asarray(lambdas, float)
    if len(np.unique(lam)) != len(lam):
        raise ValueError("Bateman's formula needs distinct decay constants; use decay_chain")
    t = np.atleast_1d(np.asarray(t, float))
    N = np.zeros((len(t), len(lam)))
    for k in range(len(lam)):
        prefactor = N0 * np.prod(lam[:k])
        for i in range(k + 1):
            denom = np.prod([lam[j] - lam[i] for j in range(k + 1) if j != i])
            N[:, k] += prefactor * np.exp(-lam[i] * t) / denom
    return N


def decay_chain(N0, lambdas, t):
    r"""Any chain, by the matrix exponential $\mathbf N(t) = e^{Mt}\mathbf N_0$.

    ``N0`` is a vector of initial amounts (or a number, meaning pure parent). Works with
    repeated decay constants. Returns shape ``(len(t), len(lambdas))``.
    """
    lam = np.asarray(lambdas, float)
    n0 = np.zeros(len(lam))
    if np.ndim(N0) == 0:
        n0[0] = N0
    else:
        n0[:] = N0
    M = np.diag(-lam) + np.diag(lam[:-1], -1)
    return np.array([expm(M * ti) @ n0 for ti in np.atleast_1d(np.asarray(t, float))])


def simulate_decay(N0, lam, t, trials=1, seed=None):
    r"""Monte Carlo decay: in each step of length $\Delta t$ every nucleus decays with probability
    $1 - e^{-\lambda\Delta t}$. Returns integer counts of shape ``(trials, len(t))``.
    """
    rng = np.random.default_rng(seed)
    t = np.asarray(t, float)
    N = np.empty((trials, len(t)), dtype=np.int64)
    N[:, 0] = N0
    for k in range(1, len(t)):
        p = 1 - np.exp(-lam * (t[k] - t[k - 1]))
        N[:, k] = N[:, k - 1] - rng.binomial(N[:, k - 1], p)
    return N
