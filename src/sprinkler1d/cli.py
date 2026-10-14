"""Command line interface; invalid inputs and unmet synthesis targets exit nonzero."""

import argparse
import json
from pathlib import Path
from .config import Case


def main():
    parser = argparse.ArgumentParser(
        prog="sprinkler1d", description="Reduced-order sprinkler research demonstrator"
    )
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Generate a reproducible report")
    run.add_argument("--config", required=True)
    run.add_argument("--output", required=True)
    run.add_argument("--classes", type=int, default=128)
    run.add_argument("--bins", type=int, default=30)
    fit = sub.add_parser("calibrate", help="Fit breakup closure using labeled CSV")
    fit.add_argument("csv")
    fit.add_argument("--output", required=True)
    inv = sub.add_parser("synthesize", help="Select pressure and nozzle diameter")
    inv.add_argument("--config", required=True)
    inv.add_argument("--flow-l-min", type=float, required=True)
    inv.add_argument("--d32-mm", type=float, required=True)
    inv.add_argument("--output", required=True)
    uq = sub.add_parser("uncertainty")
    uq.add_argument("--config", required=True)
    uq.add_argument("--samples", type=int, default=100)
    uq.add_argument("--seed", type=int, default=42)
    uq.add_argument("--output", required=True)
    sub.add_parser("dimensions")
    cfd = sub.add_parser("compare-cfd")
    cfd.add_argument("--config", required=True)
    cfd.add_argument("--csv", required=True)
    cfd.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        if args.command == "run":
            from .report import create_report

            payload = create_report(Case.load(args.config), args.output, args.classes, args.bins)
        elif args.command == "calibrate":
            from .calibration import fit_breakup

            payload = fit_breakup(args.csv)
        elif args.command == "synthesize":
            from .inverse import synthesize

            payload = synthesize(Case.load(args.config), args.flow_l_min, args.d32_mm)
        elif args.command == "uncertainty":
            from .uncertainty import propagate

            payload = propagate(Case.load(args.config), args.samples, args.seed)
        elif args.command == "compare-cfd":
            from .cfd import compare_film
            from .solver import simulate

            payload = compare_film(args.csv, simulate(Case.load(args.config)))
        else:
            from .dimensions import audit

            payload = audit()
        if hasattr(args, "output") and args.command != "run":
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        if args.command == "synthesize" and not payload["target_met"]:
            raise SystemExit(2)
    except (ValueError, OSError, TypeError, KeyError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    main()
