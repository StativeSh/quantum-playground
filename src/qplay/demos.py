"""Ready-made figures. Each demo takes no arguments and returns a matplotlib Figure.

Add one by decorating a function with ``@demo("name")``; it then shows up in
``python -m qplay list`` and runs with ``python -m qplay run name``.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from . import chaos, em, mechanics, plotting, quantum, waves

DEMOS: dict = {}


def demo(name):
    def register(fn):
        DEMOS[name] = fn
        return fn

    return register


def run(name, outdir="figures"):
    """Run one demo and save its figure. Returns the file path."""
    if name not in DEMOS:
        raise KeyError(f"unknown demo {name!r}; available: {', '.join(sorted(DEMOS))}")
    return plotting.save(DEMOS[name](), name, outdir)


@demo("pendulum")
def pendulum_demo():
    """Large-amplitude pendulum vs the small-angle approximation."""
    theta0, g, L = 2.5, 9.81, 1.0
    T = mechanics.pendulum_period(theta0, g, L)
    t, th, _ = mechanics.pendulum(theta0, 0.0, g, L, t_max=2 * T, n=800)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(t, th, label="nonlinear")
    ax.plot(t, theta0 * np.cos(np.sqrt(g / L) * t), "--", label="small-angle approximation")
    ax.set(xlabel="t [s]", ylabel=r"$\theta$ [rad]",
           title=rf"Pendulum released at {theta0} rad: $T={T:.3f}$ s")
    ax.legend()
    return fig


@demo("double-pendulum")
def double_pendulum_demo():
    """Sensitive dependence on initial conditions in a double pendulum."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for eps, style in [(0.0, "-"), (1e-6, "--")]:
        t, y = mechanics.double_pendulum([2.0, 2.0 + eps, 0.0, 0.0], t_max=25, n=2500)
        ax.plot(t, y[:, 1], style, label=rf"$\theta_2(0)=2+{eps:g}$")
    ax.set(xlabel="t [s]", ylabel=r"$\theta_2$ [rad]",
           title="Double pendulum: a $10^{-6}$ nudge changes everything")
    ax.legend()
    return fig


@demo("projectile")
def projectile_demo():
    """Projectile trajectories with and without air drag."""
    fig, ax = plt.subplots(figsize=(7, 4))
    for angle in (15, 30, 45, 60, 75):
        _, x, y = mechanics.projectile(30, angle)
        ax.plot(x, y, color=f"C{angle // 15 - 1}", label=f"{angle}°")
        _, xd, yd = mechanics.projectile(30, angle, drag=0.02)
        ax.plot(xd, yd, "--", color=f"C{angle // 15 - 1}")
    ax.set(xlabel="x [m]", ylabel="y [m]", title="Projectiles: vacuum (solid) vs quadratic drag (dashed)")
    ax.legend(ncol=5, fontsize=8)
    return fig


@demo("orbits")
def orbits_demo():
    """Three-body figure-eight choreography."""
    fe = mechanics.FIGURE_EIGHT
    _, pos, _ = mechanics.nbody(fe["masses"], fe["pos0"], fe["vel0"], fe["period"], n=600)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    for i in range(3):
        (line,) = ax.plot(pos[:, i, 0], pos[:, i, 1], lw=2 - 0.5 * i, alpha=0.6, label=f"body {i + 1}")
        ax.plot(*pos[0, i], "o", color=line.get_color(), ms=9)
    ax.set(aspect="equal", xlabel="x", ylabel="y", title="Three bodies on a figure-eight orbit")
    ax.legend()
    return fig


@demo("wave")
def wave_demo():
    """1D wave equation: a pulse splitting and reflecting off fixed ends."""
    x = np.linspace(0, 10, 401)
    t, u = waves.wave_1d(np.exp(-((x - 5) ** 2) / 0.1), x, c=1.0, t_max=8.0)
    fig, ax = plt.subplots(figsize=(7, 4))
    im = ax.imshow(u, extent=[x[0], x[-1], t[-1], t[0]], aspect="auto", cmap="RdBu_r",
                   vmin=-1, vmax=1)
    ax.set(xlabel="x", ylabel="t", title="A plucked string splits, reflects and inverts")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="u")
    return fig


@demo("heat")
def heat_demo():
    """Diffusion of a top-hat temperature profile."""
    x = np.linspace(0, 1, 201)
    t, u = waves.heat_1d(np.where(np.abs(x - 0.5) < 0.2, 1.0, 0.0), x, alpha=0.01, t_max=0.5, nt=400)
    fig, ax = plt.subplots(figsize=(7, 4))
    for k in (0, 5, 20, 80, 400):
        ax.plot(x, u[k], label=f"t={t[k]:.3f}")
    ax.set(xlabel="x", ylabel="u", title="Diffusion smooths a top-hat profile")
    ax.legend()
    return fig


@demo("fourier")
def fourier_demo():
    """Square wave built from Fourier partial sums (Gibbs phenomenon)."""
    period = 2 * np.pi
    f = lambda s: np.sign(np.sin(s))  # noqa: E731
    a0, a, b = waves.fourier_coefficients(f, period, 40, points=[period / 2])
    x = np.linspace(0, 2 * period, 1000)
    fig, ax = plt.subplots(figsize=(7, 4))
    for n in (1, 3, 9, 39):
        ax.plot(x, waves.fourier_sum(a0, a[:n], b[:n], x, period), label=f"{n} terms", lw=1)
    ax.set(xlabel="x", title="Square wave from its Fourier series (Gibbs overshoot)")
    ax.legend()
    return fig


@demo("tise")
def tise_demo():
    """Quantum harmonic oscillator eigenstates from a finite-difference solver."""
    x = np.linspace(-6, 6, 1200)
    E, psi = quantum.solve_tise(lambda s: 0.5 * s**2, x, n_states=5)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(x, 0.5 * x**2, "k", lw=1)
    for n in range(5):
        ax.plot(x, E[n] + psi[n] * 0.6)
        ax.axhline(E[n], color=f"C{n}", lw=0.5, alpha=0.5)
    ax.set(ylim=(0, 6), xlabel="x", ylabel="energy",
           title=r"Quantum harmonic oscillator: $E_n = n + \frac{1}{2}$")
    return fig


@demo("wavepacket")
def wavepacket_demo():
    """Gaussian wavepacket tunnelling through a barrier (split-step Fourier)."""
    x = np.linspace(-60, 60, 2048, endpoint=False)
    V0, width, k0 = 2.0, 2.0, 1.5
    V = np.where(np.abs(x) < width / 2, V0, 0.0)
    psi0 = quantum.gaussian_wavepacket(x, x0=-20, sigma=3, k0=k0)
    times, psi = quantum.split_step(psi0, x, V, dt=0.01, steps=3000, save_every=1000)
    dx = x[1] - x[0]
    transmitted = np.sum(np.abs(psi[-1][x > width / 2]) ** 2) * dx
    T = quantum.barrier_transmission(k0**2 / 2, V0, width)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.fill_between(x, V / V0 * 0.08, color="0.8", label="barrier")
    for p, tt in zip(psi, times):
        ax.plot(x, np.abs(p) ** 2, label=f"t={tt:.0f}")
    ax.set(xlim=(-45, 45), xlabel="x", ylabel=r"$|\psi|^2$",
           title=f"Tunnelling: {transmitted:.2f} transmitted (plane-wave T={T:.2f})")
    ax.legend()
    return fig


@demo("laplace")
def laplace_demo():
    """Electrostatic potential in a box by solving Laplace's equation."""
    V = em.solve_laplace(101, 101, top=1.0)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    im = ax.imshow(V, origin="lower", extent=[0, 1, 0, 1], cmap="viridis")
    ax.contour(np.linspace(0, 1, 101), np.linspace(0, 1, 101), V, 12, colors="w", linewidths=0.5)
    ax.set(xlabel="x", ylabel="y", title="Potential in a box: top edge at 1, others at 0")
    ax.grid(False)
    fig.colorbar(im, ax=ax, label="V")
    return fig


@demo("lorenz")
def lorenz_demo():
    """The Lorenz strange attractor."""
    _, y = chaos.lorenz(t_max=50, n=8000)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(y[:, 0], y[:, 2], lw=0.4)
    ax.set(xlabel="x", ylabel="z", title="Lorenz attractor")
    return fig


@demo("mandelbrot")
def mandelbrot_demo():
    """The Mandelbrot set."""
    counts = chaos.mandelbrot(width=700, height=470, max_iter=120)
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.imshow(counts, extent=[-2.2, 0.8, -1.2, 1.2], cmap="magma", origin="lower")
    ax.set(xlabel="Re c", ylabel="Im c", title="Mandelbrot set")
    ax.grid(False)
    return fig


@demo("bifurcation")
def bifurcation_demo():
    """Bifurcation diagram of the logistic map."""
    r, x = chaos.bifurcation(np.linspace(2.8, 4.0, 1200))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(r, x, s=0.1, c="k", alpha=0.3, linewidths=0)
    ax.set(xlabel="r", ylabel="x", title="Logistic map: the road to chaos")
    return fig
