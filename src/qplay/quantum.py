r"""Quantum mechanics: Schroedinger solvers, tunnelling, hydrogen, spin-1/2.

Time-independent: $-\frac{\hbar^2}{2m}\psi'' + V\psi = E\psi$.
Time-dependent:   $i\hbar\,\partial_t\psi = \hat H\psi$.
All solvers default to natural units $\hbar = m = 1$.
"""

from __future__ import annotations

import numpy as np
from scipy import constants
from scipy.linalg import eigh_tridiagonal, expm

# ---- particle in a box ---------------------------------------------------------

def infinite_well_energy(n, L=1.0, m=1.0, hbar=1.0):
    r"""$E_n = n^2\pi^2\hbar^2 / (2 m L^2)$."""
    return (np.asarray(n) * np.pi * hbar / L) ** 2 / (2 * m)


def infinite_well_state(n, x, L=1.0):
    r"""$\psi_n(x) = \sqrt{2/L}\sin(n\pi x/L)$ on $[0, L]$."""
    return np.sqrt(2 / L) * np.sin(n * np.pi * np.asarray(x) / L)


# ---- numerical solvers ---------------------------------------------------------

def solve_tise(V, x, n_states=6, m=1.0, hbar=1.0):
    """Lowest eigenstates of an arbitrary 1D potential by finite differences.

    ``V`` is a callable or an array on the uniform grid ``x``. The wavefunction is
    taken to vanish just outside the grid. Returns ``(E, psi)`` with
    ``psi.shape == (n_states, len(x))`` and $\\int|\\psi|^2 dx = 1$.
    """
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    Vx = np.asarray(V(x) if callable(V) else V, float)
    t = hbar**2 / (2 * m * dx**2)
    E, psi = eigh_tridiagonal(2 * t + Vx, -t * np.ones(len(x) - 1),
                              select="i", select_range=(0, n_states - 1))
    return E, psi.T / np.sqrt(dx)


def gaussian_wavepacket(x, x0=0.0, sigma=1.0, k0=0.0):
    r"""Normalised packet $\psi\propto e^{-(x-x_0)^2/4\sigma^2}e^{ik_0x}$ ($|\psi|^2$ has std $\sigma$)."""
    x = np.asarray(x, float)
    psi = np.exp(-((x - x0) ** 2) / (4 * sigma**2) + 1j * k0 * x)
    return psi / np.sqrt(np.sum(np.abs(psi) ** 2) * (x[1] - x[0]))


def split_step(psi0, x, V, dt, steps, m=1.0, hbar=1.0, save_every=1):
    """Time evolution by the Strang split-step Fourier method (periodic box).

    Unitary and second order in ``dt``. Returns ``(times, psi)`` with
    ``psi.shape == (n_saved, len(x))``.
    """
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    k = 2 * np.pi * np.fft.fftfreq(len(x), dx)
    Vx = np.asarray(V(x) if callable(V) else V, float)
    half_potential = np.exp(-0.5j * Vx * dt / hbar)
    kinetic = np.exp(-0.5j * hbar * k**2 * dt / m)
    psi = np.asarray(psi0, complex).copy()
    times, saved = [0.0], [psi.copy()]
    for s in range(1, steps + 1):
        psi = half_potential * np.fft.ifft(kinetic * np.fft.fft(half_potential * psi))
        if s % save_every == 0:
            times.append(s * dt)
            saved.append(psi.copy())
    return np.array(times), np.array(saved)


def probability_density(psi):
    return np.abs(psi) ** 2


def expectation(operator_values, psi, x):
    """$\\langle A\\rangle$ for a function ``A(x)`` sampled on the grid."""
    dx = x[1] - x[0]
    return np.real(np.sum(np.conj(psi) * operator_values * psi) * dx)


def barrier_transmission(E, V0, a, m=1.0, hbar=1.0):
    r"""Exact transmission through a rectangular barrier of height $V_0$ and width $a$."""
    scalar = np.ndim(E) == 0
    E = np.atleast_1d(np.asarray(E, float))
    T = np.empty_like(E)
    below, above = E < V0, E > V0
    equal = ~(below | above)
    Eb, Ea = E[below], E[above]
    kappa = np.sqrt(2 * m * (V0 - Eb)) / hbar
    T[below] = 1 / (1 + V0**2 * np.sinh(kappa * a) ** 2 / (4 * Eb * (V0 - Eb)))
    k2 = np.sqrt(2 * m * (Ea - V0)) / hbar
    T[above] = 1 / (1 + V0**2 * np.sin(k2 * a) ** 2 / (4 * Ea * (Ea - V0)))
    T[equal] = 1 / (1 + m * V0 * a**2 / (2 * hbar**2))
    return float(T[0]) if scalar else T


# ---- hydrogen ------------------------------------------------------------------

_RYDBERG_EV = constants.physical_constants["Rydberg constant times hc in eV"][0]


def hydrogen_energy_eV(n):
    r"""$E_n = -13.6\,\mathrm{eV}/n^2$."""
    return -_RYDBERG_EV / np.asarray(n, float) ** 2


def hydrogen_wavelength_nm(n_upper, n_lower):
    r"""Photon wavelength (vacuum) for the transition $n_u \to n_l$ via the Rydberg formula."""
    inv = constants.Rydberg * (1 / np.asarray(n_lower, float) ** 2 - 1 / np.asarray(n_upper, float) ** 2)
    return 1e9 / inv


# ---- spin-1/2 ------------------------------------------------------------------

SIGMA_X = np.array([[0, 1], [1, 0]], dtype=complex)
SIGMA_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
SIGMA_Z = np.array([[1, 0], [0, -1]], dtype=complex)
PAULI = (SIGMA_X, SIGMA_Y, SIGMA_Z)


def evolve(H, psi0, t, hbar=1.0):
    r"""Exact $|\psi(t)\rangle = e^{-iHt/\hbar}|\psi_0\rangle$ for a matrix Hamiltonian."""
    return expm(-1j * np.asarray(H) * t / hbar) @ np.asarray(psi0, complex)


def bloch_vector(psi):
    """Bloch-sphere vector ``(<sx>, <sy>, <sz>)`` of a normalised qubit state."""
    psi = np.asarray(psi, complex)
    return np.array([np.real(np.conj(psi) @ s @ psi) for s in PAULI])
