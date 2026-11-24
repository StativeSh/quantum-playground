r"""Kinetic theory: a hard-sphere gas in a box.

Units have $k_B = 1$, so "temperature" means $k_BT$ in energy units. In $d$ dimensions
equipartition gives $\langle\tfrac12 m v^2\rangle = \tfrac d2 k_BT$, and the speeds settle to the
Maxwell-Boltzmann distribution

$$f(v) = S_d\, v^{d-1}\left(\frac{m}{2\pi k_BT}\right)^{d/2} e^{-mv^2/2k_BT},
\qquad S_2 = 2\pi,\ S_3 = 4\pi .$$

Pressure, measured as momentum delivered to the walls per unit time per unit wall area,
obeys the ideal-gas law $pV = Nk_BT$ when the molecules take up a small fraction $\eta$ of the
box. For hard spheres the first correction is $pV/Nk_BT \approx 1 + 4\eta$ (discs: $1 + 2\eta$).
Here $V$ is the volume the centres can reach: a box of side $L - 2r$.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree
from scipy.special import gamma as gamma_fn

__all__ = [
    "maxwell_boltzmann_speed", "mean_speed", "rms_speed", "kinetic_temperature", "GasRun",
    "gas_box",
]


def maxwell_boltzmann_speed(v, kT, m=1.0, dim=3):
    r"""Maxwell-Boltzmann speed distribution $f(v)$ in ``dim`` dimensions (normalised on $v\ge0$)."""
    v = np.asarray(v, float)
    surface = 2 * np.pi ** (dim / 2) / gamma_fn(dim / 2)
    return surface * v ** (dim - 1) * (m / (2 * np.pi * kT)) ** (dim / 2) * np.exp(-m * v**2 / (2 * kT))


def mean_speed(kT, m=1.0, dim=3):
    r"""$\langle v\rangle = \sqrt{2k_BT/m}\;\Gamma\!\left(\tfrac{d+1}{2}\right)/\Gamma\!\left(\tfrac d2\right)$; in 3D, $\sqrt{8k_BT/\pi m}$."""
    return np.sqrt(2 * kT / m) * gamma_fn((dim + 1) / 2) / gamma_fn(dim / 2)


def rms_speed(kT, m=1.0, dim=3):
    r"""$c_{rms} = \sqrt{\langle v^2\rangle} = \sqrt{d\,k_BT/m}$; in 3D, $\sqrt{3k_BT/m}$."""
    return np.sqrt(dim * kT / m)


def kinetic_temperature(velocities, m=1.0):
    r"""$k_BT = m\langle v^2\rangle/d$ from velocities of shape ``(N, d)`` (or ``(..., N, d)``)."""
    v = np.asarray(velocities, float)
    return m * (v**2).sum(-1).mean(-1) / v.shape[-1]


@dataclass
class GasRun:
    """Result of :func:`gas_box`. Histories have shape ``(n_saved, N, dim)``."""

    t: np.ndarray
    positions: np.ndarray
    velocities: np.ndarray
    wall_impulse: np.ndarray   # cumulative momentum given to the walls at each saved time
    collisions: np.ndarray     # cumulative number of molecule-molecule collisions
    L: float
    radius: float
    m: float

    @property
    def dim(self):
        return self.positions.shape[-1]

    @property
    def n_particles(self):
        return self.positions.shape[1]

    @property
    def side(self):
        """Side $L - 2r$ of the box the centres can reach."""
        return self.L - 2 * self.radius

    @property
    def volume(self):
        """Volume available to the centres, $(L - 2r)^d$."""
        return self.side**self.dim

    @property
    def packing_fraction(self):
        r"""Fraction $\eta$ of the box filled by molecules (discs or spheres)."""
        ball = np.pi ** (self.dim / 2) / gamma_fn(self.dim / 2 + 1) * self.radius**self.dim
        return self.n_particles * ball / self.L**self.dim

    def pressure(self, start=0):
        r"""Mean pressure $p = \Delta J / (\Delta t\, A_{walls})$ from saved index ``start`` to the end,
        with total wall area $A_{walls} = 2d\,(L-2r)^{d-1}$."""
        area = 2 * self.dim * self.side ** (self.dim - 1)
        return (self.wall_impulse[-1] - self.wall_impulse[start]) / ((self.t[-1] - self.t[start]) * area)

    def temperature(self):
        """Kinetic temperature (constant: collisions are elastic)."""
        return float(kinetic_temperature(self.velocities[0], self.m))

    def speeds(self, start=0):
        """All molecular speeds from saved index ``start`` onwards, flattened."""
        return np.linalg.norm(self.velocities[start:], axis=-1).ravel()


def _place(n, dim, L, radius, rng):
    """Random non-overlapping centres inside the box (rejection sampling)."""
    pos = np.empty((0, dim))
    tries = 0
    while len(pos) < n:
        tries += 1
        if tries > 1000 * n:
            raise ValueError("box too crowded to place the molecules; lower n or radius")
        p = rng.uniform(radius, L - radius, dim)
        if len(pos) == 0 or np.min(((pos - p) ** 2).sum(1)) > (2 * radius) ** 2:
            pos = np.vstack([pos, p])
    return pos


def gas_box(n=400, dim=3, L=1.0, radius=0.02, speed=1.0, m=1.0, t_max=5.0, dt=None,
            save_every=10, seed=0):
    r"""Hard spheres (discs if ``dim=2``) bouncing elastically off each other and off the walls.

    Every molecule starts with the same ``speed`` in a random direction, so you can watch the
    speeds spread out into the Maxwell-Boltzmann distribution. Collisions swap the velocity
    components along the line of centres, which conserves energy and momentum exactly.

    ``dt`` defaults to a tenth of the time to travel one radius. Returns a :class:`GasRun`.
    """
    rng = np.random.default_rng(seed)
    pos = _place(n, dim, L, radius, rng)
    vel = rng.normal(size=(n, dim))
    vel *= speed / np.linalg.norm(vel, axis=1, keepdims=True)
    dt = 0.1 * radius / speed if dt is None else dt
    steps = int(np.ceil(t_max / dt))
    dt = t_max / steps

    n_saved = steps // save_every + 1
    P = np.empty((n_saved, n, dim))
    V = np.empty_like(P)
    J = np.zeros(n_saved)
    C = np.zeros(n_saved, dtype=int)
    P[0], V[0] = pos, vel
    impulse, collisions = 0.0, 0
    lo, hi = radius, L - radius

    for step in range(1, steps + 1):
        pos += vel * dt
        for wall, outside in ((lo, pos < lo), (hi, pos > hi)):
            if outside.any():
                impulse += 2 * m * np.abs(vel[outside]).sum()
                pos[outside] = 2 * wall - pos[outside]
                vel[outside] *= -1
        pairs = cKDTree(pos).query_pairs(2 * radius, output_type="ndarray")
        for i, j in pairs:
            d = pos[i] - pos[j]
            dv = vel[i] - vel[j]
            approach = d @ dv
            if approach < 0:                      # only if they are moving together
                kick = (approach / (d @ d)) * d
                vel[i] -= kick
                vel[j] += kick
                collisions += 1
        if step % save_every == 0:
            k = step // save_every
            P[k], V[k], J[k], C[k] = pos, vel, impulse, collisions

    t = np.arange(n_saved) * save_every * dt
    return GasRun(t, P, V, J, C, L, radius, m)
