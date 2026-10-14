"""Versioned SI exchange contract; no external CFD solver is run here."""

from dataclasses import asdict
import csv
import json
import numpy as np


def export_boundary(case, result, path):
    payload = {
        "schema_version": 1,
        "status": "DEMONSTRATIVE_NOT_VALIDATED",
        "coordinates": "axisymmetric r-z; r outward, z upward",
        "units": "SI",
        "pressure_convention": "absolute",
        "averaging": "phase flow rates; volume flux weighted velocity",
        "recommended_2d": "axisymmetric RANS/VOF for internal flow and film; cannot resolve discrete air ports",
        "recommended_3d": "resolved air ports and transient VOF breakup; DPM downstream",
        "case": asdict(case),
        "outlet": {
            "water_mass_kgs": case.rho_water * result.ejector.water_m3s,
            "air_mass_kgs": result.ejector.air_kgs,
            "pressure_pa": case.pressure_atm_pa,
            "velocity_ms": result.ejector.velocity_ms,
        },
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def compare_film(path, result):
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"r_m", "velocity_ms", "liquid_thickness_m", "source", "mesh_id"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("CFD CSV missing required SI fields")
        rows = list(reader)
    if len(rows) < 2 or any(not r["source"] or not r["mesh_id"] for r in rows):
        raise ValueError("Need >=2 points with source and mesh identifiers")
    data = np.array(
        [[float(r[k]) for k in ["r_m", "velocity_ms", "liquid_thickness_m"]] for r in rows]
    )
    r = data[:, 0]
    if (
        not np.isfinite(data).all()
        or np.any(data <= 0)
        or np.any(np.diff(r) <= 0)
        or r[0] < result.film.radius_m[0]
        or r[-1] > result.film.radius_m[-1]
    ):
        raise ValueError("Invalid CFD data or points outside film domain")
    errors = {}
    for i, name in enumerate(["velocity_ms", "liquid_thickness_m"], 1):
        pred = np.interp(r, result.film.radius_m, getattr(result.film, name))
        errors[name + "_relative_rmse"] = float(
            np.sqrt(np.mean(((pred - data[:, i]) / data[:, i]) ** 2))
        )
    return {
        "status": "CFD_COMPARISON_NOT_EXPERIMENTAL_VALIDATION",
        "metrics": errors,
        "sources": sorted({r["source"] for r in rows}),
        "meshes": sorted({r["mesh_id"] for r in rows}),
    }
