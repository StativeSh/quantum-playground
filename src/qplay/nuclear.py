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
from numpy.typing import ArrayLike, NDArray
from scipy.sparse.linalg import expm_multiply

__all__ = [
    "decay_constant", "half_life", "remaining", "bateman", "decay_chain", "simulate_decay",
    "binding_energy_per_nucleon",
    "reaction_energy",
]


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
    N = np.empty((len(t), len(lam)))
    for k in range(len(lam)):
        rates = lam[:k + 1]
        weights = np.empty(k + 1)
        for i, rate in enumerate(rates):
            gaps = rates[rates != rate] - rate
            with np.errstate(over="ignore", invalid="ignore"):
                weights[i] = np.prod(lam[:k] / gaps)
        # For nonnegative times and rates, sum(abs(weights)) bounds the
        # amplification of rounding errors relative to the initial population.
        # Switch evaluators before losing more than about three decimal digits.
        if not np.all(np.isfinite(weights)) or np.sum(np.abs(weights)) > 1000:
            return decay_chain(N0, lam, t)
        N[:, k] = N0 * (np.exp(-t[:, None] * rates) @ weights)
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
    times = np.atleast_1d(np.asarray(t, float))
    return np.array([expm_multiply(M * ti, n0) for ti in times]).reshape(len(times), len(lam))


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


def binding_energy_per_nucleon(A: ArrayLike, Z: ArrayLike) -> float | NDArray[np.float64]:
    r"""Liquid-drop estimate in MeV per nucleon, not a mass-table measurement.

    $B=a_v A-a_s A^{2/3}-a_c Z(Z-1)/A^{1/3}-a_a(A-2Z)^2/A+\delta$.
    Pairing is positive for even-even nuclei, negative for odd-odd and zero for odd A.
    The semi-empirical fit is most useful for medium and heavy nuclei.

    ``A`` and ``Z`` are integers or integer arrays that broadcast together, so a whole
    curve can be computed at once. Scalar inputs return a float.
    """
    A, Z = np.asarray(A), np.asarray(Z)
    if not (np.issubdtype(A.dtype, np.integer) and np.issubdtype(Z.dtype, np.integer)) \
            or np.any((Z <= 0) | (Z >= A)):
        raise ValueError("require integer mass and proton numbers with 0 < Z < A")
    a, z = A.astype(float), Z.astype(float)
    pairing = np.where(A % 2 == 1, 0.0, np.where(Z % 2 == 1, -12.0, 12.0) / np.sqrt(a))
    energy = (15.75*a - 17.8*a**(2/3) - 0.711*z*(z-1)/a**(1/3)
              - 23.7*(a-2*z)**2/a + pairing) / a
    return float(energy) if energy.ndim == 0 else energy


def reaction_energy(reactant_binding_energies: ArrayLike, product_binding_energies: ArrayLike) -> float:
    r"""Released energy $Q=\sum B_{\rm products}-\sum B_{\rm reactants}$ in MeV.

    Supply total binding energies in MeV, one entry per nucleus, for a
    nucleon-conserving reaction. A negative result means energy is required.
    """
    return float(np.sum(product_binding_energies, dtype=float) - np.sum(reactant_binding_energies, dtype=float))
