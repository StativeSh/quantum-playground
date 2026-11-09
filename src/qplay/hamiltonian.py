r"""Hamiltonian mechanics with SymPy.

Hamilton's equations: $\dot q_i = \frac{\partial H}{\partial p_i}$, $\dot p_i = -\frac{\partial H}{\partial q_i}$.
Legendre transform: $p_i = \frac{\partial L}{\partial \dot q_i}$, $H = \sum_i p_i\dot q_i - L$.

Here ``qs`` and ``ps`` are plain SymPy symbols (not functions of time).
"""

from __future__ import annotations

import numpy as np
import sympy as sp


def hamilton_equations(H, qs, ps):
    """Return ``(qdot, pdot)`` as lists of SymPy expressions."""
    return [sp.diff(H, p) for p in ps], [-sp.diff(H, q) for q in qs]


def legendre_transform(L, qs_t, t):
    """Hamiltonian from a Lagrangian written with coordinates ``q(t)``.

    Returns ``(H, qs, ps)`` where ``qs = q0, q1, ...`` and ``ps = p0, p1, ...`` are new symbols.
    """
    n = len(qs_t)
    qs, ps, vs = sp.symbols(f"q0:{n}"), sp.symbols(f"p0:{n}"), sp.symbols(f"_v0:{n}")
    replace = {sp.diff(q, t): v for q, v in zip(qs_t, vs)}
    replace.update(dict(zip(qs_t, qs)))
    Lx = L.xreplace(replace)
    momenta = [sp.Eq(p, sp.diff(Lx, v)) for p, v in zip(ps, vs)]
    sol = sp.solve(momenta, vs, dict=True)
    if not sol:
        raise ValueError("could not invert the momenta for the velocities")
    H = sum(p * v for p, v in zip(ps, vs)) - Lx
    return sp.simplify(H.subs(sol[0])), qs, ps


def to_numeric_rhs(H, qs, ps, params=None):
    """``rhs(t, y)`` for ``y = [q_1..q_n, p_1..p_n]``, ready for ``integrators.solve``."""
    qdot, pdot = hamilton_equations(H, qs, ps)
    exprs = [sp.sympify(e).subs(params or {}) for e in qdot + pdot]
    f = sp.lambdify([*qs, *ps], exprs, "numpy")

    def rhs(_t, y):
        return np.array(f(*np.asarray(y, float)), dtype=float)

    return rhs


def to_numeric_energy(H, qs, ps, params=None):
    """Vectorised ``energy(y)`` for a history ``y`` with columns ``q..., p...``."""
    f = sp.lambdify([*qs, *ps], sp.sympify(H).subs(params or {}), "numpy")

    def energy(y):
        y = np.asarray(y, float)
        return np.broadcast_to(f(*y.T), y.shape[:-1]) if y.ndim > 1 else f(*y)

    return energy
