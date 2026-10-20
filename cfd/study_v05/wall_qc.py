"""Audit SST near-wall resolution using OpenFOAM yPlus function-object log lines.

Keep patch minima/maxima and report per-patch maximum; an empty patch is not a
1e300 physical yPlus. Solver logs, not mesh counts, establish actual yPlus.
"""
from __future__ import annotations
import argparse
import csv
import json
import re
from pathlib import Path

LINE = re.compile(r'patch\s+(\w+)\s+y\+\s*:\s*min\s*=\s*([-+\d.eE]+),\s*max\s*=\s*([-+\d.eE]+),\s*average\s*=\s*([-+\d.eE]+)')


def audit(case: Path, report: Path, target_yplus: float = 1.0) -> dict:
    case = Path(case).expanduser().resolve()
    report = Path(report).expanduser().resolve()
    report.mkdir(parents=True, exist_ok=True)
    latest = {}
    n = 0
    for log in sorted(case.glob('log.*'), key=lambda p: (p.stat().st_mtime, p.name)):
        for match in LINE.finditer(log.read_text(encoding='utf-8', errors='replace')):
            patch = match.group(1)
            y_min,y_max,y_mean = (float(x) for x in match.groups()[1:])
            if y_min > 1e100 or y_max < -1e100:
                continue
            latest[patch] = {'patch':patch, 'min':y_min, 'max':y_max,'mean':y_mean}
            n += 1
    data = list(latest.values())
    if data:
        with (report/'wall_yplus.csv').open('w', newline='', encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=('patch','min','max','mean'))
            writer.writeheader();writer.writerows(data)
    warnings = [f'{r["patch"]}: max y+ {r["max"]:.2f} exceeds near-wall target {target_yplus:g}'
                for r in data if r['max']>target_yplus]
    result = {'n_readings':n, 'patches':data, 'target_yplus':target_yplus,
              'near_wall_resolution_satisfied': bool(data) and not warnings,
              'flags':warnings if data else ['No valid yPlus readings in solver logs']}
    (report/'wall_qc.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--target-yplus',type=float,default=1.)
    args=parser.parse_args()
    print(json.dumps(audit(args.case,args.report,args.target_yplus),indent=2))


if __name__=='__main__':
    main()
