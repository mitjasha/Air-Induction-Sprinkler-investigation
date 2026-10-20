"""Compare v0.5 open/closed and mesh levels from per-case summary.json files.

Never claim validation based on RANS or mesh count alone.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
from pathlib import Path


def compare(study_dir: Path, report_dir: Path) -> dict:
    study_dir=Path(study_dir).expanduser().resolve()
    report_dir=Path(report_dir).expanduser().resolve()
    report_dir.mkdir(parents=True,exist_ok=True)
    levels=['coarse','medium','fine']
    modes=['open','closed']
    rows=[]
    for level in levels:
        for mode in modes:
            name=f'ejector_{level}_{mode}'
            result=study_dir/name/'report'/'summary.json'
            row={'case':name,'level':level,'air_mode':mode,
                 'has_report':result.exists(), 'k_phi':None,'kQ':None,
                 'quasi_steady':False,'relative_balance':None}
            if result.exists():
                v=json.loads(result.read_text(encoding='utf-8'))
                row.update(k_phi=v.get('k_phi_final'),kQ=v.get('kQ_phase_resolved'),
                    quasi_steady=v.get('flux_quasi_steady'),
                    relative_balance=v.get('final_relative_volume_balance'))
            rows.append(row)
    with (report_dir/'comparison.csv').open('w',newline='',encoding='utf-8') as out:
        cols=['case','level','air_mode','has_report','k_phi','kQ','quasi_steady','relative_balance']
        wr=csv.DictWriter(out,fieldnames=cols)
        wr.writeheader()
        wr.writerows(rows)
    by_name={x['case']:x for x in rows}
    changes={}
    for a,b in [('coarse','medium'),('medium','fine')]:
        aa=by_name[f'ejector_{a}_open']['k_phi']
        bb=by_name[f'ejector_{b}_open']['k_phi']
        if aa is not None and bb is not None and math.isfinite(aa) and math.isfinite(bb) and abs(bb)>1e-12:
            changes[f'{a}_to_{b}_open_kphi_rel_change']=abs(aa-bb)/abs(bb)
    with (report_dir/'comparison.md').open('w',encoding='utf-8') as out:
        out.write('# v0.5 mesh/turbulence & air-intake comparison\n\n')
        out.write('| Case | k_phi mixture | Real phase kQ | Temporal QC | Relative volume balance |\n')
        out.write('|---|---:|---:|---|---:|\n')
        for x in rows:
            ratio=f'{x["k_phi"]:.5f}' if x['k_phi'] is not None else 'NO DATA'
            quality='PASS (flux only)' if x['quasi_steady'] else 'NOT PASSED'
            b=f'{x["relative_balance"]:.3g}' if x['relative_balance'] is not None else '—'
            out.write(f'| {x["case"]} | {ratio} | NOT MEASURED | {quality} | {b} |\n')
        out.write('\n**Interpretation gate:** These are mixture flow ratios. Mesh agreement '
                  'in k_phi is not validation of real gas entrainment; inspect yPlus, '
                  'phase fluxes, pressure and interface evolution independently.\n')
        out.write('\n## Mesh sensitivity of mixture flux ratio\n\n')
        for k,v in changes.items():
            out.write(f'- {k}: {v:.2%}\n')
    return {'cases':len(rows),'reports':sum(1 for r in rows if r['has_report']),
            'mesh_relative_changes':changes, 'report':str(report_dir)}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--study-dir',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    args=ap.parse_args()
    print(json.dumps(compare(args.study_dir,args.report),indent=2))

if __name__=='__main__':
    main()
