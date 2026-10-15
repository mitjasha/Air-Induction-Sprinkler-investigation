# Local verification record — 2026-10-15

Environment: new isolated virtual environment, Windows 11, Python 3.12.14. Dependencies were installed into that environment, then sprinkler1d was built and installed as a wheel (not an editable checkout). Exact dependency versions are recorded in constraints-tested.txt.

## Completed checks

- 39 automated tests passed from the installed 0.2.0 wheel in a newly created isolated environment, including two CLI subprocess integration tests and the publication-specific checks.
- Ruff lint passed.
- Forward CLI generated standalone HTML, PNG, SVG, CSV, a CFD boundary contract and a JSON provenance manifest.
- The six-panel PNG was visually inspected for readable labels and layout.
- Synthetic calibration and bounded synthesis CLI examples completed.
- Source distribution and wheel built successfully; the final wheel was reinstalled and the complete test suite passed again.
- The 2019 audit produced a literal-to-reported ratio of 979.5429–1023.3610 under its stated assumptions. The eight-row CSV and comparison figure were checked against the source table and inspected visually.
- pip check reported no broken requirements in the final clean environment.

## Demonstration outputs

| Quantity | Value |
|---|---|
| Gauge pressure | 200 kPa |
| Water flow | 15.9912686 L/min |
| Air flow at reference ambient conditions | 8.3424439 L/min |
| Absolute suction pressure | 36074.9209 Pa |
| d32 | 0.54970777 mm |
| Volume-weighted mean range, 128 classes | 1.31013343 m |
| Momentum residual | -2.36e-11 Pa |
| Film energy-identity residual | -9.25e-11 m²/s² |
| Rainfall relative volume residual | 6.66e-16 |

The seeded noisy synthetic fit recovered C=5.92191, a=-0.197957, q=0.500098, with holdout MAPE=1.34164%. This is recovery against synthetic data, not measured model accuracy.

The inverse example targeted 16 L/min and 0.55 mm: a feasible result was approximately 202.615 kPa and 3.98864 mm nozzle diameter. Relative target errors were approximately 0.002% and -0.0509%. It does not establish uniqueness or global optimality.

The current single-head area-weighted CU is sensitive to diameter quadrature and footprint extent. Do not interpret it as field uniformity. The pressure sweep can encounter inadmissible roots before its requested upper pressure.

The project was pushed to mitjasha/Air-Induction-Sprinkler-investigation and GitHub Actions was triggered. Local results above are independent of remote CI; consult the repository's Actions page for the latest Linux/Windows and Python 3.11–3.13 matrix status. CI builds use an isolated build environment so setuptools/wheel do not have to be preinstalled on the runner.
