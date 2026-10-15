"""Compare the printed 2019 equation with the unconfirmed C=0.001 hypothesis."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from sprinkler1d.literature import (
    criterion_2019,
    criterion_2019_c001_hypothesis,
    exponents_2019,
    control_flows_2021,
)


def comparison_metrics(predicted, reference):
    error = np.asarray(predicted) - np.asarray(reference)
    return {
        "mae_mm": float(np.mean(np.abs(error))),
        "rmse_mm": float(np.sqrt(np.mean(error**2))),
        "mape_percent": float(np.mean(np.abs(error / reference)) * 100),
        "max_absolute_relative_error_percent": float(np.max(np.abs(error / reference)) * 100),
    }


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
        hypothesis = 1000 * criterion_2019_c001_hypothesis(
            diameter, row["froude"], row["ohnesorge"], x1, x5
        )
        row["hypothesis_c001_dk_mm"] = hypothesis
        row["hypothesis_minus_reported_calculation_mm"] = (
            hypothesis - row["reported_calculation_dk_mm"]
        )
        row["hypothesis_vs_reported_calculation_error_percent"] = 100 * (
            hypothesis / row["reported_calculation_dk_mm"] - 1
        )
        row["hypothesis_minus_reported_experiment_mm"] = (
            hypothesis - row["reported_experiment_dk_mm"]
        )
        row["hypothesis_vs_reported_experiment_error_percent"] = 100 * (
            hypothesis / row["reported_experiment_dk_mm"] - 1
        )
        # Implied per-row C is diagnostic only; it is never used for prediction.
        row["implied_c_for_exact_reported_calculation"] = 1 / row["literal_to_reported_ratio"]
        # Precision-only bounds, assuming round-to-nearest for displayed Oh/Fr.
        # These are not measurement uncertainties or statistical confidence bounds.
        row["hypothesis_precision_lower_mm"] = 1000 * criterion_2019_c001_hypothesis(
            diameter, row["froude"] - 0.5, row["ohnesorge"] + 0.00005, x1, x5
        )
        row["hypothesis_precision_upper_mm"] = 1000 * criterion_2019_c001_hypothesis(
            diameter, row["froude"] + 0.5, row["ohnesorge"] - 0.00005, x1, x5
        )
        row["compatible_with_display_rounding"] = (
            row["hypothesis_precision_lower_mm"] <= row["reported_calculation_dk_mm"] + 0.005
            and row["hypothesis_precision_upper_mm"] >= row["reported_calculation_dk_mm"] - 0.005
        )
    ratios = [r["literal_to_reported_ratio"] for r in rows]
    hypothesis_values = np.array([r["hypothesis_c001_dk_mm"] for r in rows])
    published_calculation = np.array([r["reported_calculation_dk_mm"] for r in rows])
    published_experiment = np.array([r["reported_experiment_dk_mm"] for r in rows])
    payload = {
        "status": "UNCONFIRMED_CORRECTION_HYPOTHESIS_COMPARISON",
        "validation_status": "NOT_VALIDATED",
        "literal_status": "SOURCE_REPRODUCTION_DISCREPANCY",
        "hypothesis": {
            "dimensionless_c": 0.001,
            "status": "HYPOTHESIS_NOT_CONFIRMED_ERRATUM",
            "selection": "fixed unit-scale hypothesis; not fitted in this audit",
            "excluded_from_forward_and_inverse_solver": True,
        },
        "source_doi": "10.29235/1817-7204-2019-57-2-230-237",
        "assumptions": "Printed Eqs.18-20; d0 in m; alpha=1; rounded Table 1 Oh and Fr",
        "diameter_definition": "dk as printed; not asserted to be d32",
        "data_kind": "literature_transcription_not_raw_measurements",
        "ratio_min": min(ratios),
        "ratio_max": max(ratios),
        "hypothesis_vs_published_calculation": comparison_metrics(
            hypothesis_values, published_calculation
        ),
        "hypothesis_vs_reported_experiment": comparison_metrics(
            hypothesis_values, published_experiment
        ),
        "rounding_assumptions": {
            "rule": "round-to-nearest; independent displayed-value bounds",
            "ohnesorge_half_step": 0.00005,
            "froude_half_step": 0.5,
            "reported_calculation_half_step_mm": 0.005,
            "nozzle_and_exponent_rounding_included": False,
            "interpretation": "precision compatibility only, not measurement uncertainty",
            "compatible_rows": sum(r["compatible_with_display_rounding"] for r in rows),
        },
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
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.3), layout="constrained")
    x = np.arange(1, len(rows) + 1)
    axes[0].plot(
        x,
        [r["literal_equation_dk_mm"] for r in rows],
        "s-",
        color="#9e3e52",
        label="Literal printed equation (C=1)",
    )
    axes[0].plot(x, published_calculation, "o", color="#de7c37", label="Published calculation")
    axes[0].plot(
        x, hypothesis_values, "x", color="#168372", markersize=8, label="C=0.001 hypothesis"
    )
    axes[0].set(yscale="log", ylabel="Paper diameter dk [mm]", title="Original scale retained")
    axes[0].legend(fontsize=8)
    for key, label, color in [
        ("reported_experiment_dk_mm", "Reported experiment", "#126b87"),
        ("reported_calculation_dk_mm", "Published calculation", "#de7c37"),
        ("hypothesis_c001_dk_mm", "C=0.001 hypothesis", "#168372"),
    ]:
        for start, stop in [(0, 4), (4, 8)]:
            axes[1].plot(
                x[start:stop],
                [r[key] for r in rows[start:stop]],
                linestyle="--",
                label=label if start == 0 else None,
                color=color,
                marker="x" if key.startswith("hypothesis") else "o",
            )
    axes[1].set(ylabel="Paper diameter dk [mm]", title="Hypothesis at the published scale")
    axes[1].legend(fontsize=8)
    axes[2].bar(
        x - 0.18,
        [r["hypothesis_vs_reported_calculation_error_percent"] for r in rows],
        width=0.36,
        color="#168372",
        label="vs published calculation",
    )
    axes[2].bar(
        x + 0.18,
        [r["hypothesis_vs_reported_experiment_error_percent"] for r in rows],
        width=0.36,
        color="#126b87",
        label="vs reported experiment",
    )
    axes[2].axhline(0, color="black", linewidth=0.8)
    axes[2].set(
        ylabel="100 × (hypothesis / reference − 1) [%]", title="Two distinct comparison targets"
    )
    axes[2].legend(fontsize=8)
    for ax in axes:
        ax.set(xlabel="Table 1 row (1–4: 69 kPa; 5–8: 206 kPa)", xticks=x)
        ax.axvline(4.5, color="#94a3b8", linewidth=0.8, linestyle=":")
        ax.grid(axis="y", alpha=0.15)
    fig.suptitle(
        "2019 criterion · Original equation and C=0.001 correction hypothesis", fontsize=14
    )
    fig.supxlabel(
        "UNCONFIRMED HYPOTHESIS · Literature transcription · No independent validation",
        fontsize=10,
        color="#9e3e52",
    )
    fig.savefig(output / "comparison.png", dpi=180)
    fig.savefig(output / "comparison.svg")
    plt.close(fig)
    lines = [
        "# Eight-row comparison: unconfirmed C=0.001 hypothesis",
        "",
        "Original equation retained. All diameters below are in mm. Errors are signed.",
        "",
        "| Row | Nozzle | p [kPa] | Reported experiment | Published calculation | Literal C=1 | Hypothesis C=0.001 | Error vs calculation [%] | Error vs experiment [%] |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for i, row in enumerate(rows, 1):
        lines.append(
            f"| {i} | {row['nozzle_mm']:.2f} | {row['pressure_kpa']:.0f} | "
            f"{row['reported_experiment_dk_mm']:.2f} | {row['reported_calculation_dk_mm']:.2f} | "
            f"{row['literal_equation_dk_mm']:.3f} | {row['hypothesis_c001_dk_mm']:.6f} | "
            f"{row['hypothesis_vs_reported_calculation_error_percent']:+.3f} | "
            f"{row['hypothesis_vs_reported_experiment_error_percent']:+.3f} |"
        )
    for key, label in [
        ("hypothesis_vs_published_calculation", "published calculation"),
        ("hypothesis_vs_reported_experiment", "reported experiment"),
    ]:
        metric = payload[key]
        lines += [
            "",
            f"Comparison with {label}: MAPE={metric['mape_percent']:.4f}%; "
            f"MAE={metric['mae_mm']:.6f} mm; RMSE={metric['rmse_mm']:.6f} mm; "
            f"maximum absolute relative error={metric['max_absolute_relative_error_percent']:.4f}%.",
        ]
    lines += [
        "",
        "All eight published calculation intervals overlap the hypothesis intervals "
        "under the explicitly assumed display-rounding bounds in audit.json. This is a "
        "precision compatibility check, not a measurement uncertainty assessment.",
        "",
        "C=0.001 is fixed for this hypothesis. Per-row implied C values in comparison.csv "
        "are diagnostics only. The original workbook or a confirmed erratum is still needed.",
        "",
        "Source: [2019 paper, Table 1 and Eqs.18–20](https://doi.org/10.29235/1817-7204-2019-57-2-230-237).",
        "",
    ]
    (output / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({k: v for k, v in payload.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
