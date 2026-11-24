r"""Classical mechanics: oscillators, pendulums, projectiles, gravity.

Pendulum:  $\ddot\theta = -\frac{g}{L}\sin\theta$
"""

from __future__ import annotations

import warnings

import numpy as np
from numpy.typing import ArrayLike
from scipy.integrate import solve_ivp
from scipy.special import ellipk

from .integrators import solve

__all__ = [
    "oscillator_trajectory", "harmonic_oscillator", "pendulum_trajectory", "pendulum",
    "pendulum_period", "double_pendulum", "double_pendulum_xy", "double_pendulum_energy",
    "projectile_trajectory", "projectile", "nbody_trajectory", "nbody", "nbody_energy",
    "FIGURE_EIGHT", "collision",
]


def oscillator_trajectory(
    x0: float = 1.0, v0: float = 0.0, omega: float = 1.0, gamma: float = 0.0, drive: float = 0.0,
    drive_omega: float = 1.0, t_max: float = 20.0, n: int = 1000,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Damped, driven oscillator $\ddot x + 2\gamma\dot x + \omega^2 x = F\cos\Omega t$.

    Return time and a state matrix with columns for displacement and velocity.
    """
    def rhs(t, y):
        return [y[1], -omega**2 * y[0] - 2 * gamma * y[1] + drive * np.cos(drive_omega * t)]

    t, y = solve(rhs, [x0, v0], (0, t_max), n)
    return t, y


def harmonic_oscillator(x0=1.0, v0=0.0, omega=1.0, gamma=0.0, drive=0.0,
                        drive_omega=1.0, t_max=20.0, n=1000):
    """Compatibility interface. Use :func:`oscillator_trajectory` for time and a state matrix."""
    warnings.warn("harmonic_oscillator is deprecated; use oscillator_trajectory", DeprecationWarning, stacklevel=2)
    t, y = oscillator_trajectory(x0, v0, omega, gamma, drive, drive_omega, t_max, n)
    return t, y[:, 0], y[:, 1]


def pendulum_trajectory(
    theta0: float = 1.0, omega0: float = 0.0, g: float = 9.81, length: float = 1.0,
    t_max: float = 10.0, n: int = 500,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Nonlinear simple pendulum.

    Return time and a state matrix with columns for angle and angular velocity.
    """
    def rhs(_, y):
        return [y[1], -(g / length) * np.sin(y[0])]

    t, y = solve(rhs, [theta0, omega0], (0, t_max), n)
    return t, y


def pendulum(theta0=1.0, omega0=0.0, g=9.81, length=1.0, t_max=10.0, n=500):
    """Compatibility interface. Use :func:`pendulum_trajectory` for time and a state matrix."""
    warnings.warn("pendulum is deprecated; use pendulum_trajectory", DeprecationWarning, stacklevel=2)
    t, y = pendulum_trajectory(theta0, omega0, g, length, t_max, n)
    return t, y[:, 0], y[:, 1]


def pendulum_period(theta0, g=9.81, length=1.0):
    r"""Exact period $T = 4\sqrt{L/g}\,K(\sin^2(\theta_0/2))$, released from rest."""
    return 4 * np.sqrt(length / g) * ellipk(np.sin(theta0 / 2) ** 2)


def double_pendulum(
    state0: ArrayLike, m1: float = 1.0, m2: float = 1.0, l1: float = 1.0, l2: float = 1.0, g: float
    = 9.81, t_max: float = 20.0, n: int = 2000,
) -> tuple[np.ndarray, np.ndarray]:
    """Double pendulum. ``state = [theta1, theta2, omega1, omega2]``. Returns ``(t, y)``."""
    def rhs(_, s):
        th1, th2, w1, w2 = s
        d = th1 - th2
        den = 2 * m1 + m2 - m2 * np.cos(2 * d)
        a1 = (-g * (2 * m1 + m2) * np.sin(th1) - m2 * g * np.sin(th1 - 2 * th2)
              - 2 * np.sin(d) * m2 * (w2**2 * l2 + w1**2 * l1 * np.cos(d))) / (l1 * den)
        a2 = (2 * np.sin(d) * (w1**2 * l1 * (m1 + m2) + g * (m1 + m2) * np.cos(th1)
                               + w2**2 * l2 * m2 * np.cos(d))) / (l2 * den)
        return [w1, w2, a1, a2]

    return solve(rhs, state0, (0, t_max), n)


def double_pendulum_xy(y, l1=1.0, l2=1.0):
    """Cartesian positions ``(x1, y1, x2, y2)`` of both bobs (y points up)."""
    x1 = l1 * np.sin(y[:, 0])
    y1 = -l1 * np.cos(y[:, 0])
    return x1, y1, x1 + l2 * np.sin(y[:, 1]), y1 - l2 * np.cos(y[:, 1])


def double_pendulum_energy(y, m1=1.0, m2=1.0, l1=1.0, l2=1.0, g=9.81):
    th1, th2, w1, w2 = y.T
    kinetic = (0.5 * (m1 + m2) * l1**2 * w1**2 + 0.5 * m2 * l2**2 * w2**2
               + m2 * l1 * l2 * w1 * w2 * np.cos(th1 - th2))
    potential = -(m1 + m2) * g * l1 * np.cos(th1) - m2 * g * l2 * np.cos(th2)
    return kinetic + potential


def projectile_trajectory(
    speed: float, angle_deg: float, drag: float = 0.0, g: float = 9.81, h0: float = 0.0,
    n: int = 300,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Projectile with optional quadratic drag $\mathbf a = -g\hat y - c|\mathbf v|\mathbf v$.

    ``drag`` is $c$ in 1/m.

    Return time and a state matrix with columns for x, y, vx, vy.
    """
    ang = np.radians(angle_deg)

    def rhs(_, s):
        vx, vy = s[2], s[3]
        sp = np.hypot(vx, vy)
        return [vx, vy, -drag * sp * vx, -g - drag * sp * vy]

    def ground(_, s):
        return s[1]

    ground.terminal = True
    ground.direction = -1
    sol = solve_ivp(rhs, (0, 1e4), [0, h0, speed * np.cos(ang), speed * np.sin(ang)],
                    events=ground, dense_output=True, rtol=1e-10, atol=1e-12)
    if len(sol.t_events[0]) == 0:
        raise RuntimeError("projectile never landed")
    t = np.linspace(0, sol.t_events[0][0], n)
    s = sol.sol(t)
    return t, s.T


def projectile(speed, angle_deg, drag=0.0, g=9.81, h0=0.0, n=300):
    """Compatibility interface. Use :func:`projectile_trajectory` for time and a state matrix."""
    warnings.warn("projectile is deprecated; use projectile_trajectory", DeprecationWarning, stacklevel=2)
    t, y = projectile_trajectory(speed, angle_deg, drag, g, h0, n)
    return t, y[:, 0], y[:, 1]


def nbody_trajectory(
    masses: ArrayLike, pos0: ArrayLike, vel0: ArrayLike, t_max: float, n: int = 1000,
    G: float = 1.0, softening: float = 0.0,
) -> tuple[np.ndarray, np.ndarray]:
    r"""Newtonian N-body gravity in any dimension.

    ``pos0`` and ``vel0`` have shape ``(N, d)``.

    Return time and a state matrix with columns for flattened positions followed by flattened velocities in body order.
    """
    m = np.asarray(masses, float)
    pos0 = np.asarray(pos0, float)
    vel0 = np.asarray(vel0, float)
    N, d = pos0.shape

    def acc(pos):
        diff = pos[None, :, :] - pos[:, None, :]            # r_j - r_i
        r2 = (diff**2).sum(-1) + softening**2
        np.fill_diagonal(r2, 1.0)
        inv3 = r2 ** -1.5
        np.fill_diagonal(inv3, 0.0)
        return G * (diff * (m[None, :, None] * inv3[:, :, None])).sum(axis=1)

    def rhs(_, y):
        return np.concatenate([y[N * d:], acc(y[:N * d].reshape(N, d)).ravel()])

    t, y = solve(rhs, np.concatenate([pos0.ravel(), vel0.ravel()]), (0, t_max), n)
    return t, y


def nbody(masses, pos0, vel0, t_max, n=1000, G=1.0, softening=0.0):
    """Compatibility interface. Use :func:`nbody_trajectory` for time and a state matrix."""
    warnings.warn("nbody is deprecated; use nbody_trajectory", DeprecationWarning, stacklevel=2)
    t, y = nbody_trajectory(masses, pos0, vel0, t_max, n, G, softening)
    n_bodies, dim = np.asarray(pos0).shape
    positions, velocities = np.hsplit(y, 2)
    return t, positions.reshape(-1, n_bodies, dim), velocities.reshape(-1, n_bodies, dim)


def nbody_energy(masses, pos, vel, G=1.0, softening=0.0):
    """Total energy at each saved time of an :func:`nbody` run."""
    m = np.asarray(masses, float)
    kinetic = 0.5 * (m[None, :] * (vel**2).sum(-1)).sum(axis=1)
    potential = np.zeros(pos.shape[0])
    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            r = np.sqrt(((pos[:, i] - pos[:, j]) ** 2).sum(-1) + softening**2)
            potential -= G * m[i] * m[j] / r
    return kinetic + potential


# Chenciner-Montgomery figure-eight orbit (G = 1, unit masses, period ~ 6.32591398).
FIGURE_EIGHT = {
    "masses": [1.0, 1.0, 1.0],
    "pos0": [[0.97000436, -0.24308753], [-0.97000436, 0.24308753], [0.0, 0.0]],
    "vel0": [[0.466203685, 0.43236573], [0.466203685, 0.43236573], [-0.93240737, -0.86473146]],
    "period": 6.32591398,
}


def collision(m1: float, m2: float, u1: ArrayLike, u2: ArrayLike,
              normal: ArrayLike = (1,), restitution: float = 1.) -> tuple[np.ndarray, np.ndarray]:
    r"""Post-impact velocities for smooth bodies, $J=(1+e)(u_1-u_2)\cdot n/(1/m_1+1/m_2)$.

    Use a unit direction from body one towards body two. Only closing velocities
    receive an impulse. Tangential motion is unchanged even for zero restitution.
    """
    a, b, n = (np.atleast_1d(np.asarray(x, float)) for x in (u1, u2, normal))
    if a.shape != b.shape or a.shape != n.shape or n.ndim != 1 or not np.linalg.norm(n):
        raise ValueError("velocities and a nonzero normal must have matching dimensions")
    if min(m1, m2) <= 0 or not 0 <= restitution <= 1:
        raise ValueError("require positive masses and restitution between zero and one")
    n = n / np.linalg.norm(n)
    impulse = (1 + restitution) * max(0., (a - b) @ n) / (1/m1 + 1/m2)
    return a - impulse*n/m1, b + impulse*n/m2
