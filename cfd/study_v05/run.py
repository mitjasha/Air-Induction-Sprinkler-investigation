"""Sequential, checked OpenFOAM case runner; never claims an unrun case passed.

Usage: python -m cfd.study_v05.run --study-dir ~/CAE/CFD-runs/patent_v05 --case ejector_coarse_open --steps mesh check dry
Use --steps mesh check dry solve after a successful preflight and resource review.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

STEPS = {'mesh': ['blockMesh'], 'check': ['checkMesh', '-allTopology', '-allGeometry'],
         'dry': ['interFoam', '-dry-run'], 'solve': ['interFoam']}


def run_case(study_dir: Path, name: str, steps: list[str]) -> dict:
    study_dir = study_dir.expanduser().resolve()
    case = (study_dir / name).resolve()
    if case.parent != study_dir or not (case/'case_manifest.json').exists():
        raise ValueError('Unknown case directory; generate cases before running')
    if any(x not in STEPS for x in steps):
        raise ValueError('Unknown step')
    meta = json.loads((case/'case_manifest.json').read_text(encoding='utf-8'))
    audit = {'case':name,'started_utc':datetime.now(timezone.utc).isoformat(),
             'solver_path':shutil.which('interFoam'), 'steps':[], 'status':'IN_PROGRESS'}
    for step in steps:
        args = STEPS[step]
        if not shutil.which(args[0]):
            raise RuntimeError(f'Missing {args[0]}: source OpenFOAM bashrc first')
        log = case/f'log.v05.{step}'
        with log.open('w', encoding='utf-8') as stream:
            p = subprocess.run(args, cwd=case, stdout=stream, stderr=subprocess.STDOUT,
                               env=os.environ.copy(), check=False)
        line = {'step':step,'exit_code':p.returncode,'log':str(log)}
        audit['steps'].append(line)
        if p.returncode != 0:
            audit['status'] = 'FAILED'
            break
        if step == 'mesh' and not (case/'constant/polyMesh/points').exists():
            audit['status'] = 'FAILED_MISSING_MESH'
            break
        if step == 'check' and 'Mesh OK.' not in log.read_text(encoding='utf-8',errors='replace'):
            audit['status'] = 'FAILED_MESH_QUALITY'
            break
        if step == 'solve' and not log.read_text(encoding='utf-8',errors='replace').rstrip().endswith('End'):
            audit['status'] = 'FAILED_NO_SOLVER_END'
            break
    else:
        audit['status'] = 'SOLVED_UNVALIDATED' if 'solve' in steps else 'PREFLIGHT_PASSED'
    audit['completed_utc'] = datetime.now(timezone.utc).isoformat()
    (case/'run_audit.json').write_text(json.dumps(audit,indent=2)+'\n', encoding='utf-8')
    return audit


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--study-dir',type=Path,required=True)
    ap.add_argument('--case',required=True)
    ap.add_argument('--steps',nargs='+',choices=list(STEPS),default=['mesh','check','dry'])
    ns=ap.parse_args()
    r=run_case(ns.study_dir,ns.case,ns.steps)
    print(json.dumps(r,indent=2))
    if r['status'].startswith('FAILED'):
        raise SystemExit(1)

if __name__=='__main__':
    main()
