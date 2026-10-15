"""Reproduce the printed equations; expose rather than conceal discrepancies."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sprinkler1d.literature import criterion_2019, exponents_2019, control_flows_2021


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/literature")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    with (root / "datasets/literature/criterion2019_table1.csv").open() as file:
        rows = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(file)]
    for row in rows:
        diameter = row["nozzle_mm"] / 1000
        x1, x5 = exponents_2019(diameter)
        row["literal_equation_dk_mm"] = 1000 * criterion_2019(
            diameter, row["froude"], row["ohnesorge"], x1, x5
        )
        row["literal_to_reported_ratio"] = (
            row["literal_equation_dk_mm"] / row["reported_calculation_dk_mm"]
        )
    ratios = [r["literal_to_reported_ratio"] for r in rows]
    payload = {
        "status": "SOURCE_REPRODUCTION_DISCREPANCY",
        "source_doi": "10.29235/1817-7204-2019-57-2-230-237",
        "assumptions": "Printed Eqs.18-20; d0 in m; alpha=1; rounded Table 1 Oh and Fr",
        "diameter_definition": "dk as printed; not asserted to be d32",
        "data_kind": "literature_transcription_not_raw_measurements",
        "ratio_min": min(ratios),
        "ratio_max": max(ratios),
        "rows": rows,
        "control_demo_2021": control_flows_2021(0.001, 0.0005, 0.01, heads=12),
        "control_demo_provenance": "assumed numerical example, not a measured operating point",
    }
    (output / "audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    with (output / "comparison.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.7), layout="constrained")
    x = np.arange(1, len(rows) + 1)
    for key, label, color in [
        ("reported_experiment_dk_mm", "Experiment as reported in Table 1", "#126b87"),
        ("reported_calculation_dk_mm", "Calculation as reported in Table 1", "#de7c37"),
    ]:
        axes[0].plot(x, [r[key] for r in rows], "o--", label=label, color=color)
    axes[0].set(xlabel="Table 1 row", ylabel="Paper diameter dk [mm]", title="Published comparison")
    axes[0].legend(fontsize=8)
    axes[1].bar(x, ratios, color="#9e3e52")
    axes[1].axhline(1, color="black", linestyle="--", label="Exact reproduction")
    axes[1].set(
        yscale="log",
        xlabel="Table 1 row",
        ylabel="Literal / reported calculation",
        title="Printed-equation audit: unresolved discrepancy",
    )
    axes[1].legend(fontsize=8)
    fig.suptitle("2019 source audit · Literature transcription, not device validation", fontsize=13)
    fig.savefig(output / "comparison.png", dpi=180)
    plt.close(fig)
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
