"""Source-specific equations, deliberately separate from the unvalidated solver.

2019: doi:10.29235/1817-7204-2019-57-2-230-237, equations 18-20.
2021: https://rep.bsatu.by/handle/doc/12545, equations 1-6.
See docs/literature.md before interpreting outputs as physical predictions.
"""

import math


def _positive(**values):
    for name, value in values.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be finite and positive")


def criterion_2019(length_m, froude, ohnesorge, x1, x5, alpha=1.0):
    """Literal Eq. 18: dk=L*(alpha*Fr/2)^x1*(1/Oh^2)^x5.

    Fr is v²/(g L), NOT v/sqrt(g L). dk is the paper's diameter,
    not automatically a Sauter mean. This is an audit equation, not a closure.
    """
    _positive(length_m=length_m, froude=froude, ohnesorge=ohnesorge, alpha=alpha)
    if not all(math.isfinite(x) for x in (x1, x5)):
        raise ValueError("Exponents must be finite")
    try:
        result = length_m * math.exp(
            x1 * math.log(alpha * froude / 2) - 2 * x5 * math.log(ohnesorge)
        )
    except OverflowError as exc:
        raise ValueError("Criterion overflow; input outside numerical domain") from exc
    _positive(diameter_m=result)
    return result


def exponents_2019(nozzle_diameter_m):
    """Printed Eqs. 19-20 interpreted with d0 in metres as defined on p.232.

    The slopes therefore carry inverse-metre units. Do not silently change
    signs or units to match Table 1: that requires source-author clarification.
    """
    _positive(nozzle_diameter_m=nozzle_diameter_m)
    return -8.8512 * nozzle_diameter_m + 0.2329, -0.9399 * nozzle_diameter_m + 0.3044


def control_flows_2021(water_m3_s, air_m3_s, throat_diameter_m, heads=1):
    """Kinematic Eq. 1-6 contract at one common local gas-volume reference.

    No pressure network, gas slip, actuator dynamics or energy feasibility is
    solved. Identical head flows are assumed. Convert standard/ambient air
    readings to the local section conditions BEFORE calling this function.
    """
    _positive(water_m3_s=water_m3_s, throat_diameter_m=throat_diameter_m)
    if not math.isfinite(air_m3_s) or air_m3_s < 0:
        raise ValueError("air_m3_s must be finite and nonnegative")
    if isinstance(heads, bool) or not isinstance(heads, int) or heads < 1:
        raise ValueError("heads must be a positive integer")
    area = math.pi * throat_diameter_m**2 / 4
    return {
        "status": "PUBLISHED_KINEMATIC_RELATION_NOT_CONTROLLER_VALIDATION",
        "entrainment_ratio": air_m3_s / water_m3_s,
        "water_only_velocity_m_s": water_m3_s / area,
        "mixture_velocity_m_s": (water_m3_s + air_m3_s) / area,
        "total_water_m3_s": heads * water_m3_s,
        "total_air_m3_s": heads * air_m3_s,
    }
