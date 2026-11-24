"""Ready-made figures. Each demo takes no arguments and returns a matplotlib Figure.

Add one by decorating a function with ``@demo("name")``; it then shows up in
``python -m qplay list`` and runs with ``python -m qplay run name``.
"""

from __future__ import annotations

from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from . import (atomic, chaos, circuits, complexplane, dynamics, em, kinetic, linalg, mechanics, nuclear, plotting,
               quantum, statmech, waves)

__all__ = [
    "DEMOS", "demo", "run", "pendulum_demo", "double_pendulum_demo", "projectile_demo",
    "orbits_demo", "wave_demo", "heat_demo", "fourier_demo", "tise_demo", "wavepacket_demo",
    "laplace_demo", "lorenz_demo", "mandelbrot_demo", "bifurcation_demo", "hydrogen_demo",
    "double_slit_demo", "ising_demo", "phase_portrait_demo", "pendulum_phase_space_demo",
    "domain_coloring_demo", "linear_map_demo", "maxwell_boltzmann_demo", "coherent_state_demo",
    "zeeman_demo", "decay_chain_demo", "rlc_resonance_demo", "energy_drift_demo",
]

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
def pendulum_demo() -> Figure:
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
def double_pendulum_demo() -> Figure:
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
def projectile_demo() -> Figure:
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
def orbits_demo() -> Figure:
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
def wave_demo() -> Figure:
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
def heat_demo() -> Figure:
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
def fourier_demo() -> Figure:
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
def tise_demo() -> Figure:
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
def wavepacket_demo() -> Figure:
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
def laplace_demo() -> Figure:
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
def lorenz_demo() -> Figure:
    """The Lorenz strange attractor."""
    _, y = chaos.lorenz(t_max=50, n=8000)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(y[:, 0], y[:, 2], lw=0.4)
    ax.set(xlabel="x", ylabel="z", title="Lorenz attractor")
    return fig


@demo("mandelbrot")
def mandelbrot_demo() -> Figure:
    """The Mandelbrot set."""
    counts = chaos.mandelbrot(width=700, height=470, max_iter=120)
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.imshow(counts, extent=[-2.2, 0.8, -1.2, 1.2], cmap="magma", origin="lower")
    ax.set(xlabel="Re c", ylabel="Im c", title="Mandelbrot set")
    ax.grid(False)
    return fig


@demo("bifurcation")
def bifurcation_demo() -> Figure:
    """Bifurcation diagram of the logistic map."""
    r, x = chaos.bifurcation(np.linspace(2.8, 4.0, 1200))
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(r, x, s=0.1, c="k", alpha=0.3, linewidths=0)
    ax.set(xlabel="r", ylabel="x", title="Logistic map: the road to chaos")
    return fig


@demo("hydrogen")
def hydrogen_demo() -> Figure:
    """Hydrogen orbital probability densities in the xz-plane."""
    states = [(1, 0, 0), (2, 0, 0), (2, 1, 0), (3, 1, 0), (3, 2, 0), (3, 2, 1), (4, 2, 0), (4, 3, 1)]
    fig, axes = plt.subplots(2, 4, figsize=(11, 5.6))
    names = "spdf"
    for ax, (n, l, m) in zip(axes.flat, states):
        X, Z, rho = quantum.hydrogen_density_xz(n, l, m, points=260)
        ax.imshow(rho ** 0.5, origin="lower", cmap="inferno",
                  extent=[X.min(), X.max(), Z.min(), Z.max()])
        ax.set_title(rf"${n}{names[l]}$, $m={m}$", fontsize=10)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.grid(False)
    fig.suptitle(r"Hydrogen orbitals $|\psi_{nlm}|$ in the $xz$-plane (lengths in $a_0$, own scale each)")
    return fig


@demo("double-slit")
def double_slit_demo() -> Figure:
    """Quantum double-slit interference from a 2D wavepacket simulation."""
    run = quantum.double_slit_experiment()
    x, y, psi = run["x"], run["y"], run["psi"]
    frame = np.argmin(np.abs(run["times"] - 11.0))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5), gridspec_kw={"width_ratios": [2, 1]})
    rho = np.abs(psi[frame]) ** 2
    ax1.imshow(rho, origin="lower", extent=[x[0], x[-1], y[0], y[-1]], cmap="magma",
               vmax=np.percentile(rho, 99.7))
    ax1.contour(x, y, run["V"], [1], colors="c", linewidths=0.8)
    ax1.axvline(run["screen_x"], color="w", ls="--", lw=0.8)
    ax1.set(xlim=(-15, 50), ylim=(-30, 30), xlabel="x", ylabel="y",
            title=rf"$|\psi|^2$ at $t={run['times'][frame]:.0f}$ (dashed: screen)")
    ax1.grid(False)
    L, d, lam = run["screen_x"], 5.0, 2 * np.pi / 3.0
    path_diff = np.hypot(L, y + d / 2) - np.hypot(L, y - d / 2)
    ax2.plot(run["screen"], y, label="simulation")
    ax2.plot(np.cos(np.pi * path_diff / lam) ** 2, y, "k:", label="two point sources")
    ax2.set(ylim=(-30, 30), xlabel="time-integrated intensity", title="Screen")
    ax2.legend(fontsize=8, loc="lower right")
    return fig


@demo("ising")
def ising_demo() -> Figure:
    """2D Ising model: lattice snapshots and magnetisation vs Onsager's exact result."""
    fig = plt.figure(figsize=(11, 4))
    grid = fig.add_gridspec(1, 4)
    for i, T in enumerate((1.8, statmech.T_CRITICAL, 3.2)):
        spins, _, _ = statmech.ising(L=96, T=T, sweeps=300, start="hot", seed=i)
        ax = fig.add_subplot(grid[0, i])
        ax.imshow(spins, cmap="gray", interpolation="nearest")
        ax.set(title=rf"$T={T:.2f}$", xticks=[], yticks=[])
        ax.grid(False)
    ax = fig.add_subplot(grid[0, 3])
    temps = np.linspace(1.2, 3.6, 20)
    mags = [np.mean(np.abs(statmech.ising(L=32, T=T, sweeps=400, seed=7)[1][150:])) for T in temps]
    fine = np.linspace(1.0, 3.6, 300)
    ax.plot(fine, statmech.onsager_magnetization(fine), "k", lw=1, label="Onsager (exact)")
    ax.plot(temps, mags, "o", ms=4, label=r"Monte Carlo, $32^2$")
    ax.axvline(statmech.T_CRITICAL, color="r", lw=0.5)
    ax.set(xlabel="T", ylabel=r"$\langle|m|\rangle$", title="Phase transition")
    ax.legend(fontsize=7)
    return fig


@demo("phase-portrait")
def phase_portrait_demo() -> Figure:
    """Phase planes with automatically classified fixed points."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    def damped_pendulum(s):
        return [s[1], -np.sin(s[0]) - 0.25 * s[1]]

    dynamics.phase_portrait(damped_pendulum, (-2 * np.pi, 2 * np.pi), (-3, 3), ax=ax1,
                            classify=[(g, 0) for g in np.arange(-2, 3) * np.pi])
    ax1.set(xlabel=r"$\theta$", ylabel=r"$\dot\theta$", title=r"Damped pendulum $\ddot\theta=-\sin\theta-0.25\dot\theta$")

    def predator_prey(s):
        return [s[0] * (1 - s[1]), s[1] * (s[0] - 1) * 0.8]

    dynamics.phase_portrait(predator_prey, (0, 3), (0, 3), ax=ax2, classify=[(0.01, 0.01), (1, 1)])
    ax2.set(xlabel="prey", ylabel="predators", title="Lotka-Volterra")
    return fig


@demo("pendulum-phase-space")
def pendulum_phase_space_demo() -> Figure:
    r"""Pendulum energy contours $H = p^2/2 - \cos q$ with the separatrix."""
    q, p = np.meshgrid(np.linspace(-2 * np.pi, 2 * np.pi, 400), np.linspace(-3, 3, 300))
    H = p**2 / 2 - np.cos(q)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.contour(q, p, H, levels=np.linspace(-0.95, 3, 18), cmap="viridis", linewidths=0.9)
    ax.contour(q, p, H, levels=[1.0], colors="r", linewidths=1.6)
    ax.set(xlabel="q", ylabel="p",
           title="Pendulum phase space: oscillation inside the red separatrix, rotation outside")
    return fig


@demo("domain-coloring")
def domain_coloring_demo() -> Figure:
    r"""Domain colouring of $f(z) = (z^2-1)(z-2-i)^2/(z^2+2+2i)$."""
    def f(z):
        return (z**2 - 1) * (z - 2 - 1j) ** 2 / (z**2 + 2 + 2j)

    fig, ax = plt.subplots(figsize=(6, 5.5))
    ax.imshow(complexplane.domain_coloring(f, (-3, 3), (-3, 3), 700), origin="lower", extent=[-3, 3, -3, 3])
    count = complexplane.winding_number(f, 0, 1.5)
    t = np.linspace(0, 2 * np.pi, 200)
    ax.plot(1.5 * np.cos(t), 1.5 * np.sin(t), "w--", lw=1)
    ax.set(xlabel="Re z", ylabel="Im z",
           title=f"Hue = arg f, bands = log|f|\nzeros - poles inside dashed circle = {count}")
    ax.grid(False)
    return fig


@demo("linear-map")
def linear_map_demo() -> Figure:
    """A 2x2 matrix maps the unit circle to an ellipse along its singular vectors."""
    A = np.array([[1.6, 0.9], [0.3, 0.8]])
    sigma, U = linalg.singular_axes(A)
    vals, vecs = np.linalg.eig(A)
    assert np.allclose(vecs.imag, 0), "this demo's matrix has real eigenvectors"
    vals, vecs = vals.real, vecs.real  # recent NumPy returns a complex dtype even then
    fig, ax = plt.subplots(figsize=(6, 5.5))
    circle = linalg.unit_circle_image(np.eye(2))
    ax.plot(*circle, color="0.6", label="unit circle")
    ax.plot(*linalg.unit_circle_image(A), color="C0", label="image under A")
    for i in range(2):
        ax.annotate("", sigma[i] * U[:, i], (0, 0), arrowprops=dict(arrowstyle="->", color="C1", lw=2))
        ax.plot(*np.outer(vecs[:, i], [-2.2, 2.2]), "--", color="C2", lw=1,
                label="eigenvector lines" if i == 0 else None)
    ax.plot([], [], color="C1", label=r"singular axes $\sigma_i\mathbf{u}_i$")
    ax.set(aspect="equal", xlim=(-2.2, 2.2), ylim=(-2.2, 2.2),
           title=rf"$A$: $\sigma = {sigma[0]:.2f}, {sigma[1]:.2f}$; $\lambda = {vals[0]:.2f}, {vals[1]:.2f}$")
    ax.legend(fontsize=8, loc="lower right")
    return fig


@demo("maxwell-boltzmann")
def maxwell_boltzmann_demo() -> Figure:
    """Hard-sphere gas: one starting speed relaxes to the Maxwell-Boltzmann distribution."""
    gas = kinetic.gas_box(n=400, dim=3, radius=0.02, t_max=6, save_every=20, seed=1)
    kT = gas.temperature()
    v = np.linalg.norm(gas.velocities, axis=-1)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    bins = np.linspace(0, 2.5, 41)
    for k, colour in [(1, "C1"), (5, "C2")]:
        ax1.hist(v[k], bins=bins, density=True, histtype="step", color=colour, label=f"t = {gas.t[k]:.2f}")
    ax1.hist(gas.speeds(len(gas.t) // 2), bins=bins, density=True, alpha=0.4, color="C0", label="t > 3 (averaged)")
    vs = np.linspace(0, 2.5, 300)
    ax1.plot(vs, kinetic.maxwell_boltzmann_speed(vs, kT), "k", label="Maxwell-Boltzmann")
    ax1.axvline(1.0, color="0.5", ls=":", lw=1, label="initial speed")
    ax1.set(xlabel="speed", ylabel="probability density", title="All molecules start at the same speed")
    ax1.legend(fontsize=8)
    ratio = (v**4).mean(1) / (v**2).mean(1) ** 2
    ax2.plot(gas.t, ratio)
    ax2.axhline(5 / 3, color="k", ls="--", label=r"Maxwell-Boltzmann: $5/3$")
    Z = gas.pressure() * gas.volume / (gas.n_particles * kT)
    ax2.set(xlabel="time", ylabel=r"$\langle v^4\rangle / \langle v^2\rangle^2$",
            title=rf"Relaxation;  measured $pV/Nk_BT = {Z:.3f}$ (theory $1+4\eta = {1 + 4 * gas.packing_fraction:.3f}$)")
    ax2.legend()
    return fig


@demo("coherent-state")
def coherent_state_demo() -> Figure:
    r"""A coherent state swings in $V = x^2/2$ like a classical particle, without spreading."""
    x = np.linspace(-20, 20, 1024, endpoint=False)
    alpha = quantum.coherent_alpha(4.0, 0.0)
    times, psi = quantum.split_step(quantum.coherent_state(x, alpha), x, 0.5 * x**2, dt=0.01, steps=1600, save_every=4)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4), gridspec_kw={"width_ratios": [2, 1]})
    ax1.imshow(np.abs(psi.T) ** 2, origin="lower", aspect="auto", cmap="magma",
               extent=[times[0], times[-1], x[0], x[-1]])
    ax1.plot(times, 4 * np.cos(times), "c--", lw=1, label=r"classical $x = 4\cos t$")
    ax1.set(ylim=(-7, 7), xlabel="t", ylabel="x", title=r"$|\psi(x,t)|^2$ for a coherent state")
    ax1.legend(loc="upper right", fontsize=8)
    ax1.grid(False)
    gauss = quantum.gaussian_wavepacket(x, 4.0, sigma=np.sqrt(0.5))
    _, free = quantum.split_step(gauss, x, 0 * x, dt=0.01, steps=1600, save_every=4)
    width = [np.sqrt(quantum.expectation(x**2, p, x) - quantum.expectation(x, p, x) ** 2) for p in psi]
    width_free = [np.sqrt(quantum.expectation(x**2, p, x) - quantum.expectation(x, p, x) ** 2) for p in free]
    ax2.plot(times, width, label="in the oscillator")
    ax2.plot(times, width_free, label="free particle")
    ax2.set(xlabel="t", ylabel=r"$\Delta x$", title="Width")
    ax2.legend()
    return fig


@demo("zeeman")
def zeeman_demo() -> Figure:
    """Zeeman effect for a p electron: from Landé splitting to the Paschen-Back limit."""
    l, xi = 1, 1.0
    B = np.linspace(0, 3, 300)
    E = atomic.zeeman_levels(l, xi, B)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(B, E, color="C0")
    for j in (0.5, 1.5):
        for mj in np.arange(-j, j + 1):
            e0 = atomic.spin_orbit_energy(l, j, xi)
            ax.plot(B[:40], e0 + atomic.lande_g(l, j) * mj * B[:40], "k:", lw=1)
    labels: dict = {}                                       # Paschen-Back levels; two coincide
    for ml, ms in atomic.basis_labels(l):
        labels.setdefault(round(B[-1] * (ml + 2 * ms) + xi * ml * ms, 6), []).append(rf"$({ml:+.0f}, {ms:+.1f})$")
    for energy, names in labels.items():
        ax.annotate(" ".join(names), (B[-1], energy), fontsize=7, xytext=(4, 0), textcoords="offset points", va="center")
    ax.text(B[-1], E.max() + 0.4, r"$(m_l, m_s)$", fontsize=8, ha="left")
    ax.set(xlabel=r"$\mu_B B / \xi$", ylabel=r"energy / $\xi$", xlim=(0, 4.1),
           title=r"$p$ electron: $\xi\,\mathbf{L\cdot S} + \mu_B B(L_z + 2S_z)$; dotted = Landé $g_J m_j \mu_B B$")
    return fig


@demo("decay-chain")
def decay_chain_demo() -> Figure:
    """A three-step decay chain: Bateman solution against a Monte Carlo of individual nuclei."""
    lambdas = [0.3, 0.8, 0.1, 0.0]
    t = np.linspace(0, 30, 301)
    N = nuclear.bateman(1.0, lambdas, t)
    rng = np.random.default_rng(0)
    counts = np.zeros((len(t), 4))
    state = np.zeros(2000, dtype=int)                       # every nucleus starts as the parent
    for k in range(len(t)):
        counts[k] = np.bincount(state, minlength=4)
        if k + 1 < len(t):
            p = 1 - np.exp(-np.array(lambdas)[state] * (t[1] - t[0]))
            state = state + (rng.random(state.size) < p)
    fig, ax = plt.subplots(figsize=(7, 4.2))
    for i, name in enumerate(["parent", "daughter 1", "daughter 2", "stable"]):
        ax.plot(t, N[:, i], color=f"C{i}", label=rf"{name} ($\lambda={lambdas[i]}$)")
        ax.plot(t[::10], counts[::10, i] / 2000, "o", color=f"C{i}", ms=3)
    ax.set(xlabel="time", ylabel="fraction of nuclei", title="Decay chain: Bateman (lines), 2000 simulated nuclei (dots)")
    ax.legend(fontsize=8)
    return fig


@demo("rlc-resonance")
def rlc_resonance_demo() -> Figure:
    """Series RLC circuit: resonance curves and the Q factor."""
    L, C, V0 = 0.05, 2e-6, 1.0
    w0 = circuits.resonant_frequency(L, C)
    w = np.linspace(0.5 * w0, 1.5 * w0, 600)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    for i, R in enumerate([5.0, 20.0, 60.0]):
        ax1.plot(w / w0, 1e3 * circuits.current_amplitude(w, V0, R, L, C), color=f"C{i}",
                 label=rf"$R = {R:g}\,\Omega$, $Q = {circuits.quality_factor(R, L, C):.0f}$")
    ax1.set(xlabel=r"$\omega/\omega_0$", ylabel="current amplitude / mA", title="Driven series RLC")
    ax1.legend(fontsize=8)
    R = 20.0
    t, _, I = circuits.rlc_series(R, L, C, V=lambda t: V0 * np.cos(w0 * t), t_max=0.08, n=4000)
    ax2.plot(1e3 * t, 1e3 * I, lw=0.8)
    amp = 1e3 * circuits.current_amplitude(w0, V0, R, L, C)
    ax2.plot(1e3 * t, amp * (1 - np.exp(-R * t / (2 * L))), "k--", lw=1, label=r"envelope $I_0(1-e^{-Rt/2L})$")
    ax2.set(xlabel="t / ms", ylabel="I / mA", title="Switching on at resonance")
    ax2.legend(fontsize=8)
    return fig


@demo("energy_drift")
def energy_drift_demo() -> Figure:
    r"""Oscillator energy drift, $E=(v^2+x^2)/2$, over twenty periods at a fixed step."""
    from . import integrators

    times = np.linspace(0, 40 * np.pi, 1601)
    def rhs(t, state):
        return [state[1], -state[0]]
    fig, ax = plt.subplots()
    for name, solver in (("Euler", integrators.euler_trajectory), ("RK4", integrators.rk4_trajectory)):
        _, state = solver(rhs, [1., 0.], times)
        ax.plot(times, np.sum(state**2, axis=1)-1, label=name)
    _, state = integrators.verlet_trajectory(lambda x: -x, [1.], [0.], times)
    ax.plot(times, np.sum(state**2, axis=1)-1, label="Velocity Verlet")
    ax.set(xlabel="Time (s)", ylabel="Relative energy error", yscale="symlog", title="Energy drift at a fixed time step")
    ax.legend()
    return fig
