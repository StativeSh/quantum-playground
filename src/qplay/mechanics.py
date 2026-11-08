r"""Classical mechanics: oscillators, pendulums, projectiles, gravity.

Pendulum:  $\ddot\theta = -\frac{g}{L}\sin\theta$
"""

from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp
from scipy.special import ellipk

from .integrators import solve


def harmonic_oscillator(x0=1.0, v0=0.0, omega=1.0, gamma=0.0, drive=0.0,
                        drive_omega=1.0, t_max=20.0, n=1000):
    r"""Damped, driven oscillator $\ddot x + 2\gamma\dot x + \omega^2 x = F\cos\Omega t$.

    Returns ``(t, x, v)``.
    """
    def rhs(t, y):
        return [y[1], -omega**2 * y[0] - 2 * gamma * y[1] + drive * np.cos(drive_omega * t)]

    t, y = solve(rhs, [x0, v0], (0, t_max), n)
    return t, y[:, 0], y[:, 1]


def pendulum(theta0=1.0, omega0=0.0, g=9.81, length=1.0, t_max=10.0, n=500):
    """Nonlinear simple pendulum. Returns ``(t, theta, omega)``."""
    def rhs(_, y):
        return [y[1], -(g / length) * np.sin(y[0])]

    t, y = solve(rhs, [theta0, omega0], (0, t_max), n)
    return t, y[:, 0], y[:, 1]


def pendulum_period(theta0, g=9.81, length=1.0):
    r"""Exact period $T = 4\sqrt{L/g}\,K(\sin^2(\theta_0/2))$, released from rest."""
    return 4 * np.sqrt(length / g) * ellipk(np.sin(theta0 / 2) ** 2)


def double_pendulum(state0, m1=1.0, m2=1.0, l1=1.0, l2=1.0, g=9.81, t_max=20.0, n=2000):
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


def projectile(speed, angle_deg, drag=0.0, g=9.81, h0=0.0, n=300):
    r"""Projectile with optional quadratic drag $\mathbf a = -g\hat y - c|\mathbf v|\mathbf v$.

    ``drag`` is $c$ in 1/m. Returns ``(t, x, y)`` from launch until ground impact.
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
    return t, s[0], s[1]


def nbody(masses, pos0, vel0, t_max, n=1000, G=1.0, softening=0.0):
    """Newtonian N-body gravity in any dimension.

    ``pos0`` and ``vel0`` have shape ``(N, d)``. Returns ``(t, pos, vel)`` with
    ``pos.shape == (n, N, d)``.
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
    return t, y[:, :N * d].reshape(n, N, d), y[:, N * d:].reshape(n, N, d)


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
