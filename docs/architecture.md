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

The source-specific literature.py module is deliberately outside the forward chain. It exposes the 2019 printed-equation audit and the 2021 flow-accounting contract. Neither the unresolved correlation nor the purely kinematic control relations are substituted for the solver's physical blocks.
