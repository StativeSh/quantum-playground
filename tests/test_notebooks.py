"""Structural checks on notebooks and lessons (they are executed separately by `make notebooks-check`)."""
import importlib.util
import re
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


def _deprecated_names():
    """Functions kept only for 0.3 compatibility; their docstrings start "Compatibility interface"."""
    import importlib

    import qplay
    names = set()
    for module_name in (m for m in qplay.__all__ if m != "__version__"):
        module = importlib.import_module(f"qplay.{module_name}")
        for name in getattr(module, "__all__", []):
            doc = getattr(getattr(module, name), "__doc__", None) or ""
            if callable(getattr(module, name)) and doc.startswith("Compatibility interface"):
                names.add(name)
    return names


def test_notebooks_use_the_current_api():
    deprecated = _deprecated_names()
    assert {"rc_circuit", "projectile", "nbody", "velocity_verlet"} <= deprecated
    call = re.compile(r"\.(" + "|".join(sorted(deprecated)) + r")\(")
    for path in NOTEBOOKS:
        for cell in nbformat.read(path, as_version=4).cells:
            if cell.cell_type == "code":
                found = call.search(cell.source)
                assert not found, f"{path.name} calls deprecated {found.group(1)}(); use the *_trajectory function"


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


PREDICT = re.compile(r"^\*\*Predict \(P(\d+)\)\.\*\* ")
EXPLAIN = re.compile(r"^\*\*Explain \(P(\d+)\)\.\*\* ")


def predict_explain_structure(cells):
    """Problems with a lesson's predict-run-explain prompts (empty list if they are well formed)."""
    problems, numbers = [], []
    for i, cell in enumerate(cells):
        m = PREDICT.match(cell.source) if cell.cell_type == "markdown" else None
        if not m:
            continue
        n = int(m.group(1))
        numbers.append(n)
        nxt = cells[i + 1] if i + 1 < len(cells) else None
        after = cells[i + 2] if i + 2 < len(cells) else None
        if nxt is None or nxt.cell_type != "code":
            problems.append(f"P{n}: the Predict box must come straight before the experiment's code cell")
        if after is None or after.cell_type != "markdown" or not (EXPLAIN.match(after.source) and EXPLAIN.match(after.source).group(1) == str(n)):
            problems.append(f"P{n}: an Explain (P{n}) box must follow the experiment's code cell")
    if len(numbers) < 2:
        problems.append(f"needs at least two Predict boxes, found {len(numbers)}")
    if numbers != list(range(1, len(numbers) + 1)):
        problems.append(f"Predict boxes must be numbered P1, P2, ... in order, found {numbers}")
    text = "\n".join(c.source for c in cells)
    solutions = text.split("## Worked solutions", 1)[-1]
    if "### Predict and explain: answers" not in solutions:
        problems.append("missing '### Predict and explain: answers' after the worked solutions")
    for n in numbers:
        if f"**P{n}.**" not in solutions.split("### Predict and explain: answers", 1)[-1]:
            problems.append(f"no answer for P{n}")
    return problems


@pytest.mark.parametrize("path", sorted(ROOT.glob("lessons/*.ipynb")), ids=lambda p: p.name)
def test_lessons_have_predict_run_explain_prompts(path):
    """Before key experiments students commit to a prediction, run it, then explain; answers come at the end."""
    assert predict_explain_structure(nbformat.read(path, as_version=4).cells) == []


def test_predict_explain_checker_catches_mistakes():
    md, code = nbformat.v4.new_markdown_cell, nbformat.v4.new_code_cell
    good = [md("**Predict (P1).** a?"), code("x = 1"), md("**Explain (P1).** why?"),
            md("**Predict (P2).** b?"), code("y = 2"), md("**Explain (P2).** why?"),
            md("## Worked solutions"), md("### Predict and explain: answers\n\n**P1.** a\n\n**P2.** b")]
    assert predict_explain_structure(good) == []
    assert any("straight before" in p for p in predict_explain_structure([good[0], good[2]] + good[3:]))
    assert any("Explain (P2)" in p for p in predict_explain_structure(good[:5] + good[6:]))
    assert any("no answer for P2" in p for p in predict_explain_structure(good[:7] + [md("### Predict and explain: answers\n\n**P1.** a")]))
    assert any("at least two" in p for p in predict_explain_structure(good[:3] + good[6:]))
