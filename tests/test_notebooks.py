"""Structural checks on notebooks and lessons (they are executed separately by `make notebooks-check`)."""
from pathlib import Path

import nbformat
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted(ROOT.glob("notebooks/*.ipynb")) + sorted(ROOT.glob("lessons/*.ipynb"))


@pytest.mark.parametrize("path", NOTEBOOKS, ids=lambda p: p.name)
def test_notebook_opens_in_colab_and_is_committed_clean(path):
    nb = nbformat.read(path, as_version=4)
    rel = path.relative_to(ROOT).as_posix()
    assert f"colab.research.google.com/github/StativeSh/quantum-playground/blob/main/{rel}" in nb.cells[0].source
    code = [c for c in nb.cells if c.cell_type == "code"]
    assert 'find_spec("qplay")' in code[0].source, "first code cell must install qplay when it is missing"
    assert all(not c.outputs and c.execution_count is None for c in code), "commit notebooks without outputs"


def test_lessons_have_exercises_and_solutions():
    lessons = sorted(ROOT.glob("lessons/*.ipynb"))
    assert lessons
    for path in lessons:
        text = "\n".join(c.source for c in nbformat.read(path, as_version=4).cells)
        assert "## Exercises" in text and "## Worked solutions" in text, path.name
        assert "You will be able to" in text, path.name
