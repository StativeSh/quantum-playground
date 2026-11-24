"""Animated GIFs. Each animation takes ``n_frames`` and returns ``(fig, update, frames)``.

Register one with ``@animation("name")``; render with ``python -m qplay animate name``.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import PowerNorm

from . import kinetic, mechanics, plotting, quantum, statmech

__all__ = [
    "ANIMATIONS", "animation", "render", "double_pendulum_anim", "wavepacket_anim",
    "figure_eight_anim", "double_slit_anim", "ising_anim", "gas_anim",
]

ANIMATIONS: dict = {}


def animation(name):
    def register(fn):
        ANIMATIONS[name] = fn
        return fn

    return register


def render(name, outdir="figures", n_frames=120, fps=24):
    """Render one animation to ``<outdir>/<name>.gif`` and return the path."""
    if name not in ANIMATIONS:
        raise KeyError(f"unknown animation {name!r}; available: {', '.join(sorted(ANIMATIONS))}")
    fig, update, frames = ANIMATIONS[name](n_frames)
    return plotting.save_gif(fig, update, frames, Path(outdir) / f"{name}.gif", fps=fps)


@animation("double-pendulum")
def double_pendulum_anim(n_frames):
    """A chaotic double pendulum with a fading trail."""
    sub = 10  # integrate on a finer grid so the trail is smooth
    t, y = mechanics.double_pendulum([2.2, 2.6, 0.0, 0.0], t_max=15, n=n_frames * sub)
    x1, y1, x2, y2 = mechanics.double_pendulum_xy(y)
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.set(xlim=(-2.2, 2.2), ylim=(-2.2, 2.2), aspect="equal", xticks=[], yticks=[])
    ax.grid(False)
    (trail,) = ax.plot([], [], color="C1", lw=1, alpha=0.6)
    (rods,) = ax.plot([], [], "o-", color="k", lw=2, ms=7, mfc="C0")
    label = ax.text(0.03, 0.95, "", transform=ax.transAxes, va="top")

    def update(frame):
        i = frame * sub
        rods.set_data([0, x1[i], x2[i]], [0, y1[i], y2[i]])
        start = max(0, i - 25 * sub)
        trail.set_data(x2[start:i + 1], y2[start:i + 1])
        label.set_text(f"t = {t[i]:.1f} s")

    return fig, update, range(n_frames)


@animation("wavepacket")
def wavepacket_anim(n_frames):
    """A Gaussian wavepacket tunnelling through and reflecting off a barrier."""
    x = np.linspace(-60, 60, 2048, endpoint=False)
    V = np.where(np.abs(x) < 1.0, 2.0, 0.0)
    psi0 = quantum.gaussian_wavepacket(x, x0=-20, sigma=3, k0=1.5)
    steps = 3000
    times, psi = quantum.split_step(psi0, x, V + quantum.absorbing_layer(x, 10.0),
                                    dt=0.01, steps=steps, save_every=max(1, steps // n_frames))
    fig, ax = plt.subplots(figsize=(6, 3.2))
    ax.fill_between(x, V / 2.0 * 0.15, color="0.85")
    (line,) = ax.plot([], [], color="C0")
    (real,) = ax.plot([], [], color="C1", lw=0.6, alpha=0.6)
    ax.set(xlim=(-45, 45), ylim=(-0.4, 0.4), xlabel="x")
    label = ax.text(0.02, 0.92, "", transform=ax.transAxes)

    def update(i):
        line.set_data(x, np.abs(psi[i]) ** 2)
        real.set_data(x, psi[i].real * 0.6)
        label.set_text(rf"$|\psi|^2$ and Re $\psi$,  t = {times[i]:.1f}")

    return fig, update, range(min(n_frames, len(psi)))


@animation("figure-eight")
def figure_eight_anim(n_frames):
    """Three equal masses chasing each other around a figure-eight."""
    fe = mechanics.FIGURE_EIGHT
    _, pos, _ = mechanics.nbody(fe["masses"], fe["pos0"], fe["vel0"], fe["period"], n=n_frames)
    fig, ax = plt.subplots(figsize=(5, 2.8))
    ax.plot(pos[:, 0, 0], pos[:, 0, 1], color="0.85", lw=1)
    ax.set(xlim=(-1.2, 1.2), ylim=(-0.45, 0.45), aspect="equal", xticks=[], yticks=[])
    ax.grid(False)
    bodies = ax.scatter(pos[0, :, 0], pos[0, :, 1], s=60, c=["C0", "C1", "C2"], zorder=3)

    def update(i):
        bodies.set_offsets(pos[i])

    return fig, update, range(n_frames)


@animation("double-slit")
def double_slit_anim(n_frames):
    """A 2D wavepacket passing through two slits and interfering."""
    steps = 1600
    run = quantum.double_slit_experiment(save_every=max(1, steps // n_frames))
    x, y, psi = run["x"], run["y"], run["psi"]
    amp = np.abs(psi)
    # square-root colour scale: the transmitted ~13% stays visible next to the bright incident packet
    norm = PowerNorm(gamma=0.5, vmin=0, vmax=np.percentile(amp, 99.9))
    fig, ax = plt.subplots(figsize=(4.6, 4.25))
    fig.subplots_adjust(left=0.02, right=0.98, bottom=0.02, top=0.98)
    fig.patch.set_facecolor("#0B0B0D")  # dark margins, so the GIF sits cleanly on dark pages
    im = ax.imshow(amp[0], origin="lower", extent=[x[0], x[-1], y[0], y[-1]], cmap="magma", norm=norm)
    ax.contour(x, y, run["V"], [1], colors="c", linewidths=0.8)
    ax.set(xlim=(-15, 50), ylim=(-30, 30), xticks=[], yticks=[])
    ax.grid(False)
    label = ax.text(0.02, 0.94, "", transform=ax.transAxes, color="w")

    def update(i):
        im.set_data(amp[i])
        label.set_text(rf"$|\psi|$,  t = {run['times'][i]:.1f}")

    return fig, update, range(min(n_frames, len(psi)))


@animation("ising")
def ising_anim(n_frames):
    """Domains coarsening in the 2D Ising model at the critical temperature."""
    snaps: list = []
    statmech.ising(L=128, T=statmech.T_CRITICAL, sweeps=n_frames, start="hot", seed=3, snapshots=snaps)
    fig, ax = plt.subplots(figsize=(4, 4))
    im = ax.imshow(snaps[0], cmap="gray", interpolation="nearest", vmin=-1, vmax=1)
    ax.set(xticks=[], yticks=[])
    ax.grid(False)
    title = ax.set_title("")

    def update(i):
        im.set_data(snaps[i])
        title.set_text(rf"Ising at $T_c$, sweep {i + 1}")

    return fig, update, range(n_frames)


@animation("gas")
def gas_anim(n_frames):
    """Discs in a box: every one starts at the same speed and the speeds spread into Maxwell-Boltzmann."""
    gas = kinetic.gas_box(n=400, dim=2, radius=0.009, t_max=8, save_every=2, seed=4)
    stride = max(1, (len(gas.t) - 1) // max(1, n_frames - 1))
    idx = np.arange(0, len(gas.t), stride)[:n_frames]
    speeds = np.linalg.norm(gas.velocities, axis=-1)
    kT = gas.temperature()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.6, 3.8), gridspec_kw={"width_ratios": [1, 1]})
    ax1.set(xlim=(0, 1), ylim=(0, 1), aspect="equal", xticks=[], yticks=[])
    ax1.grid(False)
    dots = ax1.scatter(*gas.positions[0].T, s=9, c=speeds[0], cmap="plasma", vmin=0, vmax=2.5)
    bins = np.linspace(0, 3, 31)
    vs = np.linspace(0, 3, 200)
    ax2.plot(vs, kinetic.maxwell_boltzmann_speed(vs, kT, dim=2), "k", lw=1.2, label="Maxwell-Boltzmann (2D)")
    bars = ax2.bar(bins[:-1], np.zeros(30), width=bins[1] - bins[0], align="edge", color="C0", alpha=0.6)
    ax2.set(xlim=(0, 3), ylim=(0, 2.2), xlabel="speed", yticks=[])
    ax2.legend(loc="upper right", fontsize=8)
    label = ax2.set_title("")

    def update(frame):
        k = idx[frame]
        dots.set_offsets(gas.positions[k])
        dots.set_array(speeds[k])
        window = speeds[max(0, k - 40):k + 1].ravel()       # smooth the histogram over recent steps
        hist, _ = np.histogram(window, bins=bins, density=True)
        for bar, h in zip(bars, hist):
            bar.set_height(h)
        label.set_text(f"t = {gas.t[k]:.2f}")

    return fig, update, range(len(idx))
