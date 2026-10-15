# Model architecture

```mermaid
flowchart LR
    C[Typed SI case] --> E[1D ejector momentum root]
    E --> F[Quasi-1D radial film ODE]
    F --> B[Dimensionless breakup closure]
    B --> T[Droplet trajectory ODEs]
    T --> R[Conservative annular rainfall]
    R --> O[HTML report and CSV figures]
    D[Labeled calibration and holdout CSV] --> I[Identification]
    I -. fitted closure .-> B
    S[Target flow and drop size] --> X[Bounded inverse synthesis]
    X --> C
    E <-. SI JSON and section CSV .-> CFD[2D and 3D CFD interface]
    F <-. comparison .-> CFD
```

Block dataclasses expose intermediate states; input Case objects are immutable. The solver composes the blocks without hidden global calibration state. Report generation is downstream of the physical solution.

The source-specific literature.py module is deliberately outside the forward chain. It exposes the unchanged 2019 printed equation, the separately named criterion_2019_c001_hypothesis API, and the 2021 flow-accounting contract. The correction hypothesis has a fixed dimensionless C=0.001 and returns SI metres. Both 2019 variants and the purely kinematic control relations remain separate from the solver's physical blocks.
