# Applicability and limitations

**No experimentally validated operating range exists in this release.**

The example is water/air near 293.15 K and 101325 Pa, gauge pressure 200 kPa, a 4 mm nozzle, 8 mm mixing section, 1 mm² air opening, radial film from 10 to 25 mm, 1.5 m height and 25° launch. These are invented inputs, not recovered device dimensions.

Synthesis searches 80–350 kPa and 2.5–min(5.5, 0.8*mixing diameter in mm) mm. This is a computational design box, not validated manufacturing or operating limits. The forward solver accepts other SI values if its mathematical checks pass.

Hard guards: finite inputs, positive dimensions/properties, coefficient ranges, suction pressure above 1.01 times user-specified vapor pressure, bracketed entraining root, hydraulic energy upper bound, film speed above 0.05 m/s, d32 between 10 µm and 10 mm, and ground impact within 120 s. These are numerical gates, not safety limits.

Exclusions:

- Phase slip, realistic pressure recovery, coupled gas energy, cavitation dynamics and transient entrainment.
- Real deflector curvature, roughness correlations, film instability eigenmodes and measured gas retention.
- Non-spherical drops, secondary breakup, evaporation, heat/mass transfer, wind and collective spray dynamics.
- Rotating heads, installation overlap, terrain, soil infiltration, controller/actuator dynamics.
- Structural verification, manufacturing tolerances and field certification.

The spherical-drag approximation becomes uncertain for deformable drops; the report flags classes above 2 mm. A thickness/radius ratio above 0.1 flags questionable film slenderness. Neither threshold is a validated device boundary.

Finite diameter quadrature truncates lognormal tails. Rain histograms and single-head CU depend on class count, bin count and wet-disk definition. Mean range convergence does not prove CU convergence.

Calibration estimates breakup parameters only. Upstream parameters are fixed user inputs. Experimental records still require calibration certificates, independent holdout, error covariance and applicability review before validation claims.

## Publication-specific limits added 2026-10-15

The 2019 source formula does not reproduce its table under the documented literal SI interpretation. It is isolated in literature.py and excluded from forward/inverse design. The 2021 device description includes direct post-deflector breakup in aerated operation; the solver's film/breakup chain requires regime verification. See [literature audit](literature.md). Published observations are not validation of the newly implemented model.
