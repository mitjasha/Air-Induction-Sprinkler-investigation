"""Portable HTML report, scientific figure and exact provenance manifest."""

from dataclasses import asdict, replace
from pathlib import Path
import base64
import hashlib
import html
import importlib.metadata
import json
import platform
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from .solver import simulate
from .ejector import solve as ejector
from .film import solve as film
from .breakup import solve as breakup
from .uncertainty import propagate
from .dimensions import audit
from .cfd import export_boundary


def create_report(case, output, classes=128, bins=30):
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    result = simulate(case, classes=classes, bins=bins)
    summary = result.summary()
    uncertainty = propagate(case)
    config_text = json.dumps(asdict(case), indent=2, sort_keys=True)
    (out / "case.json").write_text(config_text, encoding="utf-8")
    manifest = {
        "package_version": importlib.metadata.version("sprinkler1d"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "dependencies": {
            p: importlib.metadata.version(p) for p in ["numpy", "scipy", "matplotlib", "pint"]
        },
        "case_sha256": hashlib.sha256(config_text.encode()).hexdigest(),
        "classes": classes,
        "bins": bins,
        "uncertainty": uncertainty,
        "dimension_audit": audit(),
        "result": summary,
        "data_provenance": "Synthetic inputs; no experimental measurements used",
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    export_boundary(case, result, out / "cfd_boundary.json")
    np.savetxt(
        out / "film.csv",
        np.column_stack(
            [
                result.film.radius_m,
                result.film.velocity_ms,
                result.film.liquid_thickness_m,
                result.film.alpha,
            ]
        ),
        delimiter=",",
        header="r_m,velocity_ms,liquid_thickness_m,alpha",
        comments="",
    )
    np.savetxt(
        out / "rain.csv",
        np.column_stack(
            [result.rain.edges_m[:-1], result.rain.edges_m[1:], result.rain.intensity_mm_h]
        ),
        delimiter=",",
        header="r_inner_m,r_outer_m,intensity_mm_h",
        comments="",
    )
    np.savetxt(
        out / "drops.csv",
        np.column_stack(
            [
                result.drops.diameter_m,
                result.drops.volume_fraction,
                [f.range_m for f in result.flights],
            ]
        ),
        delimiter=",",
        header="diameter_m,volume_fraction,range_m",
        comments="",
    )
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.titleweight": "bold",
            "axes.labelcolor": "#334155",
            "text.color": "#0f172a",
            "axes.edgecolor": "#cbd5e1",
            "grid.alpha": 0.2,
        }
    )
    fig, axs = plt.subplots(2, 3, figsize=(15, 8.8), layout="constrained")
    fig.patch.set_facecolor("#f8fafc")
    fig.suptitle(
        "SPRINKLER1D  /  Air-entraining sprinkler\nDemonstrative model · no experimental validation",
        fontsize=21,
        fontweight="bold",
    )
    teal, blue, orange = "#0d9488", "#2563eb", "#ea580c"
    f, d, r = result.film, result.drops, result.rain
    axs[0, 0].plot(f.radius_m * 1000, f.velocity_ms, color=teal, lw=2.6)
    axs[0, 0].set(
        title="01  Radial film transport", xlabel="Radius [mm]", ylabel="Film speed [m/s]"
    )
    axs[0, 1].plot(
        f.radius_m * 1000,
        f.liquid_thickness_m * 1000,
        label="Liquid equivalent",
        color=blue,
        lw=2.5,
    )
    axs[0, 1].plot(
        f.radius_m * 1000, f.mixture_thickness_m * 1000, label="Aerated layer", color=teal, lw=2.5
    )
    axs[0, 1].set(title="02  Film continuity", xlabel="Radius [mm]", ylabel="Thickness [mm]")
    axs[0, 1].legend(frameon=False)
    axs[0, 2].plot(d.diameter_m * 1000, np.cumsum(d.volume_fraction), color=blue, lw=2.5)
    axs[0, 2].axvline(d.d32_m * 1000, color=orange, ls="--", label=f"d32 = {d.d32_m * 1000:.3f} mm")
    axs[0, 2].set(
        title="03  Volume distribution",
        xlabel="Drop diameter [mm]",
        ylabel="Cumulative volume fraction",
    )
    axs[0, 2].legend(frameon=False)
    for idx in np.linspace(0, len(result.flights) - 1, 6, dtype=int):
        flight = result.flights[idx]
        axs[1, 0].plot(
            flight.path[:, 0], flight.path[:, 1], label=f"{d.diameter_m[idx] * 1000:.2f} mm"
        )
    axs[1, 0].set(
        title="04  Still-air trajectories", xlabel="Radial position [m]", ylabel="Height [m]"
    )
    axs[1, 0].legend(fontsize=8, frameon=False, ncol=2)
    axs[1, 1].stairs(r.intensity_mm_h, r.edges_m, color=teal, fill=True, alpha=0.65)
    axs[1, 1].set(
        title="05  Conservative deposition", xlabel="Radius [m]", ylabel="Rainfall [mm/h]"
    )
    pressures = np.linspace(80, 350, 24)
    diameters = []
    for pressure in pressures:
        try:
            c = replace(case, pressure_pa=pressure * 1000)
            diameters.append(breakup(c, film(c, ejector(c))).d32_m * 1000)
        except ValueError:
            diameters.append(np.nan)
    axs[1, 2].plot(pressures, diameters, color=orange, lw=2.5)
    axs[1, 2].set_xlim(pressures[0], pressures[-1])
    invalid = pressures[~np.isfinite(diameters)]
    if invalid.size:
        axs[1, 2].axvspan(invalid[0], pressures[-1], color="#cbd5e1", alpha=0.4)
        axs[1, 2].text(
            0.97,
            0.95,
            "Shaded: no admissible root",
            ha="right",
            va="top",
            transform=axs[1, 2].transAxes,
            fontsize=8,
        )
    axs[1, 2].scatter([case.pressure_pa / 1000], [d.d32_m * 1000], color=blue, zorder=3)
    axs[1, 2].set(
        title="06  Operating-pressure sweep",
        xlabel="Gauge pressure [kPa]",
        ylabel="Predicted d32 [mm]",
    )
    for ax in axs.flat:
        ax.grid(True)
    fig.savefig(out / "overview.png", dpi=170)
    fig.savefig(out / "overview.svg")
    plt.close(fig)
    encoded = base64.b64encode((out / "overview.png").read_bytes()).decode()
    metrics = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{v:.8g}</td></tr>"
        for k, v in summary.items()
        if isinstance(v, (float, int))
    )
    warnings = "".join(f"<li>{html.escape(x)}</li>" for x in result.warnings)
    page = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>sprinkler1d | Demonstration report</title>
    <style>body{{font:16px/1.6 system-ui,sans-serif;color:#0f172a;background:#f1f5f9;margin:0}}main{{max-width:1100px;margin:auto;padding:48px 28px;background:white}}h1{{font-size:42px;line-height:1.15}}h2{{margin-top:36px}}.tag{{color:#9a3412;background:#ffedd5;padding:8px 14px;border-radius:8px;font-weight:700}}img{{width:100%}}table{{border-collapse:collapse;width:100%}}td{{padding:8px;border-bottom:1px solid #e2e8f0}}td:last-child{{font-family:monospace}}pre{{white-space:pre-wrap;background:#f8fafc;padding:20px;font-size:12px}}</style>
    <main><span class="tag">DEMONSTRATIVE · NOT VALIDATED</span><h1>From air entrainment<br>to a rainfall footprint.</h1>
    <p>A reproducible reduced-order engineering calculation. All geometry and closure coefficients are illustrative. No measurement or dissertation result is reproduced.</p>
    <img alt="Six scientific plots of the demonstration case" src="data:image/png;base64,{encoded}">
    <h2>Engineering outputs and balance checks</h2><table>{metrics}</table>
    <h2>Interpretation</h2><p>The momentum root and liquid balances verify implementation consistency. They do not establish device accuracy. Air flow is referenced to ambient pressure and temperature. CU describes a single head over the modeled disk and is sensitive to binning; it is not the uniformity of a sprinkler installation.</p>
    <h2>Limitations</h2><ul>{warnings}<li>Homogeneous outlet closure neglects phase slip and internal gas-compression work. Hydraulic-to-kinetic power is an admissibility bound, not a full thermodynamic balance.</li><li>Horizontal radial film; prescribed lossless redirection at the edge. No wind, evaporation, droplet deformation, coalescence, or secondary breakup.</li></ul>
    <h2>Uncertainty scenarios</h2><p>Assumed parameter spreads only; these are not confidence intervals.</p><pre>{html.escape(json.dumps(uncertainty, indent=2))}</pre>
    <h2>Reproduce</h2><pre>sprinkler1d run --config case.json --output reproduced --classes {classes} --bins {bins}</pre>
    <h2>Provenance manifest</h2><pre>{html.escape(json.dumps(manifest, indent=2))}</pre></main></html>"""
    (out / "report.html").write_text(page, encoding="utf-8")
    return manifest
