# quantum-playground

A physics and maths playground: simulations, symbolic maths and notebooks in Python + Jupyter.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/jupyter lab
```

## Layout

- `src/` reusable simulation code (start with `pendulum.py`)
- `notebooks/` Jupyter notebooks
- `tests/` run with `.venv/bin/pytest`
