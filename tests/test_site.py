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

    for placeholder in ("$version", "$gallery", "$animations", "$notebooks", "$notebooks_heading", "$n_notebooks",
                        "$n_figures", "$n_modules", "$n_tests", "$commit", "$built"):
        assert placeholder not in index
    for name in demos.DEMOS:
        assert f"figures/{name}.png" in index and (out / "figures" / f"{name}.png").exists()
    for name in animations.ANIMATIONS:
        assert f"figures/{name}.gif" in index and (out / "figures" / f"{name}.gif").exists()
    for nb in (ROOT / "notebooks").glob("*.ipynb"):
        assert f"notebooks/{nb.stem}.html" in index
    assert (out / "explorer" / "index.html").read_text().startswith("<!doctype html>")
    assert (out / ".nojekyll").exists()
    counts = re.findall(r"<dd>(\d+)</dd>", index)
    assert len(counts) == 4 and all(int(c) > 0 for c in counts), counts  # modules, figures, notebooks, tests
