import csv
import json
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import pytest
from sprinkler1d import Case, simulate
from sprinkler1d.calibration import fit_breakup
from sprinkler1d.inverse import synthesize
from sprinkler1d.uncertainty import propagate
from sprinkler1d.cfd import export_boundary, compare_film

ROOT = Path(__file__).resolve().parents[1]


def make_csv(path, flat=False):
    with path.open("w", newline="") as f:
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
        for i in range(24):
            h = 0.0003
            we = 50 if flat else 20 + 7 * i
            a = 0.1 if flat else 0.02 + 0.04 * (i % 7)
            d = 6 * h * we ** (-0.2) * (1 - a) ** 0.5
            w.writerow(
                [i, "holdout" if i % 4 == 0 else "calibration", "synthetic", h, we, a, d, 0.02 * d]
            )


def test_parameter_recovery(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path)
    fit = fit_breakup(path)
    assert fit["status"] == "SYNTHETIC_RECOVERY_ONLY"
    assert fit["parameters"]["breakup_c"] == pytest.approx(6, rel=1e-5)
    assert fit["parameters"]["breakup_we_exp"] == pytest.approx(-0.2, rel=1e-5)
    assert fit["parameters"]["breakup_air_exp"] == pytest.approx(0.5, rel=1e-5)
    assert fit["holdout_mape_percent"] < 1e-5


def test_identifiability_guard(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path, flat=True)
    with pytest.raises(ValueError, match="rank-deficient"):
        fit_breakup(path)


def test_holdout_not_used_to_fit(tmp_path):
    path = tmp_path / "data.csv"
    make_csv(path)
    before = fit_breakup(path)
    with path.open() as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        if row["split"] == "holdout":
            row["d32_m"] = str(float(row["d32_m"]) * 2)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    after = fit_breakup(path)
    assert before["parameters"] == after["parameters"]
    assert after["holdout_mape_percent"] > 40


def test_inverse_recovers_targets():
    c = replace(Case(), pressure_pa=180000, nozzle_m=0.0042)
    s = simulate(c).summary()
    result = synthesize(Case(), s["water_l_min"], s["d32_mm"])
    assert result["target_met"]
    assert max(abs(x) for x in result["relative_errors"]) < 1e-5


def test_unreachable_target_flagged():
    result = synthesize(Case(), 1000, 5)
    assert not result["target_met"]


def test_scenario_reproducibility():
    assert propagate(Case(), 20, 7) == propagate(Case(), 20, 7)


def test_cfd_contract_roundtrip(tmp_path):
    c = Case()
    r = simulate(c)
    export_boundary(c, r, tmp_path / "boundary.json")
    assert json.loads((tmp_path / "boundary.json").read_text())["units"] == "SI"
    path = tmp_path / "film.csv"
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["r_m", "velocity_ms", "liquid_thickness_m", "source", "mesh_id"])
        for i in [0, 20, 40, 99]:
            writer.writerow(
                [
                    r.film.radius_m[i],
                    r.film.velocity_ms[i],
                    r.film.liquid_thickness_m[i],
                    "synthetic-interface-test",
                    "none",
                ]
            )
    assert all(value < 1e-12 for value in compare_film(path, r)["metrics"].values())


def test_cli_report(tmp_path):
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "sprinkler1d",
            "run",
            "--config",
            str(ROOT / "examples/demo.json"),
            "--output",
            str(tmp_path),
            "--classes",
            "16",
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 0, p.stderr
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest["result"]["status"] == "DEMONSTRATIVE_NOT_VALIDATED"
    assert (tmp_path / "overview.png").stat().st_size > 10000
    assert "data:image/png;base64" in (tmp_path / "report.html").read_text(encoding="utf-8")


def test_cli_invalid_input(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text('{"pressure_pa": -1}')
    p = subprocess.run(
        [
            sys.executable,
            "-m",
            "sprinkler1d",
            "run",
            "--config",
            str(path),
            "--output",
            str(tmp_path / "out"),
        ],
        capture_output=True,
        text=True,
    )
    assert p.returncode == 2
    assert "must be positive" in p.stderr
