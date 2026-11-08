"""Figure helpers. Honour ``MPLBACKEND`` so everything works headless."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt


def setup_style():
    plt.rcParams.update({
        "figure.dpi": 110,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "mathtext.fontset": "cm",
    })


def save(fig, name, outdir="figures", dpi=150):
    """Save ``fig`` as ``<outdir>/<name>.png``, close it, and return the path."""
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{name}.png"
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
    return path


def save_gif(fig, update, frames, path, fps=30):
    """Animate ``update(frame)`` over ``frames`` and write a GIF to ``path``."""
    from matplotlib.animation import FuncAnimation, PillowWriter

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    FuncAnimation(fig, update, frames=frames, blit=False).save(path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    return path


setup_style()
