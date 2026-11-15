# quantum-playground

Physics and maths playground: a small Python package (`qplay`) plus notebooks.

## Commands

- Install: `make install` (venv in `.venv`, editable install with dev extras)
- Test: `make test` skips tests marked `@pytest.mark.slow` (about 20 s); `make test-all` runs everything as CI does; `make coverage` adds a coverage report (fails under 95%)
- Render all demo figures: `make demos`; all GIFs: `make animations` (both write `figures/`, gitignored)
- Check notebooks run end to end: `make notebooks-check`
- Website: `make site` builds `_site/`, including the pdoc API reference in `_site/api` (`make api` builds only that); deployed by `.github/workflows/pages.yml` on push to `main`. README images: `make readme-media` writes `docs/images/`
- Release: the distribution is `quantum-playground` (import name `qplay`). Bump `version` in `pyproject.toml` and `__version__` in `src/qplay/__init__.py` together (a test checks they match), then push a tag `vX.Y.Z`; `.github/workflows/release.yml` publishes to PyPI

## Layout

- `src/qplay/` one module per topic: `mechanics`, `waves`, `em`, `quantum`, `atomic`, `kinetic`, `nuclear`, `circuits`, `relativity`, `chaos`, `statmech`, `symbolic`, `hamiltonian`, `dynamics`, `complexplane`, `linalg`, `numerics`, plus `integrators`, `plotting`, `demos`, `animations`
- `tests/` one test file per area; tests check numerics against analytic results
- `notebooks/` and `lessons/` committed without outputs; both are executed by `make notebooks-check`, CI and the site build
- `scripts/` site and README-media builders; `site_src/` landing-page template (`string.Template`, so a literal `$` is written `$$`) and the standalone explorer page (plain JS on canvas; its experiments share one `requestAnimationFrame` loop via `registerSim`)

## Conventions

- Put the governing equation in each module or function docstring, in LaTeX (raw strings, `r"""`).
- Quantum code uses natural units ($\hbar = m = 1$) unless a function takes `hbar`/`m`.
- Time histories have shape `(n_times, n_dim)`; grids are uniform `numpy` arrays.
- Every new function gets a test against a known analytic result, a conservation law or a limiting case. Do not assert against the code's own output.
- Mark a test `@pytest.mark.slow` if it takes more than about 1.5 s (in `tests/test_demos.py`, add the name to `SLOW_DEMOS` or `SLOW_ANIMATIONS`).
- New demos: decorate a function with `@demo("name")` in `demos.py`; new GIFs: `@animation("name")` in `animations.py`, taking `n_frames` and returning `(fig, update, frames)`. `tests/test_demos.py` picks both up automatically.
- Do not set a matplotlib backend in library code; honour `MPLBACKEND`. Notebooks start with `%matplotlib inline`.
- Beware cancellation: for example, use $\gamma - 1 = \beta^2\gamma^2/(\gamma+1)$ rather than `gamma - 1` at low speed.
- Split-step solvers use a periodic box: add `quantum.absorbing_layer` to the potential whenever waves would reach an edge, or they wrap around and corrupt the result.
- Resolve barriers on the grid: a one-cell wall of huge height leaks in the split-step method. Use several cells and a height well above the packet energy, and check by running with the openings closed.
- Recent NumPy returns a complex dtype from `np.linalg.eig` even when the eigenvalues are real; take `.real` explicitly after checking.
- Every notebook and lesson starts with an Open in Colab badge in its first cell, and its first code cell installs `qplay` from PyPI (`pip install quantum-playground`) when it is missing. `tests/test_notebooks.py` enforces both.
- Because Colab installs the **released** package, a notebook or lesson that uses code not yet on PyPI fails there even though CI passes. Release a new version before (or together with) merging such a notebook.
- Every lesson is listed in `lessons/path.json` with what it `builds_on` (earlier lessons only, each with a reason) and appears in at least one route under `tracks`. After editing it, run `python scripts/lesson_path.py --write` to refresh the "Before this lesson" and "Leads to" lines in the lesson headers; `tests/test_notebooks.py` fails if they drift.
- Explorer changes need a behavioural test in `tests/test_explorer.py` (Playwright): set sliders with `set_slider`, compare readouts with the Python package or an analytic result. `make test-browser` runs them.
- Lessons (`lessons/NN_topic.ipynb`) target A-level and IB: state the specification points and "You will be able to" objectives up front, end with `## Exercises` and `## Worked solutions`, and compute every exercise answer in code rather than typing numbers in.
