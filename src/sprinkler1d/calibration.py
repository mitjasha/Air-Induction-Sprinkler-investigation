"""Staged identification with explicit train/holdout provenance and CSV units."""

import csv
import numpy as np
from scipy.optimize import least_squares

REQUIRED = {
    "run_id",
    "split",
    "provenance",
    "delta_m",
    "we_liquid",
    "alpha",
    "d32_m",
    "sigma_d32_m",
}


def fit_breakup(path):
    with open(path, encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if not REQUIRED.issubset(reader.fieldnames or []):
            raise ValueError(
                f"Missing CSV columns: {sorted(REQUIRED - set(reader.fieldnames or []))}"
            )
        rows = list(reader)
    if not rows:
        raise ValueError("Empty experiment table")
    ids = [r["run_id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate run_id; group replicates before splitting")
    if any(
        r["split"] not in ("calibration", "holdout")
        or r["provenance"] not in ("synthetic", "experimental")
        for r in rows
    ):
        raise ValueError("Invalid split or provenance label")
    if len({r["provenance"] for r in rows}) != 1:
        raise ValueError("Synthetic and experimental records must not be mixed")
    data = np.array(
        [
            [float(r[k]) for k in ["delta_m", "we_liquid", "alpha", "d32_m", "sigma_d32_m"]]
            for r in rows
        ]
    )
    h, we, alpha, d, sd = data.T
    if (
        not np.isfinite(data).all()
        or np.any(data[:, [0, 1, 3, 4]] <= 0)
        or np.any((alpha < 0) | (alpha >= 1))
    ):
        raise ValueError("Invalid measured quantities/uncertainties")
    train = np.array([r["split"] == "calibration" for r in rows])
    if train.sum() < 5 or (~train).sum() < 2:
        raise ValueError("Need >=5 calibration and >=2 holdout runs")
    x = np.column_stack([np.ones(len(rows)), np.log(we), np.log1p(-alpha)])
    if np.linalg.matrix_rank(x[train]) < 3:
        raise ValueError("Parameters unidentifiable: rank-deficient experimental design")

    def prediction(p):
        return h * np.exp(x @ p)

    fit = least_squares(
        lambda p: (prediction(p)[train] - d[train]) / sd[train],
        [np.log(6), -0.2, 0.5],
        bounds=([-5, -2, -3], [8, 2, 3]),
    )
    pred = prediction(fit.x)
    info = fit.jac.T @ fit.jac
    condition = float(np.linalg.cond(fit.jac))
    if not fit.success or condition > 1e8:
        raise ValueError("Identification failed or is ill-conditioned")
    # Known response uncertainties; linearized covariance, conditioned on exact inputs.
    covariance = np.linalg.inv(info)
    hold = (pred[~train] - d[~train]) / d[~train]
    experimental = rows[0]["provenance"] == "experimental"
    return {
        "status": "EXPERIMENTAL_FIT_REQUIRES_REVIEW" if experimental else "SYNTHETIC_RECOVERY_ONLY",
        "parameters": {
            "breakup_c": float(np.exp(fit.x[0])),
            "breakup_we_exp": float(fit.x[1]),
            "breakup_air_exp": float(fit.x[2]),
        },
        "covariance_logc_we_air": covariance.tolist(),
        "jacobian_condition": condition,
        "holdout_mape_percent": float(np.mean(np.abs(hold)) * 100),
        "calibration_runs": int(train.sum()),
        "holdout_runs": int((~train).sum()),
        "run_ids": ids,
        "prediction_d32_m": pred.tolist(),
        "limitations": "Upstream film inputs treated as exact; correlated errors and design-family leakage require review. No automatic validation claim.",
    }
