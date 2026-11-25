# Changelog

## 1.0.1

Lessons 1, 2, 3, 6 and 11, the demos and the figure-eight animation now use the 1.0 trajectory functions, so learners no longer see deprecation warnings. Lessons 1–11 upgrade an older installation, as lessons 12–17 already did. The test suite fails if repository code calls a deprecated name.

`binding_energy_per_nucleon` accepts integer arrays, so a whole binding-energy curve takes one call. The energy drift demo is now `energy-drift`, matching the other demo names; `qplay run energy_drift` still works. The `refraction` error message now states the allowed angle range. Python 3.10 is tested with current dependencies as well as the oldest supported ones.

## 1.0.0 release series

Six new lessons cover momentum, gravity, induction, optics, thermal transfer and binding energy. The explorer adds rotating-coil and diffraction-grating experiments. The energy drift demo compares Euler, RK4 and velocity Verlet on one oscillator.

Public modules declare their supported names in `__all__`. Typed trajectory functions return time and a state matrix. Older unpacking conventions remain available through deprecated wrappers during 1.x.

| Earlier call | Preferred call | State columns |
|---|---|---|
| `integrators.euler` | `integrators.euler_trajectory` | solution components |
| `integrators.rk4` | `integrators.rk4_trajectory` | solution components |
| `integrators.velocity_verlet` | `integrators.verlet_trajectory` | positions then velocities |
| `mechanics.pendulum` | `mechanics.pendulum_trajectory` | angle and angular velocity |
| `mechanics.harmonic_oscillator` | `mechanics.oscillator_trajectory` | displacement and velocity |
| `mechanics.projectile` | `mechanics.projectile_trajectory` | x, y, vx, vy |
| `mechanics.nbody` | `mechanics.nbody_trajectory` | flattened positions followed by flattened velocities in body order |
| `em.charged_particle` | `em.particle_trajectory` | x, y, z, vx, vy, vz |
| `circuits.rc_circuit` | `circuits.rc_trajectory` | charge and current |
| `circuits.rlc_series` | `circuits.rlc_trajectory` | charge and current |

## 0.3.1

Improved the accuracy of decay-chain populations with nearly equal rates, preserved complex initial states in adaptive integration, corrected DC and Nyquist amplitudes, and cross-checked supplied starting vectors in power iteration. Releases now smoke-test the built wheel with a lesson.

## 0.3.0

Published the Python package, CLI, simulation gallery and notebook course.
