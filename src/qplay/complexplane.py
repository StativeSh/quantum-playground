r"""Complex functions: domain colouring and the argument principle.

Argument principle: $\frac{1}{2\pi i}\oint_C \frac{f'(z)}{f(z)}\,dz = N_{\text{zeros}} - N_{\text{poles}}$ inside $C$,
which equals the number of times $f(C)$ winds around $0$.
"""

from __future__ import annotations

import numpy as np
from matplotlib.colors import hsv_to_rgb


def complex_grid(xlim=(-2, 2), ylim=(-2, 2), n=500):
    X, Y = np.meshgrid(np.linspace(*xlim, n), np.linspace(*ylim, n))
    return X + 1j * Y


def domain_coloring(f, xlim=(-2, 2), ylim=(-2, 2), n=500):
    """RGB image of ``f``: hue shows $\\arg f$ (red = positive real), brightness bands show $\\log_2|f|$.

    Returns an array of shape ``(n, n, 3)`` with row 0 at ``ylim[0]`` (use ``origin="lower"``).
    """
    with np.errstate(all="ignore"):
        w = f(complex_grid(xlim, ylim, n))
        hue = (np.angle(w) / (2 * np.pi)) % 1.0
        bands = np.log2(np.abs(w)) % 1.0
    bad = ~np.isfinite(w)
    value = np.where(bad, 1.0, 0.55 + 0.45 * np.nan_to_num(bands))
    sat = np.where(bad, 0.0, 0.85)
    return hsv_to_rgb(np.stack([np.nan_to_num(hue), sat, value], axis=-1))


def winding_number(f, center=0.0, radius=1.0, n=4000):
    """How many times ``f`` maps the circle ``|z - center| = radius`` around the origin.

    By the argument principle this is (zeros - poles) inside the circle, counted with multiplicity.
    The circle must not pass through a zero or pole.
    """
    theta = np.linspace(0, 2 * np.pi, n + 1)
    w = f(center + radius * np.exp(1j * theta))
    return int(round(np.sum(np.diff(np.unwrap(np.angle(w)))) / (2 * np.pi)))
