"""Simple pendulum: integrate theta'' = -(g/L) sin(theta)."""
import numpy as np
from scipy.integrate import solve_ivp


def simulate(theta0=1.0, omega0=0.0, g=9.81, length=1.0, t_max=10.0, n=500):
    def rhs(_, y):
        return [y[1], -(g / length) * np.sin(y[0])]

    t = np.linspace(0, t_max, n)
    sol = solve_ivp(rhs, (0, t_max), [theta0, omega0], t_eval=t, rtol=1e-9, atol=1e-9)
    return sol.t, sol.y[0], sol.y[1]
