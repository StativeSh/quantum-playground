r"""Statistical mechanics: the 2D Ising model.

Energy: $E = -J\sum_{\langle ij\rangle} s_i s_j - h\sum_i s_i$, with $s_i = \pm 1$ on a periodic square lattice.
Metropolis: flip a spin with probability $\min(1, e^{-\Delta E/T})$ (units with $k_B = 1$).
"""

from __future__ import annotations

import numpy as np

T_CRITICAL = 2 / np.log(1 + np.sqrt(2))  # Onsager, for J = 1: about 2.269


def ising_energy(spins, J=1.0, h=0.0):
    """Total energy, counting each nearest-neighbour bond once."""
    s = np.asarray(spins, float)
    bonds = s * np.roll(s, 1, axis=0) + s * np.roll(s, 1, axis=1)
    return -J * bonds.sum() - h * s.sum()


def onsager_magnetization(T, J=1.0):
    r"""Exact spontaneous magnetisation $m = (1 - \sinh^{-4}(2J/T))^{1/8}$ below $T_c$, else 0."""
    T = np.asarray(T, float)
    with np.errstate(divide="ignore", invalid="ignore"):
        m = (1 - np.sinh(2 * J / T) ** -4) ** 0.125
    return np.where(T < T_CRITICAL * J, np.nan_to_num(m), 0.0)


def ising(L=64, T=2.0, sweeps=500, J=1.0, h=0.0, start="cold", seed=None, snapshots=None):
    """Checkerboard Metropolis simulation.

    ``start`` is ``"cold"`` (all up) or ``"hot"`` (random). ``L`` must be even.
    Returns ``(spins, magnetisation_per_site, energy_per_site)``, with one entry per sweep.
    If ``snapshots`` is a list, a copy of the lattice is appended to it after every sweep.
    """
    if L % 2:
        raise ValueError("L must be even for the checkerboard update")
    rng = np.random.default_rng(seed)
    s = np.ones((L, L)) if start == "cold" else rng.choice([-1.0, 1.0], size=(L, L))
    ii, jj = np.indices((L, L))
    colours = [(ii + jj) % 2 == c for c in (0, 1)]
    mags, energies = np.empty(sweeps), np.empty(sweeps)
    for k in range(sweeps):
        for mask in colours:
            nn = np.roll(s, 1, 0) + np.roll(s, -1, 0) + np.roll(s, 1, 1) + np.roll(s, -1, 1)
            dE = 2 * s * (J * nn + h)
            flip = mask & (rng.random((L, L)) < np.exp(-dE / T))
            s[flip] *= -1
        mags[k] = s.mean()
        energies[k] = ising_energy(s, J, h) / L**2
        if snapshots is not None:
            snapshots.append(s.copy())
    return s, mags, energies
