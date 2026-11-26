# Migrating from 0.3

The time vector is the first result of a trajectory call. Each row of the second result is one sample. Positions precede velocities and angles use radians unless a parameter names another unit.

## Removal in 2.0

The following 0.3 interfaces remain available throughout 1.x and will be removed in 2.0.0.

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

For example, the angle of a pendulum at every saved time is available with:

```python
from qplay.mechanics import pendulum_trajectory
t, state = pendulum_trajectory(theta0=0.2)
angle = state[:, 0]
```

The earlier names still accept their 0.3 arguments and return their original shapes. They emit DeprecationWarning. Grid solvers keep their spatial axes, Monte Carlo runs keep their ensemble dimensions, and snapshot or observable helpers document their own return types. SI is the default for new dimensional physics. Existing natural-unit quantum functions, normalised N-body gravity and electrostatics retain their documented defaults. Pass G or the Coulomb constant explicitly when using those models with SI data.
