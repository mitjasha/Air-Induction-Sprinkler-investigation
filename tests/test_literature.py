import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sprinkler1d.literature import (
    criterion_2019,
    criterion_2019_c001_hypothesis,
    exponents_2019,
    control_flows_2021,
)


def test_dimensionless_limits_and_scaling():
    assert criterion_2019(0.01, 2, 1, 0.4, 0.2) == pytest.approx(0.01)
    assert criterion_2019(0.02, 8, 0.5, 0.4, 0.2) == pytest.approx(
        2 * criterion_2019(0.01, 8, 0.5, 0.4, 0.2)
    )


def test_published_table_is_not_silently_fitted():
    table = Path(__file__).parents[1] / "datasets/literature/criterion2019_table1.csv"
    with table.open() as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 8
    for row in rows:
        d = float(row["nozzle_mm"]) / 1000
        literal = 1000 * criterion_2019(
            d, float(row["froude"]), float(row["ohnesorge"]), *exponents_2019(d)
        )
        # A regression guard against silently changing the published signs/units.
        assert literal / float(row["reported_calculation_dk_mm"]) > 100
        assert float(row["reported_experiment_dk_mm"]) - float(
            row["reported_calculation_dk_mm"]
        ) == pytest.approx(float(row["reported_difference_mm"]))


def test_hypothesis_first_row_in_metres_and_original_preserved():
    args = (0.00298, 4178, 0.0022, 0.206523424, 0.301599098)
    assert criterion_2019(*args) == pytest.approx(0.579304847807418)
    assert criterion_2019_c001_hypothesis(*args) == pytest.approx(0.000579304847807418)
    assert criterion_2019(0.01, 2, 1, 0.4, 0.2) == pytest.approx(0.01)
    assert criterion_2019_c001_hypothesis(0.01, 2, 1, 0.4, 0.2) == pytest.approx(0.00001)


def test_literature_audit_artifacts_and_provenance(tmp_path):
    root = Path(__file__).parents[1]
    table = root / "datasets/literature/criterion2019_table1.csv"
    original_hash = hashlib.sha256(table.read_bytes()).hexdigest()
    run = subprocess.run(
        [sys.executable, str(root / "examples/literature_audit.py"), "--output", str(tmp_path)],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, run.stderr
    payload = json.loads((tmp_path / "audit.json").read_text())
    assert payload["validation_status"] == "NOT_VALIDATED"
    assert payload["literal_status"] == "SOURCE_REPRODUCTION_DISCREPANCY"
    assert payload["hypothesis"]["status"] == "HYPOTHESIS_NOT_CONFIRMED_ERRATUM"
    assert payload["hypothesis"]["dimensionless_c"] == 0.001
    assert payload["hypothesis"]["excluded_from_forward_and_inverse_solver"]
    rows = payload["rows"]
    assert len(rows) == 8
    assert rows[0]["hypothesis_vs_reported_calculation_error_percent"] == pytest.approx(
        -0.11985382630723684
    )
    assert rows[0]["hypothesis_minus_reported_experiment_mm"] == pytest.approx(-0.120695152192582)
    assert payload["hypothesis_vs_published_calculation"]["mape_percent"] < 2
    assert payload["hypothesis_vs_reported_experiment"]["mape_percent"] > 10
    assert all(row["compatible_with_display_rounding"] for row in rows)
    assert payload["rounding_assumptions"]["compatible_rows"] == 8
    assert hashlib.sha256(table.read_bytes()).hexdigest() == original_hash
    assert (tmp_path / "comparison.png").stat().st_size > 10000
    assert "C=0.001" in (tmp_path / "comparison.svg").read_text(encoding="utf-8")
    assert "Literal C=1" in (tmp_path / "comparison.md").read_text(encoding="utf-8")
    with (tmp_path / "comparison.csv").open() as file:
        csv_rows = list(csv.DictReader(file))
    assert len(csv_rows) == 8
    assert "literal_equation_dk_mm" in csv_rows[0]
    assert "hypothesis_c001_dk_mm" in csv_rows[0]


def test_2021_flow_conservation_and_air_closed_limit():
    closed = control_flows_2021(0.001, 0, 0.01, 12)
    open_ = control_flows_2021(0.001, 0.0005, 0.01, 12)
    assert closed["mixture_velocity_m_s"] == closed["water_only_velocity_m_s"]
    assert open_["mixture_velocity_m_s"] / closed["mixture_velocity_m_s"] == pytest.approx(1.5)
    assert open_["total_water_m3_s"] == pytest.approx(0.012)
    assert open_["total_air_m3_s"] == pytest.approx(0.006)


@pytest.mark.parametrize("bad", [0, -1, float("nan"), float("inf")])
def test_criterion_rejects_invalid_dimensionless_inputs(bad):
    with pytest.raises(ValueError):
        criterion_2019(0.01, bad, 0.001, 0.2, 0.3)


@pytest.mark.parametrize("heads", [0, -1, 1.5, True])
def test_control_rejects_invalid_head_count(heads):
    with pytest.raises(ValueError):
        control_flows_2021(0.001, 0, 0.01, heads)
