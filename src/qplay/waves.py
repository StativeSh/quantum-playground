r"""Waves, diffusion and Fourier analysis.

Wave equation: $u_{tt} = c^2 u_{xx}$.  Heat equation: $u_t = \alpha u_{xx}$.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import ArrayLike
from scipy import sparse
from scipy.integrate import quad
from scipy.sparse.linalg import splu

__all__ = [
    "wave_1d", "heat_1d", "fourier_coefficients", "fourier_sum", "spectrum", "grating_angle",
    "slit_envelope", "image_distance", "refraction",
    "string_harmonic", "fringe_spacing",
]


def _sample(f, x):
    return np.asarray(f(x) if callable(f) else f, float)


def wave_1d(u0, x, c=1.0, t_max=1.0, v0=None, cfl=0.9):
    """Leapfrog finite differences, fixed ends ($u=0$). Returns ``(t, u)``, ``u.shape == (nt, nx)``."""
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    nt = int(np.ceil(t_max * c / (cfl * dx)))
    dt = t_max / nt
    r2 = (c * dt / dx) ** 2
    u = np.zeros((nt + 1, len(x)))
    u[0] = _sample(u0, x)
    u[0, [0, -1]] = 0.0
    vel = np.zeros_like(x) if v0 is None else _sample(v0, x)
    u[1, 1:-1] = (u[0, 1:-1] + dt * vel[1:-1]
                  + 0.5 * r2 * (u[0, :-2] - 2 * u[0, 1:-1] + u[0, 2:]))
    for n in range(1, nt):
        u[n + 1, 1:-1] = (2 * u[n, 1:-1] - u[n - 1, 1:-1]
                          + r2 * (u[n, :-2] - 2 * u[n, 1:-1] + u[n, 2:]))
    return np.linspace(0, t_max, nt + 1), u


def heat_1d(u0, x, alpha=1.0, t_max=0.1, nt=200):
    """Crank-Nicolson heat equation with $u=0$ at both ends. Returns ``(t, u)``."""
    x = np.asarray(x, float)
    dx = x[1] - x[0]
    dt = t_max / nt
    r = alpha * dt / (2 * dx**2)
    n = len(x) - 2
    ones = np.ones(n - 1)
    lhs = sparse.diags([-r * ones, (1 + 2 * r) * np.ones(n), -r * ones], [-1, 0, 1], format="csc")
    rhs = sparse.diags([r * ones, (1 - 2 * r) * np.ones(n), r * ones], [-1, 0, 1], format="csr")
    lu = splu(lhs)
    u = np.zeros((nt + 1, len(x)))
    u[0] = _sample(u0, x)
    u[0, [0, -1]] = 0.0
    for k in range(nt):
        u[k + 1, 1:-1] = lu.solve(rhs @ u[k, 1:-1])
    return np.linspace(0, t_max, nt + 1), u


def fourier_coefficients(f, period, n_terms, points=None):
    r"""Coefficients of $f(x)=\tfrac{a_0}{2}+\sum_k a_k\cos(k\omega x)+b_k\sin(k\omega x)$.

    ``f`` must accept scalars; ``points`` lists discontinuities in ``[0, period]``.
    Returns ``(a0, a, b)`` with ``a`` and ``b`` of length ``n_terms``.
    """
    w = 2 * np.pi / period

    def integral(g):
        return (2 / period) * quad(g, 0, period, limit=400, points=points)[0]

    a0 = integral(f)
    a = np.array([integral(lambda s, k=k: f(s) * np.cos(k * w * s)) for k in range(1, n_terms + 1)])
    b = np.array([integral(lambda s, k=k: f(s) * np.sin(k * w * s)) for k in range(1, n_terms + 1)])
    return a0, a, b


def fourier_sum(a0, a, b, x, period):
    """Evaluate a truncated Fourier series at ``x``."""
    x = np.asarray(x, float)
    w = 2 * np.pi / period
    y = np.full_like(x, a0 / 2)
    for k, (ak, bk) in enumerate(zip(a, b), start=1):
        y += ak * np.cos(k * w * x) + bk * np.sin(k * w * x)
    return y


def spectrum(signal, dt):
    """One-sided amplitude spectrum. Returns ``(frequencies, amplitudes)``."""
    signal = np.asarray(signal, float)
    amp = np.abs(np.fft.rfft(signal)) / len(signal)
    # Only positive frequencies with a distinct negative partner are doubled.
    paired_end = -1 if len(signal) % 2 == 0 else None
    amp[1:paired_end] *= 2
    return np.fft.rfftfreq(len(signal), dt), amp


def grating_angle(order: int, wavelength: float, spacing: float) -> float | None:
    r"""Principal maximum at normal incidence, $d\sin\theta=m\lambda$; radians or None for absent orders."""
    if min(wavelength, spacing) <= 0:
        raise ValueError("wavelength and spacing must be positive")
    sine = order * wavelength / spacing
    return float(np.arcsin(sine)) if abs(sine) <= 1 else None


def slit_envelope(theta: ArrayLike, width: float, wavelength: float) -> float | np.ndarray:
    r"""Normalised intensity $I/I_0=\mathrm{sinc}^2(\pi w\sin\theta/\lambda)$ at angle in radians."""
    if min(width, wavelength) <= 0:
        raise ValueError("width and wavelength must be positive")
    return np.sinc(width * np.sin(theta) / wavelength)**2


def image_distance(focal_length: float, object_distance: float) -> float:
    r"""Signed image distance in metres, $1/v=1/f-1/u$, for a real object; negative means virtual."""
    if object_distance <= 0 or focal_length == 0:
        raise ValueError("require a positive object distance and nonzero focal length")
    if object_distance == focal_length:
        return np.inf
    return 1 / (1 / focal_length - 1 / object_distance)


def refraction(theta: float, n1: float, n2: float) -> float | None:
    r"""Angle from the normal, $n_1\sin\theta_1=n_2\sin\theta_2$, or None for total internal reflection."""
    if min(n1, n2) <= 0 or abs(theta) > np.pi / 2:
        raise ValueError("require positive indices and an angle of incidence between -pi/2 and pi/2")
    sine = n1 * np.sin(theta) / n2
    return float(np.arcsin(sine)) if abs(sine) <= 1 else None


def string_harmonic(n: int, length: float, tension: float, linear_density: float) -> float:
    r"""Frequency in Hz of mode $f_n=n\sqrt{T/\mu}/(2L)$ on a uniform fixed-end string.

    Supply length in m, tension in N and mass per unit length in kg/m.
    """
    if not isinstance(n, (int, np.integer)) or n < 1 or min(length, tension, linear_density) <= 0:
        raise ValueError("use a positive integer harmonic and positive string parameters")
    return float(n * np.sqrt(tension / linear_density) / (2 * length))


def fringe_spacing(wavelength: float, distance: float, separation: float) -> float:
    r"""Paraxial double-slit fringe spacing $\Delta y=\lambda L/d$ (all lengths in m)."""
    if min(wavelength, distance, separation) <= 0:
        raise ValueError("lengths must be positive")
    return wavelength * distance / separation
