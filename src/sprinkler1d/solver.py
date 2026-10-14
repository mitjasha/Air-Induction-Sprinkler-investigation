"""Composition layer: blocks can be replaced independently by measured/CFD closures."""

from dataclasses import dataclass
from . import ejector, film, breakup, ballistics, rainfall


@dataclass
class Result:
    ejector: ejector.Ejector
    film: film.Film
    drops: breakup.Drops
    flights: list
    rain: rainfall.Rain
    warnings: list

    def summary(self):
        return {
            "status": "DEMONSTRATIVE_NOT_VALIDATED",
            "water_l_min": self.ejector.water_m3s * 60000,
            "air_ref_l_min": self.ejector.air_ref_m3s * 60000,
            "suction_absolute_pa": self.ejector.suction_pa,
            "alr": self.ejector.alr,
            "kq": self.ejector.kq,
            "d32_mm": self.drops.d32_m * 1000,
            "mean_range_m": sum(
                f.range_m * w for f, w in zip(self.flights, self.drops.volume_fraction)
            ),
            "single_head_area_cu_percent": self.rain.cu_area_percent,
            "momentum_residual_pa": self.ejector.momentum_residual_pa,
            "film_mass_residual_relative": self.film.liquid_balance_relative,
            "film_energy_residual_m2s2": self.film.energy_residual_m2s2,
            "rain_mass_residual_relative": self.rain.balance_relative,
            "hydraulic_power_w": self.ejector.hydraulic_w,
            "outlet_kinetic_power_w": self.ejector.kinetic_w,
            "warnings": self.warnings,
        }


def simulate(case, classes=32, bins=30):
    e = ejector.solve(case)
    f = film.solve(case, e)
    d = breakup.solve(case, f, classes)
    flights = [
        ballistics.fly(
            x,
            f.velocity_ms[-1],
            case.angle_deg,
            case.height_m,
            case.radius_edge_m,
            case.rho_air,
            case.rho_water,
            case.mu_air,
        )
        for x in d.diameter_m
    ]
    rain = rainfall.deposit([x.range_m for x in flights], d.volume_fraction, e.water_m3s, bins)
    warnings = [
        "Uncalibrated closures; no device-specific validation available",
        "Single-head annular CU depends on quadrature/binning; not field overlap CU",
    ]
    if max(f.mixture_thickness_m / f.radius_m) > 0.1:
        warnings.append("Thin-film assumption questionable: mixture thickness/radius > 0.1")
    if max(d.diameter_m) > 0.002:
        warnings.append("Large-drop deformation omitted; spherical drag uncertain above 2 mm")
    return Result(e, f, d, flights, rain, warnings)
