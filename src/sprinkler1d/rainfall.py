"""Conservative annular deposition and area-weighted single-head uniformity."""

from dataclasses import dataclass
import numpy as np


@dataclass
class Rain:
    edges_m: np.ndarray
    intensity_mm_h: np.ndarray
    area_m2: np.ndarray
    balance_relative: float
    cu_area_percent: float


def christiansen(intensity, area=None):
    x = np.asarray(intensity, dtype=float)
    w = np.ones_like(x) if area is None else np.asarray(area, dtype=float)
    if (
        x.ndim != 1
        or not x.size
        or x.shape != w.shape
        or not np.all(np.isfinite(x))
        or not np.all(np.isfinite(w))
        or np.any(x < 0)
        or np.any(w <= 0)
    ):
        raise ValueError("Finite nonnegative intensities and positive matching weights required")
    mean = np.average(x, weights=w)
    if mean <= 0:
        raise ValueError("CU undefined for zero rain")
    # Unclipped definition: strongly localized patterns can produce negative CU.
    return float(100 * (1 - np.average(np.abs(x - mean), weights=w) / mean))


def deposit(ranges, fractions, flow, bins=30):
    ranges, fractions = np.asarray(ranges), np.asarray(fractions)
    if (
        bins < 2
        or ranges.ndim != 1
        or not ranges.size
        or ranges.shape != fractions.shape
        or not np.all(np.isfinite(ranges))
        or not np.all(np.isfinite(fractions))
        or np.any(ranges < 0)
        or np.any(fractions < 0)
        or not np.isfinite(flow)
        or flow <= 0
        or not np.isclose(fractions.sum(), 1, rtol=0, atol=1e-10)
    ):
        raise ValueError("Invalid deposition inputs")
    edges = np.linspace(0, max(float(ranges.max()) * 1.001, 0.01), bins + 1)
    volume = np.histogram(ranges, bins=edges, weights=fractions * flow)[0]
    area = np.pi * np.diff(edges**2)
    intensity = volume / area * 3.6e6
    balance = abs(float(np.sum(intensity * area) / 3.6e6 / flow) - 1)
    return Rain(edges, intensity, area, balance, christiansen(intensity, area))
