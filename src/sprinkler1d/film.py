"""Quasi-1D horizontal radial film: wall friction and gas-release closures."""

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp


@dataclass
class Film:
    radius_m: np.ndarray
    velocity_ms: np.ndarray
    liquid_thickness_m: np.ndarray
    mixture_thickness_m: np.ndarray
    alpha: np.ndarray
    liquid_balance_relative: float
    energy_residual_m2s2: float


def solve(c, e, points=100, rtol=1e-8):
    if points < 2:
        raise ValueError("At least two film points required")
    r = np.linspace(c.radius_start_m, c.radius_edge_m, points)

    def gas(x):
        return c.retention * e.air_ref_m3s * np.exp(-(x - c.radius_start_m) / c.degas_length_m)

    def rhs(x, y):
        u = max(y[0], 1e-9)
        delta = (e.water_m3s + gas(x)) / (2 * np.pi * x * u)
        loss = c.friction * u * u / (2 * delta)
        return [-loss / u, loss]

    def stall(x, y):
        return y[0] - 0.05

    stall.terminal = True
    stall.direction = -1
    u0 = c.impact * e.velocity_ms
    if u0 <= 0.05:
        raise ValueError("Film below minimum supported speed")
    sol = solve_ivp(rhs, (r[0], r[-1]), [u0, 0], t_eval=r, rtol=rtol, atol=1e-10, events=stall)
    if not sol.success or sol.t.size != r.size:
        raise ValueError("Film stalls before edge")
    u = sol.y[0]
    dl = e.water_m3s / (2 * np.pi * r * u)
    dm = (e.water_m3s + gas(r)) / (2 * np.pi * r * u)
    residual = np.max(np.abs(2 * np.pi * r * u * dl / e.water_m3s - 1))
    energy = float(0.5 * u[-1] ** 2 + sol.y[1, -1] - 0.5 * u0**2)
    return Film(r, u, dl, dm, gas(r) / (e.water_m3s + gas(r)), float(residual), energy)
