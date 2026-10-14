"""Typed SI inputs and explicit supported domain (not a validated envelope)."""

from dataclasses import dataclass, asdict
import json
import math


@dataclass(frozen=True)
class Case:
    pressure_pa: float = 200000.0  # gauge inlet pressure
    nozzle_m: float = 0.004
    mixing_m: float = 0.008
    air_area_m2: float = 1e-6
    radius_start_m: float = 0.010
    radius_edge_m: float = 0.025
    height_m: float = 1.5
    angle_deg: float = 25.0
    cd_water: float = 0.92
    cd_air: float = 0.70
    mixing_loss: float = 0.20
    impact: float = 0.85
    friction: float = 0.003
    retention: float = 0.30
    degas_length_m: float = 0.03
    breakup_c: float = 6.0
    breakup_we_exp: float = -0.20
    breakup_air_exp: float = 0.50
    log_sigma: float = 0.35
    rho_water: float = 998.2
    mu_water: float = 0.001002
    sigma: float = 0.0728
    pressure_atm_pa: float = 101325.0
    temperature_k: float = 293.15
    mu_air: float = 1.81e-5
    vapor_pressure_pa: float = 2339.0

    def __post_init__(self):
        for key, value in asdict(self).items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
            ):
                raise ValueError(f"{key} must be a finite number in SI units")
        positive = [
            "pressure_pa",
            "nozzle_m",
            "mixing_m",
            "radius_start_m",
            "radius_edge_m",
            "height_m",
            "degas_length_m",
            "breakup_c",
            "rho_water",
            "mu_water",
            "sigma",
            "pressure_atm_pa",
            "temperature_k",
            "mu_air",
            "vapor_pressure_pa",
        ]
        for key in positive:
            if getattr(self, key) <= 0:
                raise ValueError(f"{key} must be positive")
        for key in ["air_area_m2", "mixing_loss", "friction", "log_sigma"]:
            if getattr(self, key) < 0:
                raise ValueError(f"{key} must be nonnegative")
        for key in ["cd_water", "cd_air", "impact"]:
            if not 0 < getattr(self, key) <= 1:
                raise ValueError(f"{key} must lie in (0, 1]")
        if not 0 <= self.retention <= 1 or not 0 <= self.angle_deg <= 70:
            raise ValueError("retention must be in [0,1]; angle in [0,70] degrees")
        if self.mixing_m <= self.nozzle_m or self.radius_edge_m <= self.radius_start_m:
            raise ValueError("mixing diameter and edge radius must exceed upstream values")
        if self.vapor_pressure_pa >= self.pressure_atm_pa:
            raise ValueError("vapor pressure must be below atmospheric pressure")

    @property
    def rho_air(self):
        return self.pressure_atm_pa / (287.05 * self.temperature_k)

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as stream:
            return cls(**json.load(stream))
