"""Build the GitHub Pages site.

    python scripts/build_site.py [OUT_DIR] [--quick]

Renders every demo and animation, executes every notebook to HTML, copies the
interactive explorer, and fills ``site_src/index.html``. ``--quick`` skips the
notebooks and renders 3-frame animations (used by the test suite).
"""

from __future__ import annotations

import html
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from string import Template

import matplotlib

matplotlib.use("Agg")

import nbformat  # noqa: E402

from qplay import __version__, animations, demos, plotting  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GIF_WIDTH = 420


def _doc(fn):
    lines = (fn.__doc__ or "").strip().splitlines()
    return lines[0] if lines else ""


def notebook_info(path):
    """Title from the first '# ' heading and a summary from the next paragraph."""
    nb = nbformat.read(path, as_version=4)
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            lines = [ln.strip() for ln in cell.source.splitlines() if ln.strip()]
            if lines and lines[0].startswith("# "):
                return lines[0][2:].strip(), (lines[1] if len(lines) > 1 else "")
    return path.stem, ""


def execute_notebooks(out):
    out.mkdir(parents=True, exist_ok=True)
    env = {k: v for k, v in os.environ.items() if k != "MPLBACKEND"}  # notebooks use inline figures
    for nb in sorted((ROOT / "notebooks").glob("*.ipynb")):
        subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "html", "--execute",
                        "--output-dir", str(out), str(nb)], check=True, env=env)


def count_tests():
    res = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", str(ROOT / "tests")],
                         capture_output=True, text=True, cwd=ROOT)
    return sum(1 for line in res.stdout.splitlines() if "::" in line)


def git_commit():
    res = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, cwd=ROOT)
    return res.stdout.strip() or "unknown"


def build(out, quick=False):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    figs = out / "figures"

    cards = []
    for name in sorted(demos.DEMOS):
        demos.run(name, figs)
        doc = html.escape(_doc(demos.DEMOS[name]))
        cards.append(
            f'      <figure class="card"><a class="img" href="figures/{name}.png">'
            f'<img src="figures/{name}.png" alt="{doc}" loading="lazy"></a>'
            f"<figcaption><strong>{name}</strong><span>{doc}</span>"
            f"<code>qplay run {name}</code></figcaption></figure>")

    anims = []
    for name in sorted(animations.ANIMATIONS):
        path = animations.render(name, figs, n_frames=3 if quick else 72, fps=18)
        plotting.shrink_gif(path, GIF_WIDTH)
        doc = html.escape(_doc(animations.ANIMATIONS[name]))
        anims.append(
            f'      <figure class="card"><img src="figures/{name}.gif" alt="{doc}" loading="lazy">'
            f"<figcaption><strong>{name}</strong><span>{doc}</span>"
            f"<code>qplay animate {name}</code></figcaption></figure>")

    notebooks = []
    if not quick:
        execute_notebooks(out / "notebooks")
    for nb in sorted((ROOT / "notebooks").glob("*.ipynb")):
        title, summary = notebook_info(nb)
        notebooks.append(
            f'      <li><a href="notebooks/{nb.stem}.html">{html.escape(title)}</a>'
            f"<p>{html.escape(summary)}</p></li>")

    explorer = out / "explorer"
    explorer.mkdir(parents=True)
    shutil.copy(ROOT / "site_src" / "explorer.html", explorer / "index.html")

    page = Template((ROOT / "site_src" / "index.html").read_text()).substitute(
        version=__version__,
        gallery="\n".join(cards),
        animations="\n".join(anims),
        notebooks="\n".join(notebooks),
        n_tests=count_tests(),
        commit=git_commit(),
        built=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    )
    (out / "index.html").write_text(page)
    (out / ".nojekyll").touch()
    return out


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    print(build(args[0] if args else "_site", quick="--quick" in sys.argv))
