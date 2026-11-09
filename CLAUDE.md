# quantum-playground

Physics and maths playground: a small Python package (`qplay`) plus notebooks.

## Commands

- Install: `make install` (venv in `.venv`, editable install with dev extras)
- Test: `make test` (about 45 s)
- Render all demo figures: `make demos`; all GIFs: `make animations` (both write `figures/`, gitignored)
- Check notebooks run end to end: `make notebooks-check`
- Website: `make site` builds `_site/` (deployed by `.github/workflows/pages.yml` on push to `main`); README images: `make readme-media` writes `docs/images/`

## Layout

- `src/qplay/` one module per topic: `mechanics`, `waves`, `em`, `quantum`, `relativity`, `chaos`, `statmech`, `symbolic`, `hamiltonian`, `dynamics`, `complexplane`, `linalg`, `numerics`, plus `integrators`, `plotting`, `demos`, `animations`
- `tests/` one test file per area; tests check numerics against analytic results
- `notebooks/` committed without outputs
- `scripts/` site and README-media builders; `site_src/` landing-page template (`string.Template`, so a literal `$` is written `$$`) and the standalone explorer page

## Conventions

- Put the governing equation in each module or function docstring, in LaTeX (raw strings, `r"""`).
- Quantum code uses natural units ($\hbar = m = 1$) unless a function takes `hbar`/`m`.
- Time histories have shape `(n_times, n_dim)`; grids are uniform `numpy` arrays.
- Every new function gets a test against a known analytic result, a conservation law or a limiting case. Do not assert against the code's own output.
- New demos: decorate a function with `@demo("name")` in `demos.py`; new GIFs: `@animation("name")` in `animations.py`, taking `n_frames` and returning `(fig, update, frames)`. `tests/test_demos.py` picks both up automatically.
- Do not set a matplotlib backend in library code; honour `MPLBACKEND`. Notebooks start with `%matplotlib inline`.
- Beware cancellation: for example, use $\gamma - 1 = \beta^2\gamma^2/(\gamma+1)$ rather than `gamma - 1` at low speed.
- Split-step solvers use a periodic box: add `quantum.absorbing_layer` to the potential whenever waves would reach an edge, or they wrap around and corrupt the result.
- Resolve barriers on the grid: a one-cell wall of huge height leaks in the split-step method. Use several cells and a height well above the packet energy, and check by running with the openings closed.
- Recent NumPy returns a complex dtype from `np.linalg.eig` even when the eigenvalues are real; take `.real` explicitly after checking.
