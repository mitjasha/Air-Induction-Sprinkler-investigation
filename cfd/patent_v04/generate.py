# ruff: noqa: E701, E702, E703
"""Patent-informed CFD v0.4 case builder: thin diaphragm, feed, annular 2D air proxy.

Run: python -m cfd.patent_v04.generate --out-dir cfd/patent_v04/generated
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from cfd.baseline_v03.generate import write_case

HERE=Path(__file__).resolve().parent

def build(out_dir:Path, config:Path|None=None, *, deflector:bool=False):
    cfg=json.loads((config or HERE/'config_open.json').read_text())
    out_dir=Path(out_dir)
    reports=[]
    for mode in ('open','closed'):
        case_cfg={**cfg,'air_mode':mode}
        name='diaphragm_ejector_'+mode+('_deflector' if deflector else '')
        report=write_case(case_cfg,out_dir/name,with_deflector=deflector)
        report['status']='INPUTS_GENERATED_NOT_SOLVER_VALIDATED'
        report['geometry_basis']='Patent BY22927/BY22747 descriptions plus explicitly assumed parameters'
        (out_dir/name/'case_manifest.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        reports.append(report)
    return reports

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir',type=Path,default=HERE/'generated')
    ap.add_argument('--config',type=Path)
    ap.add_argument('--with-deflector',action='store_true')
    a=ap.parse_args()
    r=build(a.out_dir,a.config,deflector=a.with_deflector)
    print(json.dumps([{'case':x['parameters']['air_mode'],'mesh':x['mesh']} for x in r],indent=2))
