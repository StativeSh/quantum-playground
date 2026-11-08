# quantum-playground

Physics and maths playground: a small Python package (`qplay`) plus notebooks.

## Commands

- Install: `make install` (venv in `.venv`, editable install with dev extras)
- Test: `make test` (about 8 s)
- Render all demo figures: `make demos` (writes `figures/`, gitignored)
- Check notebooks run end to end: `make notebooks-check`

## Layout

- `src/qplay/` one module per topic: `mechanics`, `waves`, `em`, `quantum`, `relativity`, `chaos`, `symbolic`, `numerics`, plus `integrators`, `plotting`, `demos`
- `tests/` one test file per area; tests check numerics against analytic results
- `notebooks/` committed without outputs

## Conventions

- Put the governing equation in each module or function docstring, in LaTeX (raw strings, `r"""`).
- Quantum code uses natural units ($\hbar = m = 1$) unless a function takes `hbar`/`m`.
- Time histories have shape `(n_times, n_dim)`; grids are uniform `numpy` arrays.
- Every new function gets a test against a known analytic result, a conservation law or a limiting case. Do not assert against the code's own output.
- New demos: decorate a function with `@demo("name")` in `demos.py`; `tests/test_demos.py` picks it up automatically.
- Do not set a matplotlib backend in library code; honour `MPLBACKEND`. Notebooks start with `%matplotlib inline`.
- Beware cancellation: for example, use $\gamma - 1 = \beta^2\gamma^2/(\gamma+1)$ rather than `gamma - 1` at low speed.
