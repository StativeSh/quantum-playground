"""Heating and cooling in SI units."""
import numpy as np
from numpy.typing import ArrayLike, NDArray

__all__ = [
    "heating_curve", "cooling",
]


def heating_curve(heat: ArrayLike, mass: float, start: float, melting: float,
                  solid_capacity: float, latent_heat: float, liquid_capacity: float) -> NDArray[np.float64]:
    r"""Temperature during heating through fusion, $Q=mc\Delta T$ and $Q_f=mL_f$.

    Temperatures use kelvin, heat is in joules and capacities in J/(kg K).
    The two-phase model ends before boiling.
    """
    q = np.asarray(heat, float)
    if min(mass, solid_capacity, latent_heat, liquid_capacity) <= 0 or start > melting or np.any(q < 0):
        raise ValueError("require positive material constants and heating from below melting")
    onset = mass * solid_capacity * (melting - start)
    end = onset + mass * latent_heat
    return start + np.minimum(q, onset) / (mass * solid_capacity) + np.maximum(q-end, 0) / (mass*liquid_capacity)


def cooling(time: ArrayLike, initial: float, ambient: float, rate: float) -> NDArray[np.float64]:
    r"""Newton cooling with constant surroundings, $T=T_a+(T_i-T_a)e^{-kt}$, with $k$ in inverse seconds."""
    if rate < 0:
        raise ValueError("rate must be nonnegative")
    return ambient + (initial - ambient) * np.exp(-rate * np.asarray(time, float))
