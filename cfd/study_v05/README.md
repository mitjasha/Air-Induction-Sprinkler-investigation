# CFD v0.5 — turbulence, mesh study and reproducible analysis

**Model status:** source-generation and Python postprocessing are implemented and
unit-tested; the new v0.5 `kOmegaSST` cases have **not yet run in OpenFOAM v2606**.
The user's historical v0.4 annular case **did** run through 60 ms and showed a
near-stabilized *mixture* flux ratio, but that is not numerical/physical validation.

## Working assumptions and prior results

- Patent concepts **BY 22927** (adjustable sprinkler) and **BY 22747** (hydrojet
  ejector). Original patent drawings must still be cross-checked. 7.9 mm bore,
  approximately 9.5 mm × 85 mm throat are historically motivated starts;
  feed Ø16 mm, 1.2 mm diaphragm thickness, 8 mm gap, suction Ø16 mm, lateral
  Ø5 mm intake and deflector geometry are changeable assumptions.
- 2D axisymmetric wedge has an **annular** air intake, whereas the physical patent
  device has a lateral port. Do not transfer 2D annular entrainment directly to 3D.
- v0.4 water `U` inlet 2.9251875 m/s (≈same total water inlet flow as v0.3 12 m/s
  through 7.9 mm bore), **not** matched pressure or pump energy.
- v0.4 60 ms open case: `phi(airInlet)=-2.076180457e-06 m³/s` on 5° wedge,
  `phi(waterInlet)=-8.158300457e-06 m³/s`. Thus `k_phi≈0.2545`, **not** proven
  water/air phase-resolved `kQ`. `ambientOpen` also draws some air.
- v0.4 centre profile exported only up to 45 mm, the near-wall profile to 90 mm.
  Sampled cell-to-point stair-steps do not demonstrate a physical mixing shock.

## Version 0.5 additions

1. `interFoam` with `simulationType RAS` and `RASModel kOmegaSST` (laminar option
   still supported for matched numerical-method comparisons). Explicit `k`,
   `omega`, `nut` fields, wall functions, turbulence equation schemes and solvers.
   Adjustable water/air inlet turbulence intensity and integral scale. Initial
   values are **assumptions**, not measurements.
2. Coarse / medium / fine 5° wedge meshes (estimated **5 160 / 13 446 / 30 592**
   cells) × open / closed air mode = **six cases**. This is only an initial mesh
   hierarchy. It does not automatically resolve the water-air interface or the
   boundary layer; **check yPlus and inspect interface cells**, then revise zoning.
3. `yPlus` function object; four signed **mixture**-flux function objects inherited
   from v0.4; `postProcessing`/console log parsing, automatic convergence-window
   diagnostics, mass-volume balance, per-case PNG/CSV/JSON/Markdown reports.
4. Optional ParaView `pvpython` sampler for 3 axial and 5 radial paths per time,
   to expose interface development rather than inferring shocks from two lines.
5. Controlled `run` and `batch` commands with explicit success/failure audit;
   `compare` generates the mesh/open-closed summary **without marking unrun
   cases as solved**.

## Install and generate (Ubuntu/WSL, OpenFOAM.com v2606)

```bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
cd ~/CAE/Air-Induction-Sprinkler/Air-Induction-Sprinkler-Virtual-Laboratory-v0.5
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pytest -q tests/
OUT="$HOME/CAE/CFD-runs/patent_v05"
python -m cfd.study_v05.generate --out-dir "$OUT"
```

Edit `cfd/study_v05/study_config.json` for the mesh, turbulence and run control.
Modify `cfd/patent_v04/config_open.json` for the geometry, or point
`geometry_config` to a copy and pass `--config path/to/study.json`. Use
**new study directories** when changing parameters so results remain auditable.

## A. Preflight before solving

```bash
python -m cfd.study_v05.batch --study-dir "$OUT" --cases ejector_coarse_open ejector_coarse_closed
# The runner checks blockMesh, checkMesh (Mesh OK.) and real-mesh interFoam -dry-run.
cat "$OUT/ejector_coarse_open/run_audit.json"
```

**STOP** on mesh failure or the first solver IO error. `Mesh OK` is a geometry
check, not RANS-wall or physics validation. Check `k`, `omega` and `nut` BCs
against the exact solver v2606; the local build environment has no OpenFOAM.

## B. First transient and physical consistency

```bash
python -m cfd.study_v05.run --study-dir "$OUT" --case ejector_coarse_open --steps solve
python -m cfd.study_v05.run --study-dir "$OUT" --case ejector_coarse_closed --steps solve
```

These default to a 60 ms end time, `Co < 0.2`, `alphaCo < 0.2`, write 2 ms.
If the solvers are stiff or yPlus inadequate, do not interpret physical numbers.
**Observe each run first; do not start all six expensive cases unattended.**
Restart only from existing latest saved time and update `endTime` explicitly.
A single `run_audit.json` represents only the most recent runner invocation;
solver logs and field time directories are the immutable evidence.

## C. Quantitative report (no manual calculations)

```bash
CASE="$OUT/ejector_coarse_open"
python -m cfd.study_v05.analyze --case "$CASE" --report "$CASE/report"
```

Report files:
`flux_history.csv`, `boundary_fluxes.png`, `k_phi_history.png`,
`flux_balance.png`, `summary.json`, `report.md`. The statistics use full
signed `phi`, including `ambientOpen` and the finite-volume net balance.
Quasi-steady criterion default: last 10 ms range of `k_phi` <5% of mean.
Also compare pressure and phase inventory over the same interval; stability
of a single scalar is NOT full stationarity.

## D. Extract phase and pressure profiles

Manual ParaView approach: open `case.foam` and export `Plot Over Line` CSV on
3 axial lines (1, 3, 4.5 mm radius, z=10..90 mm) and radial lines (z=10, 30,
50, 70, 90 mm). Export at the same physical time in all cases. Enable `U`,
`p_rgh`, `alpha.water`, `vtkValidPointMask`, `Points:0/1/2`.

Optional headless variant (ParaView's **pvpython**, distinct from standard Python):

```bash
# Install/provide pvpython separately; not part of the Python venv.
pvpython cfd/study_v05/sample_pvpython.py --case "$CASE"
python -m cfd.study_v05.analyze --case "$CASE" --report "$CASE/report" \
  --profiles axis="$CASE/sampled_profiles/axial_r1p0mm.csv" \
  wall="$CASE/sampled_profiles/axial_r4p5mm.csv"
```

`sample_pvpython.py` is a **version-dependent convenience prototype**:
verify on your ParaView installation. The CSV analyzer checks valid-point masks
and axial coverage; a line through 200 samples on 121 axial cells does NOT
increase numerical resolution. Get `p(z)`, `alpha(z)`, `Uz(z)` figures for each
run. Pressure is Pa; `p_rgh=p` only for `g=0` here.

## E. Comparison and acceptance gates

```bash
python -m cfd.study_v05.compare --study-dir "$OUT" --report "$OUT/summary"
```

Before declaring the model quantitatively credible:

1. **Real-mesh execution**: pass `blockMesh`, extensive `checkMesh`,
   `interFoam -dry-run`, production solve on v2606 for *every* case.
2. **Turbulence**: inspect `yPlus` at every relevant water-wet wall; choose
   wall-treatment/mesh consistent with desired yPlus, validate k/omega inlet
   values, examine sensitivity to turbulence closure (SST vs alternatives).
3. **Time convergence**: transient flux, phase volume, backflow, pressure,
   residuals and Co/alphaCo; choose a statistically stable averaging window.
4. **Phase-resolved balance**: directly integrate per-face conservative
   transported liquid phase flux (OpenFOAM version-specific alpha flux field,
   if available) with correct sign and water/air boundary contributions. An
   approximation from interpolated `alpha*U·n` is NOT guaranteed conservative.
   Until verified, report only `k_phi`, never validated `kQ`.
5. **Mesh independence**: at least three meshes for the **same geometry and
   boundary conditions**, compare phase-specific kQ, mixing onset position,
   pressure loss and radial interface thickness. Diagnose yPlus in all levels.
6. **Physical model error**: laminar/RANS vs 3D lateral duct; interface
   capture vs resolved breakup vs Eulerian multiphase; compressible air
   sensitivity, open outlet/backpressure and domain extension.
7. **Mixing-shock hypothesis**: local static pressure recovery alone is
   insufficient. Require concurrent phase redistribution across multiple
   radii, velocity redistribution, energy/momentum change, robust axial
   localization, convergence and experimental plausibility. Do not assume a
   shock exists in advance.
8. **Patent-based geometry**: update unknown parameters as actual drawings,
   dimensions or measurements become available, label their source.
9. **Independent evidence**: check against prior experimental kQ trends
   separately from other historical regimes; do not use simulated outputs
   as ground-truth calibration. Validate energy at matched flow/coverage.

## Caveats

- `kOmegaSST` is a RANS closure and cannot resolve an entire droplet/bubble
  spectrum. Grid spacing of 30,592 cells still may be **far from adequate**
  for surface breakup and mixing-shock physics.
- The 2D wedge gives full annular intake and cannot model a lateral port or
  circumferential asymmetry. The 3D Gmsh prototype from v0.4 is **not yet
  solver-ready**. Use it only after independent meshing and boundary tests.
- No unverified `alphaPhi` object name is assumed. Phase flux verification is
  solver-version and field-registration dependent and must be a separate gate.
- The physical backpressure is not yet an independent experimental control
  (the open boundaries use prescribed total pressure). Add controlled outlet
  conditions in a separate validated study before inferring mixing-shock trends.
- Do not treat smooth numerical contours or sampled stair-steps as proof of a
  physically absent/present hydraulic jump.

## F. Geometric parameter screening (after passing baseline acceptance gates)

Once the paired coarse/medium/fine baseline has been reviewed, generate
controlled one-factor-at-a-time **hypotheses** for bore 7.6–8.8 mm,
nozzle–throat gap 4–12 mm, throat diameter 9–10 mm and throat length
60–110 mm. Only the 7.9 mm bore and approximately 9–10 × 85 mm throat
have partial historical justification; other candidates are **assumed**.

```bash
SWEEP="$HOME/CAE/CFD-runs/v05_screening"
python -m cfd.study_v05.sweep --out-dir "$SWEEP" --grid coarse --air-mode open
# First inspect the resulting sweep_manifest.json and check the bounds.
# Then run selected candidates using the same run/analyze commands, changing --study-dir.
```

This is a one-factor screen, **not** an optimized design or a validated
sensitivity surface. It does not explore pressure-backpressure or 3D intake
shape yet; these must be added as independent controlled studies after
verification of the model and full phase-flux observables.

## v0.5.1 scientific-audit update (2026-10-20)

The prior note that v0.5 was unrun is historical: WSL OpenFOAM.com v2606 completed coarse Open and Closed at 60 ms (user logs); see `docs/CFD_V051_WORKFLOW_RU.md`. The **new v0.5.1 additions remain unrun** until separately preflighted.

- Mesh levels `medium` and `fine` now use optional `simpleGrading` for near-wall and upstream diaphragm focusing. Coarse is unchanged; actual wall `yPlus` requires solver evaluation. Existing CFD results must not be overwritten.
- Added `waterInventory` function object, offline `phase_flux.py` MULES face-flux auditing (`alphaPhi0.water`, `phi`), optional transient inventory check. Genuine phase conservation and kQ are **not automatically claimed**.
- Analyzer distinguishes zero air-port flow (Closed) from convergence of the outlet; also reports the ambient-open flow separately.
- `temporal.py` automates pressure-time maps, 50% recovery and near-wall recirculation diagnostics from repeated `pvpython` CSV exports; `wall_qc.py` reports yPlus warnings.
- Pressure audit uses explicit **assumed** 101325 Pa absolute reference; the incompressible solver is unchanged, and severe negative gauge pressure is a stop sign for quantitative gas-pressure claims.
- All CFD-specific new tools require WSL v2606 preflight and checks on real outputs. No claim of validated mixing shock.
