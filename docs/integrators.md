# Which integrator?

For a smooth equation of motion with a known time span, start with **solve**. Its adaptive method adjusts the internal step to meet a tolerance. The requested output sample count controls where the solution is reported.

Choose **rk4_trajectory** when comparing trajectories on a prescribed grid. For a smooth problem, halving a sufficiently small fixed step should reduce the global error by about a factor of sixteen. Check that prediction against an exact result.

Choose **verlet_trajectory** for a conservative model whose acceleration depends only on position. Use a uniform step small enough to resolve the fastest oscillation. Plot energy over many periods to distinguish bounded oscillations from accumulated drift.

Use **euler_trajectory** to study first-order error. Even the undamped harmonic oscillator gains energy under forward Euler. Run `qplay run energy_drift` to compare all three fixed-step schemes at the same step size.

## Numerical methods notebook route

1. **Classical mechanics** compares integration schemes and conserved quantities.
2. **Maths and chaos** explores convergence and sensitivity to initial conditions.
3. **Quantum mechanics** compares numerical eigenstates with exact energies.
4. **Orbitals, interference and phase space** combines the methods in larger experiments.
