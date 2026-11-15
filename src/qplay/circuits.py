r"""Electric circuits: capacitor charge and discharge, and the series RLC circuit.

Series RLC with source $V(t)$ (charge $q$ on the capacitor, current $I = \dot q$):

$$L\ddot q + R\dot q + \frac{q}{C} = V(t).$$

With $L = 0$ this is the RC circuit, time constant $\tau = RC$. The undamped resonant angular
frequency is $\omega_0 = 1/\sqrt{LC}$, the quality factor $Q = \frac1R\sqrt{L/C}$, and for a drive
$V_0\cos\omega t$ the steady current amplitude is $V_0/|Z|$ with
$Z = R + i\left(\omega L - \frac{1}{\omega C}\right)$.
"""

from __future__ import annotations

import numpy as np

from .integrators import solve


def _source(V):
    return V if callable(V) else (lambda t, V=float(V): V)


def rc_discharge(t, V0, R, C):
    r"""Capacitor voltage while discharging: $V = V_0 e^{-t/RC}$."""
    return V0 * np.exp(-np.asarray(t, float) / (R * C))


def rc_charge(t, V0, R, C):
    r"""Capacitor voltage while charging from a supply $V_0$: $V = V_0(1 - e^{-t/RC})$."""
    return V0 * -np.expm1(-np.asarray(t, float) / (R * C))


def rc_circuit(R, C, V=0.0, q0=0.0, t_max=1.0, n=500):
    r"""Integrate $R\dot q + q/C = V(t)$. ``V`` is a number or a function of $t$.

    Returns ``(t, q, I)``.
    """
    src = _source(V)
    t, y = solve(lambda t, q: [(src(t) - q[0] / C) / R], [q0], (0, t_max), n)
    q = y[:, 0]
    return t, q, (np.array([src(ti) for ti in t]) - q / C) / R


def rlc_series(R, L, C, V=0.0, q0=0.0, i0=0.0, t_max=1.0, n=1000):
    r"""Integrate $L\ddot q + R\dot q + q/C = V(t)$. Returns ``(t, q, I)``."""
    src = _source(V)

    def rhs(t, y):
        q, i = y
        return [i, (src(t) - R * i - q / C) / L]

    t, y = solve(rhs, [q0, i0], (0, t_max), n)
    return t, y[:, 0], y[:, 1]


def resonant_frequency(L, C):
    r"""$\omega_0 = 1/\sqrt{LC}$ in rad/s."""
    return 1 / np.sqrt(L * C)


def quality_factor(R, L, C):
    r"""$Q = \dfrac{1}{R}\sqrt{\dfrac{L}{C}}$; the resonance full width at half power is $\omega_0/Q = R/L$."""
    return np.sqrt(L / C) / R


def impedance(omega, R, L, C):
    r"""Complex impedance $Z = R + i(\omega L - 1/\omega C)$ of the series circuit."""
    omega = np.asarray(omega, float)
    return R + 1j * (omega * L - 1 / (omega * C))


def current_amplitude(omega, V0, R, L, C):
    r"""Steady-state current amplitude $I_0 = V_0/|Z|$ for a drive $V_0\cos\omega t$."""
    return V0 / np.abs(impedance(omega, R, L, C))
