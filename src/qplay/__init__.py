"""qplay: a small physics and maths playground.

Modules
-------
integrators  time-stepping schemes (Euler, RK4, velocity Verlet, adaptive wrapper)
mechanics    oscillators, pendulums, projectiles, N-body gravity
waves        1D wave and heat equations, Fourier series, spectra
em           point-charge fields, Laplace solver, charged-particle motion
quantum      Schroedinger solvers (1D and 2D), tunnelling, double slit, hydrogen orbitals, spin-1/2
statmech     2D Ising model and Onsager's exact solution
relativity   Lorentz transformations and special-relativity helpers
chaos        Lorenz system, logistic map, Mandelbrot/Julia sets
symbolic     SymPy helpers: Euler-Lagrange equations, Lagrangian -> simulation
hamiltonian  Legendre transform, Hamilton's equations, Hamiltonian -> simulation
dynamics     phase portraits and fixed-point classification for 2D systems
complexplane domain colouring and the argument principle
linalg       Gram-Schmidt, power iteration, how a matrix maps the unit circle
numerics     root finding, quadrature, finite differences, Monte Carlo
plotting     figure saving and GIF helpers
demos        ready-made figures, run with ``python -m qplay run <name>``
animations   GIFs, run with ``python -m qplay animate <name>``
"""

__version__ = "0.2.0"
