"""Seeded scenario propagation; assumed ranges are not calibrated confidence bounds."""

from dataclasses import replace
import numpy as np
from .ejector import solve as ejector
from .film import solve as film
from .breakup import solve as breakup


def propagate(case, samples=100, seed=42):
    if samples < 10:
        raise ValueError("Use at least 10 scenarios")
    rng = np.random.default_rng(seed)
    values, rejected = [], 0
    for _ in range(samples):
        c = replace(
            case,
            breakup_c=case.breakup_c * rng.uniform(0.8, 1.2),
            impact=min(1, case.impact * rng.uniform(0.9, 1.1)),
            friction=case.friction * rng.uniform(0.7, 1.3),
        )
        try:
            e = ejector(c)
            values.append(breakup(c, film(c, e)).d32_m * 1000)
        except ValueError:
            rejected += 1
    if not values:
        raise ValueError("All uncertainty scenarios infeasible")
    return {
        "status": "ASSUMED_SCENARIO_INTERVAL_NOT_CONFIDENCE_INTERVAL",
        "seed": seed,
        "samples": samples,
        "accepted": len(values),
        "rejected": rejected,
        "d32_mm_p05_p50_p95": np.quantile(values, [0.05, 0.5, 0.95]).tolist(),
        "assumptions": "Independent uniform: C +/-20%, impact +/-10% capped at 1, friction +/-30%",
    }
