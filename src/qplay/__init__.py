"""qplay: a small physics and maths playground.

Modules
-------
integrators  time-stepping schemes (Euler, RK4, velocity Verlet, adaptive wrapper)
mechanics    oscillators, pendulums, projectiles, N-body gravity
waves        1D wave and heat equations, Fourier series, spectra
em           point-charge fields, Laplace solver, charged-particle motion
quantum      Schroedinger solvers, tunnelling, hydrogen levels, spin-1/2
relativity   Lorentz transformations and special-relativity helpers
chaos        Lorenz system, logistic map, Mandelbrot/Julia sets
symbolic     SymPy helpers: Euler-Lagrange equations, Lagrangian -> simulation
numerics     root finding, quadrature, finite differences, Monte Carlo
plotting     figure saving and GIF helpers
demos        ready-made figures, run with ``python -m qplay run <name>``
"""

__version__ = "0.1.0"
