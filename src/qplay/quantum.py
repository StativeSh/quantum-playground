r"""Quantum mechanics: Schroedinger solvers, tunnelling, hydrogen, spin-1/2.

Time-independent: $-\frac{\hbar^2}{2m}\psi'' + V\psi = E\psi$.
Time-dependent:   $i\hbar\,\partial_t\psi = \hat H\psi$.
All solvers default to natural units $\hbar = m = 1$.
"""

from __future__ import annotations

from math import factorial

import numpy as np
from scipy import constants
from scipy.linalg import eigh_tridiagonal, expm
from scipy.special import genlaguerre, lpmv

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

    Unitary for real ``V`` and second order in ``dt``. A complex ``V`` (see
    :func:`absorbing_layer`) removes probability at the edges instead of letting it wrap.
    Returns ``(times, psi)`` with ``psi.shape == (n_saved, len(x))``.
    """
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    k = 2 * np.pi * np.fft.fftfreq(len(x), dx)
    Vx = np.asarray(V(x) if callable(V) else V, complex)
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


# ---- hydrogen orbitals ---------------------------------------------------------

def hydrogen_radial(n, l, r, a0=1.0):
    r"""Radial function $R_{nl}(r)$, normalised so that $\int_0^\infty R_{nl}^2 r^2\,dr = 1$.

    $R_{nl} = \sqrt{\left(\tfrac{2}{na_0}\right)^3\tfrac{(n-l-1)!}{2n(n+l)!}}\;e^{-\rho/2}\rho^l
    L^{2l+1}_{n-l-1}(\rho)$ with $\rho = 2r/(na_0)$.
    """
    if not 0 <= l < n:
        raise ValueError("need 0 <= l < n")
    rho = 2 * np.asarray(r, float) / (n * a0)
    norm = np.sqrt((2 / (n * a0)) ** 3 * factorial(n - l - 1) / (2 * n * factorial(n + l)))
    return norm * np.exp(-rho / 2) * rho**l * genlaguerre(n - l - 1, 2 * l + 1)(rho)


def spherical_harmonic(l, m, theta, phi):
    r"""$Y_l^m(\theta, \phi)$ with $\theta$ the polar angle and the Condon-Shortley phase."""
    if abs(m) > l:
        raise ValueError("need |m| <= l")
    am = abs(m)
    norm = np.sqrt((2 * l + 1) / (4 * np.pi) * factorial(l - am) / factorial(l + am))
    y = norm * lpmv(am, l, np.cos(theta)) * np.exp(1j * am * np.asarray(phi, float))
    return (-1) ** am * np.conj(y) if m < 0 else y


def hydrogen_density_xz(n, l, m, extent=None, points=300, a0=1.0):
    r"""$|\psi_{nlm}|^2$ on a square in the $xz$-plane (it is symmetric about the $z$ axis).

    Returns ``(X, Z, density)``; ``extent`` defaults to a size that holds the orbital.
    """
    extent = extent or (2.2 * n**2 + 3) * a0
    s = np.linspace(-extent, extent, points)
    X, Z = np.meshgrid(s, s)
    r = np.hypot(X, Z)
    theta = np.arctan2(np.abs(X), Z)
    density = hydrogen_radial(n, l, r, a0) ** 2 * np.abs(spherical_harmonic(l, m, theta, 0.0)) ** 2
    return X, Z, density


# ---- two dimensions ------------------------------------------------------------

def gaussian_wavepacket_2d(x, y, x0=0.0, y0=0.0, sigma_x=1.0, sigma_y=1.0, kx=0.0, ky=0.0):
    """Normalised 2D Gaussian packet on the grid ``meshgrid(x, y)`` (shape ``(ny, nx)``)."""
    X, Y = np.meshgrid(x, y)
    psi = np.exp(-((X - x0) ** 2) / (4 * sigma_x**2) - ((Y - y0) ** 2) / (4 * sigma_y**2)
                 + 1j * (kx * X + ky * Y))
    return psi / np.sqrt(np.sum(np.abs(psi) ** 2) * (x[1] - x[0]) * (y[1] - y[0]))


def split_step_2d(psi0, x, y, V, dt, steps, m=1.0, hbar=1.0, save_every=None):
    """2D split-step Fourier evolution on a periodic box; arrays are indexed ``[iy, ix]``.

    ``save_every`` defaults to saving only the first and last states.
    Returns ``(times, psi)`` with ``psi.shape == (n_saved, ny, nx)``.
    """
    save_every = save_every or steps
    kx = 2 * np.pi * np.fft.fftfreq(len(x), x[1] - x[0])
    ky = 2 * np.pi * np.fft.fftfreq(len(y), y[1] - y[0])
    KX, KY = np.meshgrid(kx, ky)
    half_potential = np.exp(-0.5j * np.asarray(V, complex) * dt / hbar)
    kinetic = np.exp(-0.5j * hbar * (KX**2 + KY**2) * dt / m)
    psi = np.asarray(psi0, complex).copy()
    times, saved = [0.0], [psi.copy()]
    for s in range(1, steps + 1):
        psi = half_potential * np.fft.ifft2(kinetic * np.fft.fft2(half_potential * psi))
        if s % save_every == 0:
            times.append(s * dt)
            saved.append(psi.copy())
    return np.array(times), np.array(saved)


def absorbing_layer(coords, width, strength=2.0):
    r"""Complex absorbing potential $-iW$ that grows as $W = \eta\,(d/w)^2$ over the last ``width``
    of each edge of a periodic box, so outgoing waves die instead of wrapping around.

    ``coords`` is ``x`` for 1D or ``(x, y)`` for 2D (returned on ``meshgrid(x, y)``).
    Add the result to a real potential before calling a split-step solver.
    """
    def ramp(s):
        s = np.asarray(s, float)
        depth = np.maximum(np.maximum(s.min() + width - s, s - (s.max() - width)), 0.0)
        return strength * (depth / width) ** 2

    if isinstance(coords, tuple):
        Wx, Wy = np.meshgrid(ramp(coords[0]), ramp(coords[1]))
        return -1j * (Wx + Wy)
    return -1j * ramp(coords)


def double_slit_potential(x, y, wall_x=0.0, thickness=1.5, slit_width=1.0, separation=5.0, height=50.0):
    """A wall at ``x = wall_x`` with two slits centred at ``y = +/- separation/2``.

    Keep the wall several grid cells thick and ``height`` moderate (well above the packet
    energy): a one-cell wall of huge height leaks badly in the split-step method.
    """
    X, Y = np.meshgrid(np.asarray(x, float), np.asarray(y, float))
    wall = np.abs(X - wall_x) < thickness / 2
    slits = (np.abs(Y - separation / 2) < slit_width / 2) | (np.abs(Y + separation / 2) < slit_width / 2)
    return np.where(wall & ~slits, height, 0.0)


def double_slit_experiment(n=256, k0=3.0, separation=5.0, slit_width=1.0, screen_x=30.0,
                           dt=0.01, t_max=16.0, save_every=4):
    r"""Run a wavepacket through two slits and record the time-integrated intensity on a screen.

    Far from the slits the fringes follow the two-source condition: dark where the path
    difference is a half-odd number of wavelengths $\lambda = 2\pi/k_0$.
    Returns a dict with ``x, y, times, psi`` (saved frames) and ``screen`` (normalised to max 1).
    """
    x = np.linspace(-20, 60, n, endpoint=False)
    y = np.linspace(-40, 40, n, endpoint=False)
    V = double_slit_potential(x, y, separation=separation, slit_width=slit_width)
    V = V + absorbing_layer((x, y), width=8.0, strength=2.0)
    psi0 = gaussian_wavepacket_2d(x, y, x0=-8.0, sigma_x=2.5, sigma_y=8.0, kx=k0)
    times, psi = split_step_2d(psi0, x, y, V, dt=dt, steps=int(round(t_max / dt)), save_every=save_every)
    ix = np.argmin(np.abs(x - screen_x))
    screen = (np.abs(psi[:, :, ix]) ** 2).sum(axis=0)
    return {"x": x, "y": y, "times": times, "psi": psi, "V": V.real,
            "screen": screen / screen.max(), "screen_x": x[ix]}
