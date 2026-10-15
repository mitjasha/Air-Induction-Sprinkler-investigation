# Publish this prepared project

Publication destination supplied by the author: https://github.com/mitjasha/Air-Induction-Sprinkler-investigation. The repository was empty when inspected. The commands below also document how to publish an extracted copy of the archive.

The archive includes source, sample report, templates and CI, excluding virtual environments, caches and Git internals.

## 1. Verify locally

Extract the archive, open a terminal in sprinkler1d/, and activate a virtual environment as described in README.

    python -m pip install ".[dev]"
    pytest
    ruff check .
    python -m build
    sprinkler1d run --config examples/demo.json --output artifacts/demo

## 2. Create an empty repository

For a new fork, create an empty repository under your account and substitute its URL below. For the author's published repository, clone it instead of initializing a separate history.

## 3. Commit and push

From the extracted archive:

    git init -b main
    git add .
    git commit -m "Add reproducible sprinkler research demonstrator"
    git remote add origin https://github.com/mitjasha/Air-Induction-Sprinkler-investigation.git
    git push -u origin main

For the prepared local Git checkout, inspect git status and git log -1; skip initialization and initial commit if already present. Replace the remote URL if the owner/name differs.

## 4. Complete the portfolio entry

Wait for GitHub Actions before claiming remote CI passes. Suggested description: “Reduced-order air-entraining sprinkler: multiphysics modeling, inverse design and verification.” Topics: cfd, cae, multiphysics, scientific-computing, python, inverse-problems, irrigation.

Verified publication links and their code mapping are already included. Add the dissertation and raw experimental provenance when available. Preserve demonstrative status until independent measurements support stronger claims. A later release can receive an archival DOI; none is claimed now.
