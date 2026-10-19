# CFD v0.4 — patent-informed ejector geometry

## Source provenance and scope

The design is informed by Belarusian patents **BY 22927** ("Дождевальная насадка с регулируемыми параметрами дождя", application a 20180314, published 2020-04-30) and **BY 22747** ("Гидроструйный эжектор", published 2019-10-30), by Shakhray and Kravtsov, and by the associated publication on adjustable hydraulic characteristics (2021).

**Patent numbers and overall concepts are sourced; the original patent PDF drawings have NOT yet been programmatically verified in this version.** The dimensions in `config_open.json` are **initial parameters**, not inferred measurements from an undimensioned figure. The separately controllable physical 3D air port is not equivalent to the 2D annular-air surrogate. No patent coverage or legal status is implied.

## Starting dimensions (mm)

| Parameter | Initial value | Status |
|---|---:|---|
| nozzle bore diameter `nozzle_d_mm` | 7.9 | historical experimental starting point (7.6–8.8) |
| feed pipe internal diameter `feed_d_mm` | 16 | exploratory |
| feed straight length `feed_length_mm` | 12 | exploratory |
| diaphragm thickness `diaphragm_thickness_mm` | 1.2 | exploratory; satisfies thickness <=0.2 nozzle diameter |
| mixing throat internal diameter `throat_d_mm` | 9.5 | historical approximate 9–10 |
| mixing throat length `throat_length_mm` | 85 | historical approximate |
| nozzle-to-throat axial gap `nozzle_to_throat_gap_mm` | 8 | exploratory; adjustable |
| suction chamber inlet diameter `suction_chamber_d_mm` | 16 | exploratory |
| side air port diameter `air_port_d_mm` | 5 | exploratory (3D only) |
| side air port length `air_port_length_mm` | 20 | exploratory (3D only) |
| deflector stand-off `deflector_standoff_mm` | 15 | exploratory |
| deflector radius `deflector_radius_mm` | 14 | exploratory |
| deflector axial length `deflector_length_mm` | 25 | exploratory |

### Axisymmetric wedge / OpenFOAM.com v2606

```bash
source /usr/lib/openfoam/openfoam2606/etc/bashrc
python3 -m cfd.patent_v04.generate --out-dir cfd/patent_v04/generated
CASE="$PWD/cfd/patent_v04/generated/diaphragm_ejector_open"
blockMesh -case "$CASE"
checkMesh -case "$CASE" -allTopology -allGeometry
interFoam -case "$CASE" -dry-run
```

Run full transient simulation only after successful checks; each generated case has `Allrun`. The water entrance is a **larger feeding section** ending in an annular diaphragm wall, with a thin water passage (aperture). This differs from the long, constant-bore cylindrical inlet in v0.3. `pcorr` and `pcorrFinal` entries address the OpenFOAM.com v2606 preflight issue discovered in WSL. Both open and closed air-boundary variants are generated.

The 2D model **idealizes air entry as a full annular inlet**. Default feed-inlet water velocity is **2.9251875 m/s**, selected to approximately match the v0.3 pure-water inlet volumetric flow of a 7.9 mm nozzle at 12 m/s: `U_feed = 12*(nozzle_d_mm/feed_d_mm)**2`. The target 12 m/s nozzle-bore speed is a continuity-based estimate, not a CFD result. A matched flow does NOT ensure matched inlet pressures/pump power; investigate pressure-driven inlet conditions in subsequent studies.

### Experimental 3D CAD + surface groups

```bash
python3 -m pip install gmsh
python3 -m cfd.patent_v04.geometry_3d --mesh-size-mm 1.0
```

The Gmsh OpenCASCADE model builds a coaxial water feed, thin diaphragm aperture, suction-chamber contraction, mixing throat and **one lateral air duct**, with fluid/waterInlet/airInlet/outlet/walls physical groups. This is a *meshing prototype*, NOT a solver-ready OpenFOAM case. It needs a working Gmsh runtime, inspection of boolean topology, `gmshToFoam`, checking/repairing patch type mappings, prescribed phase BCs, `checkMesh`, solver dry-run, flux audit, and 3D mesh convergence before CFD claims. A patent-faithful deflector and adjustable valve detail have not yet been meshed in 3D.

### Reporting requirements

Record source class for each parameter. Check spatial/time resolution, alpha boundedness, patch-normal fluxes including `ambientOpen`, **phase-resolved** (not mixture `phi`) air flux, reverse flow, density/compressibility limits, and transient storage. `k_phi = -sum(phi_airInlet)/-sum(phi_waterInlet)` is a screening **mixture** ratio, NOT a validated experimental air-to-water volumetric ratio. Distinct experimental regimes must be kept separate.

The mesh topology and solver behavior of the v0.4 generated cases are unverified by real OpenFOAM until the user runs the commands above in WSL. Python unit tests do not replace `blockMesh`/`checkMesh`/`interFoam`.
