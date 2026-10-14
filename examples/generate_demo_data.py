"""Create synthetic data for parameter-recovery tests, never validation."""

from pathlib import Path
import csv
import numpy as np


def generate(path, noise=0.02):
    rng = np.random.default_rng(20261014)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "run_id",
                "split",
                "provenance",
                "delta_m",
                "we_liquid",
                "alpha",
                "d32_m",
                "sigma_d32_m",
            ]
        )
        for i in range(60):
            h = rng.uniform(0.00015, 0.0007)
            we = rng.uniform(15, 350)
            alpha = rng.uniform(0.01, 0.35)
            d = 6 * h * we ** (-0.2) * (1 - alpha) ** 0.5
            sd = max(noise, 0.001) * d
            observed = d + rng.normal(0, noise * d)
            w.writerow(
                [
                    f"SYN-{i:03d}",
                    "holdout" if i % 4 == 0 else "calibration",
                    "synthetic",
                    h,
                    we,
                    alpha,
                    observed,
                    sd,
                ]
            )


if __name__ == "__main__":
    generate(Path(__file__).resolve().parents[1] / "datasets/demo/breakup_synthetic.csv")
