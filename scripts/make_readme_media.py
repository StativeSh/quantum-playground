"""Render the images and GIFs shown in README.md into docs/images.

Run with ``make readme-media``. GIFs are downscaled so the repository stays small.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from qplay import animations, demos, plotting  # noqa: E402

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "docs/images")
FIGURES = ["double-slit", "hydrogen", "ising", "phase-portrait", "mandelbrot", "domain-coloring"]
GIFS = {  # name: (frames, fps, output width in px)
    "double-pendulum": (72, 18, 360),
    "figure-eight": (72, 18, 420),
    "wavepacket": (72, 18, 520),
    "double-slit": (36, 10, 320),
}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name in FIGURES:
        print(demos.run(name, OUT))
    for name, (n_frames, fps, width) in GIFS.items():
        path = animations.render(name, OUT, n_frames=n_frames, fps=fps)
        plotting.shrink_gif(path, width)
        print(path, f"{path.stat().st_size / 1e6:.2f} MB")


if __name__ == "__main__":
    main()
