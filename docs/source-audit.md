# Source audit — 2026-10-15

## Actually available

- The linked discussion “Критериальное уравнение капель”: a conceptual chain, proposed equations and a verification-matrix proposal. Read as background, not a peer-reviewed source or measured dataset.
- The local project reference directory sources/ was empty.
- No earlier sprinkler1d package was found in the accessible workspace.
- The user supplied mitjasha/Air-Induction-Sprinkler-investigation as the publication destination. It had no Git refs when inspected; no existing sprinkler source code was reused.
- Eight relevant publications were located and their PDFs obtained from university/journal sites. See references.json for metadata, URLs, access date and PDF SHA-256, and literature.md for the exact use of each source.
- Existing unrelated topology-optimization portfolio files were not incorporated.

## Missing sources and integration points

| Missing item | Needed for | Integration point |
|---|---|---|
| Dissertation and exact title/year/institution | Trace equations to the author's work | Bibliography and equation mapping |
| Author's abstract (автореферат) | Confirm novelty and defended claims | Source register and README |
| Author calculation sheets / erratum for 2019 Eqs.18–20 | Confirm or reject the fixed C=0.001 hypothesis; distinguish unit-label error from missing prefactor | Both original and hypothesis APIs in literature.py; eight-row literature audit |
| Experiment reports and calibration certificates | Measurement uncertainty | Validation manifest |
| Raw water/air flows, pressures and temperature CSV | Ejector identification and holdout | Hydraulic CSV template |
| CAD / dimensioned drawings / adjustment mechanism | Geometry and feasible design bounds | Case files and CFD provenance |
| Film thickness, speed and gas fraction | Impact/friction/degassing identification | Film block and section profiles |
| Raw droplet images/distributions and processing | d32, distribution width and bias | Breakup CSV plus raw-data links |
| Catch-can layout, duration and volumes | I(r) and installation CU | Rainfall validation data |
| CFD cases, meshes and refinement studies | Numerical comparison | CFD exchange contract |
| Earlier sprinkler1d archive/repository and license | Migration and comparison | Compatibility review before reuse |

No missing source was reconstructed from memory. No dissertation coefficient, experimental accuracy, publication, DOI or scientific novelty was invented.

External methodological references checked: NASA Glenn's compressible-flow explanation and official SciPy documentation, linked in README. These do not validate the device.
