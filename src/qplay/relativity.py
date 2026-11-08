r"""Special relativity. Velocities are in m/s unless a function says ``beta``.

Lorentz factor: $\gamma = 1/\sqrt{1-v^2/c^2}$.
"""

from __future__ import annotations

import numpy as np
from scipy.constants import c as C


def gamma(v, c=C):
    return 1 / np.sqrt(1 - (np.asarray(v, float) / c) ** 2)


def time_dilation(proper_time, v, c=C):
    """Dilated time $\\Delta t = \\gamma\\,\\Delta\\tau$."""
    return gamma(v, c) * proper_time


def length_contraction(proper_length, v, c=C):
    """Contracted length $L = L_0/\\gamma$."""
    return proper_length / gamma(v, c)


def add_velocities(u, v, c=C):
    r"""Relativistic velocity addition $(u+v)/(1+uv/c^2)$."""
    return (u + v) / (1 + u * v / c**2)


def doppler_factor(beta):
    r"""Longitudinal Doppler ratio $f_{obs}/f_{src}=\sqrt{(1-\beta)/(1+\beta)}$ (receding for $\beta>0$)."""
    return np.sqrt((1 - beta) / (1 + beta))


def kinetic_energy(mass, v, c=C):
    r"""$(\gamma - 1)mc^2$ in joules.

    Uses $\gamma - 1 = \beta^2\gamma^2/(\gamma + 1)$, which stays accurate at low speed
    where computing $\gamma$ and subtracting 1 would cancel almost every digit.
    """
    g = gamma(v, c)
    beta2 = (np.asarray(v, float) / c) ** 2
    return beta2 * g**2 / (g + 1) * mass * c**2


def lorentz_boost(beta):
    """4x4 boost along +x acting on column vectors ``(ct, x, y, z)``."""
    g = 1 / np.sqrt(1 - beta**2)
    return np.array([[g, -g * beta, 0, 0],
                     [-g * beta, g, 0, 0],
                     [0, 0, 1, 0],
                     [0, 0, 0, 1]])


def interval(event):
    r"""Invariant $s^2 = -(ct)^2 + x^2 + y^2 + z^2$ of an event ``(ct, x, y, z)``."""
    event = np.asarray(event, float)
    return -event[0] ** 2 + event[1] ** 2 + event[2] ** 2 + event[3] ** 2
