# Evidence-led roadmap

## 0.1 — implemented demonstrator

Modular forward chain, compressible air inlet, film ODE, dimensional audit, conservative rainfall, inverse pressure/nozzle synthesis, breakup CSV identification with holdout, scenario propagation, HTML report, CFD exchange, automated tests and CI definition.

## 0.2 — published research integrated

Eight-source bibliography, source-to-code map, 2019 equation/table reproduction audit and 2021 kinematic flow contract. Raw measurement validation remains pending.

### 0.2.1 — explicit correction hypothesis

Unchanged printed 2019 equation retained alongside a fixed C=0.001 hypothesis; all eight rows compared against both published calculations and reported experiments; display-rounding compatibility, separate errors, CSV/JSON/Markdown and PNG/SVG figures. The hypothesis is not a confirmed erratum and is not used by the forward/inverse solver.

## Next evidence release

Cite dissertation equations; document real geometry and adjustments; add upstream hydraulic/film identification; preserve raw data and calibration certificates; publish independent holdout with uncertainty-aware criteria.

## 0.3 — physics and field relevance

Variable deflector profile and gravity; calibrated entrainment/degassing; measured size/angle distributions; wind and array overlap; CU convergence studies; thermodynamic/phase-slip equations where measurements justify complexity.

## 0.4 — engineering use

Validated design tables and offline selection with uncertainty bounds; comparison against measured unseen geometries. Surrogates only inside their validated domain.

## Research extensions, not present capabilities

Instability eigenvalue solver; evaporation/thermal coupling; moving spray source; actuator and control models; ROS-compatible footprint service.
## Source-driven next steps

- Confirm or reject the C=0.001 hypothesis using the author's original 2019 workbook or an erratum before enabling a published-correlation prediction mode.
- Identify attached-film and direct-breakup regimes from high-speed imaging of the actual adjustable device.
- Import the 2017/2018 run-level bench data, including pump electrical power and air-volume reference conditions; avoid counting overlapping published campaigns twice.
- Extend the 2021 kinematic flow contract to a pressure network, measured valve maps and sensor/actuator dynamics before attempting closed-loop control or ROS integration.
