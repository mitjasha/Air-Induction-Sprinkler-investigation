"""Homogeneous 1D momentum closure with lateral air inlet and ambient outlet."""

from dataclasses import dataclass
from math import pi, sqrt
from scipy.optimize import brentq
from .config import Case


@dataclass(frozen=True)
class Ejector:
    suction_pa: float
    water_m3s: float
    air_kgs: float
    air_ref_m3s: float
    velocity_ms: float
    alpha: float
    alr: float
    kq: float
    momentum_residual_pa: float
    hydraulic_w: float
    kinetic_w: float


def air_mass_flow(ps: float, c: Case) -> float:
    """Isentropic ideal-gas orifice, including choking; ps is absolute."""
    if not 0 < ps <= c.pressure_atm_pa:
        raise ValueError("air inlet requires 0 < suction pressure <= atmospheric")
    gamma, gas_r = 1.4, 287.05
    ratio = max(ps / c.pressure_atm_pa, (2 / (gamma + 1)) ** (gamma / (gamma - 1)))
    radicand = (
        2
        * gamma
        / (gas_r * c.temperature_k * (gamma - 1))
        * (ratio ** (2 / gamma) - ratio ** ((gamma + 1) / gamma))
    )
    return c.cd_air * c.air_area_m2 * c.pressure_atm_pa * sqrt(max(0, radicand))


def solve(c: Case) -> Ejector:
    an, am = pi * c.nozzle_m**2 / 4, pi * c.mixing_m**2 / 4

    def state(ps):
        q = c.cd_water * an * sqrt(2 * (c.pressure_atm_pa + c.pressure_pa - ps) / c.rho_water)
        ma = air_mass_flow(ps, c)
        qa = ma / c.rho_air
        mass = c.rho_water * q + ma
        u = (q + qa) / am
        density = mass / (q + qa)
        # Air enters laterally: zero axial momentum at inlet. Outlet at atmosphere.
        residual = (
            ps
            - c.pressure_atm_pa
            + c.rho_water * q * (q / an) / am
            - mass * u / am
            - c.mixing_loss * density * u * u / 2
        )
        return q, ma, qa, mass, u, residual

    lo, hi = c.vapor_pressure_pa * 1.01, c.pressure_atm_pa
    if state(lo)[-1] * state(hi)[-1] >= 0:
        raise ValueError(
            "No admissible entraining root above vapor pressure; change geometry/pressure"
        )
    ps = brentq(lambda p: state(p)[-1], lo, hi, xtol=1e-7)
    q, ma, qa, mass, u, residual = state(ps)
    power, kinetic = c.pressure_pa * q, mass * u * u / 2
    if kinetic > power * (1 + 1e-8):
        raise ValueError("Closure violates hydraulic energy budget")
    return Ejector(
        ps, q, ma, qa, u, qa / (q + qa), ma / (c.rho_water * q), qa / q, residual, power, kinetic
    )
