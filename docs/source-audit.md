# Sources and calibration data

## Sources used in the model

The bibliography covers eight publications on sprinkler design, air induction and droplet formation from 2017–2021. The [source register](references.json) records publication metadata, source URLs, access dates and PDF checksums. The [literature notes](literature.md) map the equations and published observations to the code.

The 2019 similarity criterion and the 2021 flow relations are implemented in `literature.py`, separately from the forward solver. The 2019 comparison retains the printed equation, the published table and a fixed C=0.001 correction hypothesis. The original calculation sheets are needed to resolve the discrepancy between the printed equation and the table.

The repository includes synthetic calibration records, a transcription of the published 2019 table and empty measurement templates. Raw bench measurements, dimensioned device drawings and CFD cases are not included.

## Data needed for further work

| Source or measurement | Use | Integration point |
|---|---|---|
| Dissertation and author’s abstract | Extend the equation references and device description | Bibliography and equation mapping |
| Original calculation sheets or erratum for 2019 Eqs. 18–20 | Resolve the C=0.001 hypothesis and unit interpretation | Literature APIs and eight-row comparison |
| Experiment reports and calibration certificates | Establish measurement uncertainty | Validation manifest |
| Raw water/air flows, pressures and temperatures | Identify ejector coefficients and test independent runs | Hydraulic CSV template |
| CAD, dimensioned drawings and adjustment settings | Define geometry and feasible design bounds | Case files and CFD geometry |
| Film thickness, velocity and gas fraction | Identify impact, friction and degassing coefficients | Film block and section profiles |
| Droplet images, size distributions and processing records | Determine d32, distribution width and processing bias | Breakup CSV and raw-data links |
| Catch-can layout, collection duration and volumes | Compare rainfall intensity and installation uniformity | Rainfall validation data |
| CFD cases, meshes and refinement studies | Compare internal flow and film profiles | CFD interface |

The air-inlet model uses ideal-gas flow relations; the numerical solvers use SciPy. Links to these implementation references are in the [README](../README.md).
