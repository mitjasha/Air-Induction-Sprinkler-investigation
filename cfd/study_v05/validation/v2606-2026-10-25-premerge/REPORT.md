# OpenFOAM.com v2606 pre-merge validation — PR #2

Validated commit: `de49a137592edc764140a35649742a5f4bc0ce6e`.

## Disposition

**HOLD / no merge recommendation.** Both coarse variants pass mesh generation,
full topology/geometry checking, solver initialization, and a bounded 0.1 ms
transient smoke run. The scientific gate remains incomplete: the predeclared
`yPlus <= 1` criterion fails on most wet walls, the open case shows startup
reverse flow at `airInlet`, and medium/fine, time-step sensitivity, 60 ms
stationarity, pressure/interface stationarity, and independent review remain
outstanding.

## Environment and commands

- Image: `opencfd/openfoam-run:2606`
- Image digest: `sha256:4229997e74defb81548222d511b8e3b95b98305e5df41b8e88b031813fe47eeb`
- OpenFOAM: OpenFOAM.com v2606, `FOAM_API=2606`, 32-bit labels, 64-bit scalars
- Commands: `blockMesh`; `checkMesh -allTopology -allGeometry`;
  `interFoam -dry-run-write`; and `interFoam` with scratch-copy controls
  `startTime=0`, `endTime=0.0001`, `writeInterval=0.00002`.

Exact timestamps and command lines are in `logs/commands.log`; complete stdout,
stderr, and exit codes are under `logs/<case>/`. The generated dictionaries and
manifests are under `cases/`. `SHA256SUMS` covers every archived file.

## Results

| Check | coarse open | coarse closed |
|---|---:|---:|
| `blockMesh` | pass | pass |
| `checkMesh -allTopology -allGeometry` | pass (`Mesh OK`) | pass (`Mesh OK`) |
| `interFoam -dry-run-write` | pass | pass |
| 0.1 ms transient | pass | pass |
| cells | 5,160 | 5,160 |
| max non-orthogonality | 21.098 degrees | 21.098 degrees |
| max skewness | 0.6747 | 0.6747 |
| alpha range | numerical undershoot about 1e-87 to 1 | comparable, bounded at report precision |
| water-budget relative max residual | 4.93e-11 | 4.93e-11 |
| phase-resolved `kQ` | unavailable | unavailable |

`alphaPhi0.water`, `phi`, and `waterInventory` were written at five common saved
times. The transient liquid balance is sign-consistent to the residual above,
but this is only a startup smoke run. The analyzer deliberately leaves
`kQ_phase_resolved=null`. On an input-only case without a compatible saved
field pair it returns `status=UNVERIFIED`, `rows=0`, and no kQ (fail closed).

At 0.1 ms the open case has outward mixture/air flow at `airInlet`, yielding a
negative boundary candidate (`-0.9757`); it is reverse flow, not entrainment.
The closed case correctly has zero air-port flux. Signed histories are archived
in each `phase_flux_history.csv`.

The coarse wall resolution fails the predeclared `yPlus <= 1` target. At 0.1 ms,
open-case maxima include feed wall 40.53, diaphragm wall 18.83, nozzle wall
8.04, and suction wall 7.35. Closed-case maxima include feed wall 40.53,
diaphragm wall 18.72, air-inlet wall 16.50, and nozzle wall 7.90. The
zero-face `deflectorWall` emits sentinel extrema and must be excluded from
finite-wall statistics. The existing `wall_qc` parser reports no readings
because it searches solver logs rather than the v2606 `yPlus.dat`; this is a
tooling defect, not a y+ pass.

The open run reached mixture Courant maxima slightly above the configured 0.2
limit (approximately 0.211; interface Courant approximately 0.014). Production
time-step sensitivity is therefore mandatory.

## Pressure and compressibility

The case uses incompressible `interFoam` with constant densities (water 998.2,
air 1.205 kg/m3) and declares an **assumed** absolute reference of 101325 Pa.
No 60 ms pressure history or pressure/interface stationarity evidence was
produced here. Compressibility risk is therefore unresolved, not cleared; a
quantitative gas-pressure claim is prohibited until the minimum inferred
absolute pressure and density-change/Mach criteria are assessed in the longer
run, with a separate compressible-formulation task if material.

## Remaining gate work

1. Fix the y+ reader and revise wall treatment/mesh, then measure coarse,
   medium, and fine against the declared threshold.
2. Run production open/closed histories and a predeclared time-step sensitivity;
   distinguish boundary-flux stationarity from pressure/interface stationarity.
3. Evaluate coarse/medium/fine convergence for phase-specific kQ (only after
   phase gates), pressure loss, interface thickness, and mixing location.
4. Assess pressure-reference and compressibility risk quantitatively.
5. Obtain an independent scientific/reproducibility review of the archived
   evidence before any merge recommendation.

The completed v0.4 baseline (COU-41) was not modified.
