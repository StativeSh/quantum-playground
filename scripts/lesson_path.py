"""The lesson learning path: prerequisites and routes, read from ``lessons/path.json``.

    python scripts/lesson_path.py          check every lesson header matches path.json
    python scripts/lesson_path.py --write  rewrite the "Before this lesson" / "Leads to" lines

The site builder and the tests import this module, so path.json is the single source.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
LESSONS = ROOT / "lessons"
BEFORE, LEADS = "**Before this lesson:**", "**Leads to:**"


def load():
    return json.loads((LESSONS / "path.json").read_text())


def lesson_files():
    """``{"01": Path(...), ...}`` for every lesson notebook."""
    return {p.name[:2]: p for p in sorted(LESSONS.glob("[0-9][0-9]_*.ipynb"))}


def title(path):
    first = nbformat.read(path, as_version=4).cells[0].source.splitlines()[0]
    return re.sub(r"^#\s*Lesson\s+\d+\s*[·.:-]\s*", "", first).strip()


def problems(path_data=None):
    """Everything inconsistent in path.json, as a list of messages (empty when all is well)."""
    data = path_data or load()
    files, lessons, out = lesson_files(), data["lessons"], []
    for num in files:
        if num not in lessons:
            out.append(f"lesson {num} is missing from path.json")
    for num, info in lessons.items():
        if num not in files:
            out.append(f"path.json lists lesson {num}, which does not exist")
        for dep in info["builds_on"]:
            if dep["lesson"] not in files:
                out.append(f"lesson {num} builds on missing lesson {dep['lesson']}")
            elif dep["lesson"] >= num:
                out.append(f"lesson {num} builds on lesson {dep['lesson']}, which does not come before it")
    for track in data["tracks"]:
        seen = set()
        for num in track["lessons"]:
            if num not in files:
                out.append(f"track {track['name']!r} lists missing lesson {num}")
                continue
            for dep in lessons.get(num, {}).get("builds_on", []):
                if dep["lesson"] in track["lessons"] and dep["lesson"] not in seen:
                    out.append(f"track {track['name']!r} puts lesson {num} before its prerequisite {dep['lesson']}")
            seen.add(num)
    return out


def leads_to(num, data=None):
    data = data or load()
    return sorted(n for n, info in data["lessons"].items() if any(d["lesson"] == num for d in info["builds_on"]))


def header_lines(num, data=None):
    """The two markdown lines that go in lesson ``num``'s first cell."""
    data = data or load()
    files, info = lesson_files(), data["lessons"][num]
    if info["builds_on"]:
        deps = "; ".join(f"Lesson {int(d['lesson'])}, *{title(files[d['lesson']])}* ({d['for']})" for d in info["builds_on"])
        before = f"{BEFORE} {deps}. Also assumed: {info['assumes']}."
    else:
        before = f"{BEFORE} none of the other lessons. Assumed: {info['assumes']}."
    after = leads_to(num, data)
    lead = f"{LEADS} " + ("; ".join(f"Lesson {int(n)}, *{title(files[n])}*" for n in after) + "." if after else "the end of this route for now.")
    return before, lead


def sync(write=False):
    """Bring every lesson's header in line with path.json. Returns the files that differ."""
    data, changed = load(), []
    for num, path in lesson_files().items():
        nb = nbformat.read(path, as_version=4)
        cell = nb.cells[0]
        before, lead = header_lines(num, data)
        lines = [ln for ln in cell.source.split("\n\n") if not ln.startswith((BEFORE, LEADS))]
        at = next(i for i, ln in enumerate(lines) if ln.startswith("**You will be able to:**"))
        new = "\n\n".join(lines[:at] + [before, lead] + lines[at:])
        if new != cell.source:
            changed.append(path)
            if write:
                cell.source = new
                nbformat.write(nb, path)
    return changed


if __name__ == "__main__":
    issues = problems()
    for msg in issues:
        print("path.json:", msg)
    stale = sync(write="--write" in sys.argv)
    for path in stale:
        print(("updated " if "--write" in sys.argv else "out of date: ") + path.name)
    sys.exit(1 if issues or (stale and "--write" not in sys.argv) else 0)
