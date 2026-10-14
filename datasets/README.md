# Dataset contract

demo/ contains synthetic records. validation/ contains header-only templates and an empty evidence manifest. There are no measured data in this release.

| Breakup CSV field | Meaning |
|---|---|
| run_id | Unique independent run; preserve replicate groups externally |
| split | calibration or holdout, chosen before fitting |
| provenance | synthetic or experimental; mixing is rejected |
| delta_m | Equivalent liquid edge-film thickness [m] |
| we_liquid | rho_l U² delta_l / sigma [-] |
| alpha | Retained air volume fraction [0,1) |
| d32_m | Sauter mean diameter [m] |
| sigma_d32_m | Positive standard uncertainty of measured d32 [m] |

At least five calibration and two holdout runs, full-rank design and an adequately conditioned Jacobian are required. This is a software minimum, not a sufficient experiment plan. Hold out independent series/geometries to assess transfer.

The fit assumes exact upstream inputs and independent response errors. Preserve raw measurements, calibration, processing scripts and units separately. Covariance is not a complete uncertainty budget.

Manifest requirements: source/owner, instrument IDs, geometry revision, acquisition/processing dates, units/reference conditions, replicate group, split policy, uncertainties, exclusions, checksum, license, reviewer and predeclared acceptance criteria.

A provenance label never automatically promotes a fit to validated.
