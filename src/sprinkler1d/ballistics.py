"""2D radial/vertical trajectories in still air, spherical-drag approximation."""

from dataclasses import dataclass
import numpy as np
from scipy.integrate import solve_ivp


@dataclass
class Flight:
    range_m: float
    time_s: float
    path: np.ndarray


def drag_cd(re):
    if re <= 0:
        raise ValueError("Reynolds number must be positive")
    return 24 / re * (1 + 0.15 * re**0.687) if re < 1000 else 0.44


def fly(
    diameter,
    speed,
    angle_deg,
    height,
    radius=0.0,
    rho_air=1.204,
    rho_water=998.2,
    mu_air=1.81e-5,
    gravity=9.80665,
    drag=True,
    rtol=1e-7,
):
    values = [diameter, speed, angle_deg, height, radius, rho_air, rho_water, mu_air, gravity, rtol]
    if (
        not all(np.isfinite(values))
        or min(diameter, height, rho_water, mu_air, gravity, rtol) <= 0
        or min(speed, radius, rho_air) < 0
    ):
        raise ValueError("Invalid trajectory inputs")
    theta = np.deg2rad(angle_deg)

    def rhs(t, y):
        v = np.hypot(y[2], y[3])
        k = 0.0
        if drag and v > 0 and rho_air > 0:
            re = rho_air * v * diameter / mu_air
            k = 3 * rho_air * drag_cd(re) * v / (4 * rho_water * diameter)
        return [y[2], y[3], -k * y[2], -gravity - k * y[3]]

    def ground(t, y):
        return y[1]

    ground.terminal = True
    ground.direction = -1
    sol = solve_ivp(
        rhs,
        (0, 120),
        [radius, height, speed * np.cos(theta), speed * np.sin(theta)],
        events=ground,
        rtol=rtol,
        atol=1e-9,
        max_step=0.1,
    )
    if not sol.success or not len(sol.t_events[0]):
        raise ValueError("Trajectory did not reach ground within 120 s")
    return Flight(float(sol.y_events[0][0, 0]), float(sol.t_events[0][0]), sol.y[:2].T)
