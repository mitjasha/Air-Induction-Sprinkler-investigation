# CFD exchange contract v1

The package exports data and compares a section profile. It does not launch or supply a solved CFD case.

cfd_boundary.json contains schema_version=1, SI units, the case, phase mass flows, absolute outlet pressure and homogeneous outlet speed. Phase mass flows refer to ambient outlet conditions. Do not impose mass flow and velocity as independent constraints on the same patch; select suitable CFD boundary types and use the remaining quantities as comparison targets.

Coordinates: axisymmetric r outward, z upward. Geometry and patch names must be mapped by the CFD user.

## Section CSV

Required columns: r_m, velocity_ms, liquid_thickness_m, source, mesh_id.

Radii must be positive, strictly increasing and within the modeled film span. Speed and thickness must be positive and finite. No extrapolation is allowed. Source should identify case and averaging window; mesh_id identifies the versioned mesh.

Use equivalent liquid thickness from integrated liquid volume, not total aerated-layer thickness. Report a flux-compatible tangential speed. Record time/volume/phase-flux averaging and extraction sensitivity.

    sprinkler1d compare-cfd --config examples/demo.json --csv my_section.csv --output artifacts/comparison.json

Relative RMSE is a comparison metric, not experimental validation.

| Level | Appropriate questions | Independent checks |
|---|---|---|
| 2D axisymmetric | Mean suction, impact and film thickness | Mass balance, boundary sensitivity, systematic mesh refinement |
| 3D internal flow | Discrete ports, asymmetry and slip | Mesh/time refinement and measured pressures/flows |
| Transient 3D VOF | Sheet instability and ligaments | Interface resolution, time-window convergence, video |
| Particle tracking | Trajectories and deposition | Measured injection distributions and catch-can data |

Record cell counts, refinement ratios, timestep/Courant limits, turbulence/interface models, residual histories and integrated balances. Estimate discretization error only when the refinement sequence supports it.

Freeze upstream coefficients before fitting CFD-derived downstream closures. CFD and 1D can agree because they share inaccurate assumptions; agreement is not sufficient evidence of reality.
