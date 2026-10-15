"""Executable dimensional audit, separate from numerical SI implementation."""

import pint


def audit():
    u = pint.UnitRegistry()
    rho, v, h = 1 * u.kg / u.m**3, 1 * u.m / u.s, 1 * u.m
    q, pressure, sigma, mu = 1 * u.m**3 / u.s, 1 * u.Pa, 1 * u.N / u.m, 1 * u.Pa * u.s
    terms = {
        "nozzle_flow": (h * h * (pressure / rho) ** 0.5, "m^3/s"),
        "momentum_pressure": (rho * q * v / (h * h), "Pa"),
        "film_thickness": (q / (h * v), "m"),
        "film_acceleration": (v * v / h, "m/s^2"),
        "weber": (rho * v * v * h / sigma, "dimensionless"),
        "ohnesorge": (mu / (rho * sigma * h) ** 0.5, "dimensionless"),
        "drag_acceleration": (rho / rho * v * v / h, "m/s^2"),
        "rain_intensity": (q / h**2, "m/s"),
        "hydraulic_power": (pressure * q, "W"),
        "published_froude_squared_convention": (v**2 / ((1 * u.m / u.s**2) * h), "dimensionless"),
        "published_exponent_slope": ((1 / u.m) * h, "dimensionless"),
        "published_criterion_diameter": (
            h * (v**2 / ((1 * u.m / u.s**2) * h)) ** 0.2 * (rho * sigma * h / mu**2) ** 0.3,
            "m",
        ),
    }
    return {name: str(value.to(target).units) for name, (value, target) in terms.items()}
