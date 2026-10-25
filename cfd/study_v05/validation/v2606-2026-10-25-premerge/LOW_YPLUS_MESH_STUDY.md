# Low-y+ mesh sizing study

Date: 2026-10-25  
Validated branch commit at start: `718381c`

## Purpose

This note records the first mesh-revision attempt following the v2606 coarse
smoke-run result. It is negative evidence, not a production result and not a
change to the declared `yPlus <= 1` gate.

The largest measured coarse value was `yPlus = 40.53` on `feedWall`. Assuming
the usual first-order proportionality between y+ and first-cell wall distance,
the first wall-normal cell must be approximately 40 times smaller before a
solver measurement can plausibly satisfy the declared threshold.

## Candidate and size estimate

The candidate retained the existing single-block radial topology, used the
generator's minimum permitted radial `simpleGrading` ratio of `0.05`, and used
the following radial counts:

| level | core | annulus | estimated cells per case |
|---|---:|---:|---:|
| coarse | 128 | 64 | 33,024 |
| medium | 192 | 96 | 77,472 |
| fine | 256 | 128 | 154,624 |

The six baseline histories would therefore contain 530,240 cells in aggregate,
versus 98,396 for the committed matrix. Scaling the prior ~26 CPU-hour estimate
by aggregate cell count gives approximately 140 CPU-hours before the required
time-step-sensitivity run or any failed/rerun cases. This is well above the
approved 30--40 CPU-hour allocation.

## OpenFOAM v2606 mesh check

The candidate coarse/open case was generated in scratch and checked with:

```text
blockMesh -case <candidate>/ejector_coarse_open
checkMesh -case <candidate>/ejector_coarse_open -allTopology -allGeometry
```

`checkMesh` reported 33,024 cells and failed two checks:

- 8,333 cells with determinant below 0.001 (minimum `1.0300568e-05`);
- 24 faces with interpolation weight below 0.05 (minimum `0.02373086279`).

Other recorded extrema were maximum aspect ratio 366.62, maximum
non-orthogonality 36.44 degrees, and maximum skewness 1.0134. The candidate was
rejected before any solver run. Its scratch case is intentionally not archived
as a valid case.

## Disposition

Uniformly strengthening `simpleGrading` in the existing blocks is not a valid
low-y+ revision. The next mesh must introduce explicit wall-normal layer blocks
with controlled growth and compatible cell sizes at block interfaces, then pass
full topology/geometry checks and a short y+ calibration solve before production.
Changing the threshold to make the existing buffer-layer values pass is not a
scientifically valid alternative.

The production allocation must be re-estimated after a mesh-valid layered
candidate exists. Based on this first sizing bound, the previously approved
30--40 CPU-hours is insufficient; a provisional planning envelope is at least
140 CPU-hours plus time-step sensitivity and rerun margin.
