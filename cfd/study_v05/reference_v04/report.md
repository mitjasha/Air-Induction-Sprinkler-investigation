# CFD v0.5 automatic diagnostic report

Case: `/mnt/data/air_induction_v05_build/v04_60ms_reference/case`

Flux histories: 1 times; source: console_logs.

Last time: 0.06 s; k_phi=0.25449 (**mixture ratio, not kQ**); last relative volume imbalance=-5.16e-07.

Quasi-steady by k_phi window criterion only: False.

**Mixing shock: NOT CONFIRMED.** A jump in a sampled curve is insufficient evidence.

## Flags and missing evidence

- Not enough points in convergence window
- axis: axial profile ends before 90 mm
- Two axial samples do not resolve radial interface evolution or mixing shock
- No conservative phase-resolved air flux: true kQ cannot be reported
- No mesh/time/turbulence validation: no quantitative physical validation

## Outputs

`summary.json`, `flux_history.csv` (when available), `k_phi_history.png`, `boundary_fluxes.png`, `flux_balance.png`, and axial profile figures (when supplied).
