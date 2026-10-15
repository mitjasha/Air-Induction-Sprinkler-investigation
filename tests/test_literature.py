import csv
from pathlib import Path

import pytest

from sprinkler1d.literature import criterion_2019, exponents_2019, control_flows_2021


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
