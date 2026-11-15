"""Structural checks on notebooks and lessons (they are executed separately by `make notebooks-check`)."""
import importlib.util
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
    assert '"quantum-playground"' in code[0].source, "install the released package from PyPI (pip install quantum-playground)"
    assert all(not c.outputs and c.execution_count is None for c in code), "commit notebooks without outputs"


def test_lessons_have_exercises_and_solutions():
    lessons = sorted(ROOT.glob("lessons/*.ipynb"))
    assert lessons
    for path in lessons:
        text = "\n".join(c.source for c in nbformat.read(path, as_version=4).cells)
        assert "## Exercises" in text and "## Worked solutions" in text, path.name
        assert "You will be able to" in text, path.name


def _lesson_path():
    spec = importlib.util.spec_from_file_location("lesson_path", ROOT / "scripts" / "lesson_path.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_learning_path_is_consistent():
    """Every lesson is in lessons/path.json, prerequisites come earlier, and routes respect them."""
    assert _lesson_path().problems() == []


def test_lesson_headers_match_learning_path():
    stale = _lesson_path().sync(write=False)
    assert not stale, f"run `python scripts/lesson_path.py --write`: {[p.name for p in stale]} out of date"


def test_learning_path_checker_catches_mistakes():
    lp = _lesson_path()
    data = lp.load()
    data["lessons"]["03"]["builds_on"].append({"lesson": "07", "for": "nothing"})       # a later lesson
    data["tracks"].append({"name": "backwards", "lessons": ["05", "03"]})
    found = lp.problems(data)
    assert any("does not come before it" in m for m in found)
    assert any("before its prerequisite" in m for m in found)
