import importlib.util
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_site_builds_with_every_page_and_asset(tmp_path):
    """One quick build (no notebook execution, 3-frame GIFs) checked end to end."""
    from qplay import animations, demos

    out = load_builder().build(tmp_path / "site", quick=True)
    index = (out / "index.html").read_text()

    for placeholder in ("$version", "$gallery", "$animations", "$notebooks", "$lessons", "$notebooks_heading", "$n_notebooks",
                        "$n_figures", "$n_modules", "$n_tests", "$commit", "$built"):
        assert placeholder not in index
    for name in demos.DEMOS:
        assert f"figures/{name}.png" in index and (out / "figures" / f"{name}.png").exists()
    for name in animations.ANIMATIONS:
        assert f"figures/{name}.gif" in index and (out / "figures" / f"{name}.gif").exists()
    for folder in ("notebooks", "lessons"):
        for nb in (ROOT / folder).glob("*.ipynb"):
            assert f"{folder}/{nb.stem}.html" in index
            assert f"colab.research.google.com/github/StativeSh/quantum-playground/blob/main/{folder}/{nb.name}" in index
    assert (out / "explorer" / "index.html").read_text().startswith("<!doctype html>")
    assert (out / ".nojekyll").exists()
    counts = re.findall(r"<dd>(\d+)</dd>", index)
    assert len(counts) == 4 and all(int(c) > 0 for c in counts), counts  # modules, figures, notebooks, tests
