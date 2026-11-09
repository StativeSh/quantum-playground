r"""Symbolic mechanics with SymPy: from a Lagrangian to equations of motion to a simulation.

Euler-Lagrange: $\frac{d}{dt}\frac{\partial L}{\partial\dot q} - \frac{\partial L}{\partial q} = 0$.

Example::

    t, m, l, g = sp.symbols("t m l g", positive=True)
    th = sp.Function("theta")(t)
    L = m*l**2*sp.diff(th, t)**2/2 + m*g*l*sp.cos(th)
    rhs = to_numeric_rhs(L, [th], t, {m: 1, l: 1, g: 9.81})
    t_arr, y = integrators.solve(rhs, [1.0, 0.0], (0, 10))
"""

from __future__ import annotations

import numpy as np
import sympy as sp


def euler_lagrange(L, qs, t):
    """Euler-Lagrange expressions (each equal to zero) for coordinates ``qs(t)``."""
    return [sp.diff(sp.diff(L, sp.diff(q, t)), t) - sp.diff(L, q) for q in qs]


def accelerations(L, qs, t):
    """Solve the Euler-Lagrange equations for the accelerations $\\ddot q_i$."""
    n = len(qs)
    qdds = [sp.diff(q, t, 2) for q in qs]
    syms = sp.symbols(f"_a0:{n}")
    eqs = [e.subs(dict(zip(qdds, syms))) for e in euler_lagrange(L, qs, t)]
    sol = sp.solve(eqs, syms, dict=True)
    if not sol:
        raise ValueError("could not solve for accelerations")
    return [sp.simplify(sol[0][s]) for s in syms]


def energy_function(L, qs, t):
    """Energy function $h=\\sum\\dot q\\,\\partial L/\\partial\\dot q - L$ (the energy when $L=T-V$)."""
    qds = [sp.diff(q, t) for q in qs]
    return sp.simplify(sum(qd * sp.diff(L, qd) for qd in qds) - L)


def to_numeric_rhs(L, qs, t, params=None):
    """Turn a Lagrangian into ``rhs(t, y)`` for ``y = [q_1..q_n, qdot_1..qdot_n]``."""
    n = len(qs)
    xs = sp.symbols(f"_x0:{n}")
    vs = sp.symbols(f"_v0:{n}")
    replace = {sp.diff(q, t): v for q, v in zip(qs, vs)}
    replace.update({q: x for q, x in zip(qs, xs)})
    acc = [a.subs(params or {}).xreplace(replace) for a in accelerations(L, qs, t)]
    f = sp.lambdify([*xs, *vs], acc, "numpy")

    def rhs(_t, y):
        y = np.asarray(y, float)
        return np.concatenate([y[n:], np.asarray(f(*y), float)])

    return rhs
