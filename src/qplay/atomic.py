r"""Atomic structure: angular momentum matrices, spin-orbit coupling, the Zeeman effect and
hydrogen fine structure.

For one electron with orbital angular momentum $l$ and spin $s = \tfrac12$ in a magnetic field
$B$ along $z$ (energies in units where $\hbar = 1$):

$$H = \xi\,\mathbf L\cdot\mathbf S + \mu_B B\,(L_z + g_s S_z).$$

At $B = 0$ the levels are labelled by $j = l\pm\tfrac12$ with
$E = \tfrac{\xi}{2}\,[\,j(j+1) - l(l+1) - \tfrac34\,]$. A weak field splits each into
$E = g_J m_j \mu_B B$ with the Landé factor $g_J$; a strong field gives the Paschen-Back limit
$E \to \mu_B B\,(m_l + g_s m_s)$.

Hydrogen fine structure (Dirac, to order $\alpha^2$):
$$E_{nj} = -\frac{R_\infty hc}{n^2}\left[1 + \frac{\alpha^2}{n^2}\left(\frac{n}{j+\tfrac12} - \frac34\right)\right].$$
"""

from __future__ import annotations

import numpy as np
from scipy import constants

__all__ = [
    "ALPHA", "RYDBERG_EV", "MU_B_EV_PER_T", "ELECTRON_G", "angular_momentum", "basis_labels",
    "spin_orbit_zeeman_hamiltonian", "zeeman_levels", "lande_g", "spin_orbit_energy",
    "hydrogen_fine_structure_eV", "dirac_energy_eV",
]

ALPHA = constants.alpha
RYDBERG_EV = constants.physical_constants["Rydberg constant times hc in eV"][0]
MU_B_EV_PER_T = constants.physical_constants["Bohr magneton in eV/T"][0]
ELECTRON_G = -constants.physical_constants["electron g factor"][0]   # about 2.0023


def angular_momentum(j):
    r"""Matrices ``(Jx, Jy, Jz)`` for spin ``j`` in the basis $m = j, j-1, \dots, -j$ ($\hbar = 1$).

    Built from $J_\pm|j,m\rangle = \sqrt{j(j+1) - m(m\pm1)}\,|j,m\pm1\rangle$.
    """
    m = np.arange(j, -j - 1, -1)
    jp = np.diag(np.sqrt(j * (j + 1) - m[1:] * (m[1:] + 1)), 1).astype(complex)  # raising
    jm = jp.conj().T
    return (jp + jm) / 2, (jp - jm) / 2j, np.diag(m).astype(complex)


def basis_labels(l, s=0.5):
    r"""``(m_l, m_s)`` for each basis vector of :func:`spin_orbit_zeeman_hamiltonian`."""
    return [(ml, ms) for ml in np.arange(l, -l - 1, -1) for ms in np.arange(s, -s - 1, -1)]


def spin_orbit_zeeman_hamiltonian(l, xi, B, mu_b=1.0, gs=2.0, s=0.5):
    r"""$H = \xi\,\mathbf L\cdot\mathbf S + \mu_B B\,(L_z + g_s S_z)$ in the $|m_l, m_s\rangle$ basis.

    ``xi`` and ``mu_b * B`` share whatever energy unit you choose.
    """
    Lx, Ly, Lz = angular_momentum(l)
    Sx, Sy, Sz = angular_momentum(s)
    il, is_ = np.eye(Lz.shape[0]), np.eye(Sz.shape[0])
    LS = sum(np.kron(a, b) for a, b in ((Lx, Sx), (Ly, Sy), (Lz, Sz)))
    return xi * LS + mu_b * B * (np.kron(Lz, is_) + gs * np.kron(il, Sz))


def zeeman_levels(l, xi, B_values, mu_b=1.0, gs=2.0):
    """Sorted energy levels for each field in ``B_values``; shape ``(len(B_values), 2(2l+1))``."""
    return np.array([np.linalg.eigvalsh(spin_orbit_zeeman_hamiltonian(l, xi, B, mu_b, gs))
                     for B in np.atleast_1d(B_values)])


def lande_g(l, j, s=0.5, gs=2.0):
    r"""$g_J = 1 + (g_s - 1)\,\dfrac{j(j+1) + s(s+1) - l(l+1)}{2j(j+1)}$."""
    return 1 + (gs - 1) * (j * (j + 1) + s * (s + 1) - l * (l + 1)) / (2 * j * (j + 1))


def spin_orbit_energy(l, j, xi, s=0.5):
    r"""$\tfrac{\xi}{2}\,[\,j(j+1) - l(l+1) - s(s+1)\,]$, the eigenvalue of $\xi\,\mathbf L\cdot\mathbf S$."""
    return xi / 2 * (j * (j + 1) - l * (l + 1) - s * (s + 1))


def hydrogen_fine_structure_eV(n, j):
    r"""Hydrogen level $E_{nj}$ in eV including fine structure to order $\alpha^2$ (see module docstring)."""
    return -RYDBERG_EV / n**2 * (1 + ALPHA**2 / n**2 * (n / (j + 0.5) - 0.75))


def dirac_energy_eV(n, j):
    r"""Exact Dirac energy minus $m_ec^2$:
    $E = m_ec^2\left[\left(1 + \dfrac{\alpha^2}{(n - \delta)^2}\right)^{-1/2} - 1\right]$,
    $\delta = j + \tfrac12 - \sqrt{(j+\tfrac12)^2 - \alpha^2}$."""
    mc2 = constants.physical_constants["electron mass energy equivalent in MeV"][0] * 1e6
    k = j + 0.5
    delta = k - np.sqrt(k**2 - ALPHA**2)
    x = (ALPHA / (n - delta)) ** 2
    return mc2 * (1 / np.sqrt(1 + x) - 1)
