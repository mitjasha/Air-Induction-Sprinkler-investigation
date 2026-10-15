# Release workflow

## Verify the checkout

From the repository root, activate the virtual environment described in the README and run:

    python -m pip install ".[dev]"
    ruff check .
    pytest
    python -m build
    sprinkler1d run --config examples/demo.json --output artifacts/demo
    python examples/literature_audit.py --output artifacts/literature

Review the generated report and literature comparison. Record the environment and results in `docs/local-verification.md` when updating the reference outputs.

## Prepare a release

1. Update the version in `pyproject.toml` and `CITATION.cff`, including the release date.
2. Update the README and roadmap to match the implemented calculations.
3. Include source data provenance, units and licenses for any new datasets.
4. Commit the changes and push the release branch to GitHub.
5. Check the Linux/Windows CI results before tagging the release.

Build artifacts are written to `dist/`. Keep virtual environments, caches and local calculation outputs out of the release archive.
