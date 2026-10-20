"""Run a controlled sequential CFD experiment matrix, stopping at first failure.

By default ONLY preflights. Pass --solve to run transients; resource-intensive!
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .run import run_case


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--study-dir',type=Path,required=True)
    ap.add_argument('--cases',nargs='+',default=['ejector_coarse_open','ejector_coarse_closed'])
    ap.add_argument('--solve',action='store_true')
    ns=ap.parse_args()
    results=[]
    for name in ns.cases:
        audit=run_case(ns.study_dir,name,['mesh','check','dry']+(['solve'] if ns.solve else []))
        results.append(audit)
        print(f'{name}: {audit["status"]}',flush=True)
        if audit['status'].startswith('FAILED'):
            break
    print(json.dumps({'results':results},indent=2))
    if results and results[-1]['status'].startswith('FAILED'):
        raise SystemExit(1)

if __name__=='__main__':
    main()
