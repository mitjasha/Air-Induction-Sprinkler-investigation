from dataclasses import replace
import numpy as np
import pytest
from sprinkler1d import Case, simulate
from sprinkler1d.ejector import solve, air_mass_flow
from sprinkler1d.film import solve as film
from sprinkler1d.ballistics import fly
from sprinkler1d.rainfall import deposit, christiansen
from sprinkler1d.dimensions import audit


def test_ejector_momentum_mass_energy():
    c = Case()
    e = solve(c)
    assert abs(e.momentum_residual_pa) < 1e-5
    assert c.vapor_pressure_pa < e.suction_pa < c.pressure_atm_pa
    assert e.air_kgs == pytest.approx(e.air_ref_m3s * c.rho_air)
    assert e.kq == pytest.approx(e.alr * c.rho_water / c.rho_air)
    assert 0 < e.kinetic_w < e.hydraulic_w


def test_orifice_limits_and_choking():
    c = Case()
    critical = c.pressure_atm_pa * (2 / 2.4) ** 3.5
    assert air_mass_flow(c.pressure_atm_pa, c) == 0
    assert air_mass_flow(0.5 * critical, c) == pytest.approx(air_mass_flow(critical, c))
    assert air_mass_flow(critical * 1.000001, c) == pytest.approx(
        air_mass_flow(critical, c), rel=1e-6
    )
    assert air_mass_flow(0.8 * c.pressure_atm_pa, c) < air_mass_flow(critical, c)


def test_closed_air_port():
    e = solve(replace(Case(), air_area_m2=0))
    assert e.air_kgs == e.kq == e.alpha == 0


def test_inadmissible_geometry_rejected():
    with pytest.raises(ValueError, match="No admissible"):
        solve(replace(Case(), mixing_m=0.00401))


def test_frictionless_film_analytic():
    c = replace(Case(), friction=0, retention=0)
    e = solve(c)
    f = film(c, e)
    assert np.allclose(f.velocity_ms, c.impact * e.velocity_ms)
    assert np.allclose(
        f.liquid_thickness_m * f.radius_m, e.water_m3s / (2 * np.pi * c.impact * e.velocity_ms)
    )
    assert f.liquid_balance_relative < 1e-12
    assert abs(f.energy_residual_m2s2) < 1e-8


def test_film_numerical_refinement():
    c = Case()
    e = solve(c)
    a, b = film(c, e, rtol=1e-5), film(c, e, rtol=1e-10)
    assert a.velocity_ms[-1] == pytest.approx(b.velocity_ms[-1], rel=1e-4)
    assert np.all(np.diff(b.velocity_ms) < 0)
    assert np.all(np.diff(b.alpha) < 0)


def test_vacuum_ballistics_exact_solution():
    v, theta, h, g = 8.0, np.deg2rad(30), 1.5, 9.80665
    time = (v * np.sin(theta) + np.sqrt((v * np.sin(theta)) ** 2 + 2 * g * h)) / g
    f = fly(0.001, v, 30, h, drag=False)
    assert f.time_s == pytest.approx(time, rel=1e-7)
    assert f.range_m == pytest.approx(v * np.cos(theta) * time, rel=1e-7)
    assert abs(f.path[-1, 1]) < 1e-8


def test_drag_reduces_range_and_refines():
    a = fly(0.001, 8, 30, 1.5)
    b = fly(0.001, 8, 30, 1.5, rtol=1e-10)
    assert a.range_m < fly(0.001, 8, 30, 1.5, drag=False).range_m
    assert a.range_m == pytest.approx(b.range_m, rel=1e-5)


def test_rain_exact_volume_and_uniform_cu():
    r = deposit([0.5, 1.5], [0.25, 0.75], 0.001, bins=2)
    assert np.sum(r.intensity_mm_h * r.area_m2) / 3.6e6 == pytest.approx(0.001)
    assert christiansen([5, 5, 5], [1, 2, 3]) == 100
    assert christiansen([0, 2]) == 0


@pytest.mark.parametrize(
    "change",
    [
        {"pressure_pa": -1},
        {"air_area_m2": -1},
        {"impact": 1.5},
        {"sigma": float("nan")},
        {"angle_deg": 90},
        {"radius_start_m": 0},
        {"log_sigma": -1},
    ],
)
def test_invalid_inputs(change):
    with pytest.raises(ValueError):
        replace(Case(), **change)


def test_dimensional_audit():
    result = audit()
    assert result["weber"] == "dimensionless"
    assert result["ohnesorge"] == "dimensionless"
    assert len(result) == 9


def test_end_to_end():
    r = simulate(Case(), classes=64)
    assert r.summary()["status"] == "DEMONSTRATIVE_NOT_VALIDATED"
    assert r.rain.balance_relative < 1e-12
    assert 1 / np.sum(r.drops.volume_fraction / r.drops.diameter_m) == pytest.approx(r.drops.d32_m)
    assert all(f.range_m > 0 for f in r.flights)


def test_class_refinement_mean_range():
    a, b = simulate(Case(), classes=32), simulate(Case(), classes=128)
    assert a.summary()["mean_range_m"] == pytest.approx(b.summary()["mean_range_m"], rel=0.01)
