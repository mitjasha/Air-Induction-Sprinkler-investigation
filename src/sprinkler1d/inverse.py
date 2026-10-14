"""Bounded synthesis in a specified design box; no global-optimality claim."""

from dataclasses import replace, asdict
import numpy as np
from scipy.optimize import least_squares
from .ejector import solve as ejector
from .film import solve as film
from .breakup import solve as breakup


def synthesize(case, target_flow_l_min, target_d32_mm):
    if (
        not np.isfinite([target_flow_l_min, target_d32_mm]).all()
        or min(target_flow_l_min, target_d32_mm) <= 0
    ):
        raise ValueError("Targets must be finite and positive")

    def response(x):
        c = replace(case, pressure_pa=x[0] * 1000, nozzle_m=x[1] / 1000)
        e = ejector(c)
        d = breakup(c, film(c, e))
        return c, np.array([e.water_m3s * 60000, d.d32_m * 1000])

    target = np.array([target_flow_l_min, target_d32_mm])

    def residual(x):
        try:
            return np.log(response(x)[1] / target)
        except ValueError:
            return np.array([100.0, 100.0])

    upper_d = min(5.5, case.mixing_m * 1000 * 0.8)
    if upper_d <= 2.5:
        raise ValueError("Mixing diameter incompatible with synthesis design box")
    lower, upper = [80, 2.5], [350, upper_d]
    best = None
    for start in ([150, 3.5], [220, 4.2], [300, 4.8]):
        fit = least_squares(
            residual,
            np.clip(start, lower, upper),
            bounds=(lower, upper),
            xtol=1e-9,
            ftol=1e-9,
            gtol=1e-9,
            max_nfev=120,
        )
        if best is None or np.linalg.norm(fit.fun) < np.linalg.norm(best.fun):
            best = fit
    c, pred = response(best.x)
    error = pred / target - 1
    return {
        "status": "DEMONSTRATIVE_NOT_VALIDATED",
        "converged": bool(best.success),
        "target_met": bool(np.max(np.abs(error)) < 0.01),
        "relative_errors": error.tolist(),
        "prediction_flow_l_min_d32_mm": pred.tolist(),
        "bounds_kpa_mm": [lower, upper],
        "case": asdict(c),
    }
