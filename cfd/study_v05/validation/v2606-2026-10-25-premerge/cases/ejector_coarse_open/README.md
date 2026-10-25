# CFD v0.5 coarse / open

- turbulence: kOmegaSST; not yet OpenFOAM-verified
- geometry: assumed 2D annular intake, not actual lateral side port
- water feed: fixed volumetric-flow proxy, not matched pump pressure
- true phase kQ, yPlus and mixing-shock evidence: not validated
- all run evidence in log.v05.*, run_audit.json and postProcessing
See cfd/study_v05/README.md for research procedures.
