"""Single-factor geometric screening matrix at one grid, without launching solver.

Initial exploratory values are not historical patent measurements.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .generate import HERE, modify_case
from cfd.baseline_v03.generate import write_case

DEFAULT_SWEEP = {
    'nozzle_d_mm':[7.6,7.9,8.2,8.6,8.8],
    'nozzle_to_throat_gap_mm':[4,8,12],
    'throat_d_mm':[9.0,9.5,10.0],
    'throat_length_mm':[60,85,110],
}


def build_sweep(out_dir: Path, config: Path | None = None,grid: str='coarse',
                air_mode: str='open',max_cases: int=30) -> list[dict]:
    path=(config or HERE/'study_config.json').resolve()
    study=json.loads(path.read_text(encoding='utf-8'))
    geo=json.loads((path.parent/study['geometry_config']).resolve().read_text(encoding='utf-8'))
    if grid not in study['mesh_levels'] or air_mode not in ('open','closed'):
        raise ValueError('Invalid grid or air_mode')
    out_dir=Path(out_dir).expanduser().resolve()
    rows=[]
    for parameter, values in DEFAULT_SWEEP.items():
        for value in values:
            if abs(value-geo[parameter])<1e-9:continue
            if len(rows)>=max_cases:raise ValueError('Screening matrix exceeds max_cases')
            cfg={**geo,**study['mesh_levels'][grid],parameter:value,
                 'air_mode':air_mode,'end_time_s':study['end_time_s']}
            slug=str(value).replace('.','p')
            name=f'{parameter.replace("_mm", "")}_{slug}_{grid}_{air_mode}'
            case=out_dir/name
            meta=write_case(cfg,case)
            meta['grid_level']=grid
            meta['parameter_varied']=parameter
            meta['parameter_value']=value
            meta['baseline_parameter_value']=geo[parameter]
            modify_case(case,cfg,study,meta)
            rows.append({'case':name,'parameter':parameter,'value':value,
                         'baseline':geo[parameter],'cells_estimated':meta['mesh']['cells_estimate']})
    out_dir.mkdir(parents=True,exist_ok=True)
    (out_dir/'sweep_manifest.json').write_text(json.dumps({'cases':rows,
        'model':study['model'],'baseline_geometry':geo,'experimental_status':'UNRUN_PARAMETRIC_HYPOTHESES'},
        indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return rows


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir',type=Path,required=True)
    ap.add_argument('--config',type=Path)
    ap.add_argument('--grid',choices=['coarse','medium','fine'],default='coarse')
    ap.add_argument('--air-mode',choices=['open','closed'],default='open')
    args=ap.parse_args()
    print(json.dumps(build_sweep(args.out_dir,args.config,args.grid,args.air_mode),indent=2))

if __name__=='__main__':main()
