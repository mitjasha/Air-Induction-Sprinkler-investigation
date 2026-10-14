# Publish this prepared project

The connected integration could read repositories but exposed no repository-creation tool. No remote repository was created and nothing was pushed.

The archive includes source, sample report, templates and CI, excluding virtual environments, caches and Git internals.

## 1. Verify locally

Extract the archive, open a terminal in sprinkler1d/, and activate a virtual environment as described in README.

    python -m pip install ".[dev]"
    pytest
    ruff check .
    python -m build
    sprinkler1d run --config examples/demo.json --output artifacts/demo

## 2. Create an empty repository

In GitHub create mitjasha/sprinkler1d, or choose another name. Choose the intended visibility. Do not prepopulate README, license or .gitignore; these are supplied.

## 3. Commit and push

From the extracted archive:

    git init -b main
    git add .
    git commit -m "Add reproducible sprinkler research demonstrator"
    git remote add origin https://github.com/mitjasha/sprinkler1d.git
    git push -u origin main

For the prepared local Git checkout, inspect git status and git log -1; skip initialization and initial commit if already present. Replace the remote URL if the owner/name differs.

## 4. Complete the portfolio entry

Wait for GitHub Actions before claiming remote CI passes. Suggested description: “Reduced-order air-entraining sprinkler: multiphysics modeling, inverse design and verification.” Topics: cfd, cae, multiphysics, scientific-computing, python, inverse-problems, irrigation.

Add verified dissertation/publication links. Preserve demonstrative status until independent measurements support stronger claims. A later release can receive an archival DOI; none is claimed now.
