"""Explicitly unvalidated dimensionless breakup closure and volume quadrature."""

from dataclasses import dataclass
import numpy as np
from scipy.special import ndtri


@dataclass
class Drops:
    d32_m: float
    diameter_m: np.ndarray
    volume_fraction: np.ndarray
    we_liquid: float
    we_air: float
    oh: float


def solve(c, film, classes=32):
    if classes < 2:
        raise ValueError("At least two diameter classes required")
    h, u, a = film.liquid_thickness_m[-1], film.velocity_ms[-1], film.alpha[-1]
    we = c.rho_water * u * u * h / c.sigma
    wea = c.rho_air * u * u * h / c.sigma
    oh = c.mu_water / np.sqrt(c.rho_water * c.sigma * h)
    d32 = c.breakup_c * h * we**c.breakup_we_exp * (1 - a) ** c.breakup_air_exp
    if not 1e-5 <= d32 <= 0.01:
        raise ValueError("d32 outside computational envelope [10 um, 10 mm]")
    # Equal-volume quantiles, then enforce the discrete Sauter mean exactly.
    raw = np.exp(c.log_sigma * ndtri((np.arange(classes) + 0.5) / classes))
    weights = np.full(classes, 1 / classes)
    d = raw * d32 * np.sum(weights / raw)
    return Drops(float(d32), d, weights, float(we), float(wea), float(oh))
