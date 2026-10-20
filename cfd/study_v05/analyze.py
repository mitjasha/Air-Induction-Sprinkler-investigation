# ruff: noqa: E701, E702, E703
"""Turn OpenFOAM logs and ParaView CSV profiles into reproducible QC reports.

This does NOT infer phase-specific flow from mixture flux alone.

Example:
 python -m cfd.study_v05.analyze --case ~/CAE/CFD-runs/patent_v05/ejector_coarse_open \
   --report ~/CAE/CFD-reports/coarse_open --profiles axis=axis_profile.csv wall=wall_profile.csv

Required: numpy, matplotlib. Profiles are optional.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
from collections import defaultdict
from pathlib import Path

import numpy as np

PATCHES = {'airInlet':'airInlet','waterInlet':'waterInlet',
           'ambientOpen':'ambientOpen','outlet':'outlet'}
TIME = re.compile(r'^Time\s*=\s*([\d.eE+\-]+)\s*$')
FLUX = re.compile(r'\bsum\((airInlet|waterInlet|ambientOpen|outlet)\)\s+of\s+phi\s*=\s*([\d.eE+\-]+)')


def parse_flux_logs(files: list[Path]) -> list[dict]:
    """Read OpenFOAM console logs (supports restart; latest log wins for duplicate time)."""
    times = {}
    for file in files:
        t = None
        for line in Path(file).read_text(encoding='utf-8',errors='replace').splitlines():
            mt = TIME.match(line.strip())
            if mt:
                t = float(mt.group(1))
            mf = FLUX.search(line)
            if mf and t is not None:
                row = times.setdefault(t, {'time_s':t})
                row[mf.group(1)] = float(mf.group(2))
    output = []
    for t,row in sorted(times.items()):
        if all(key in row for key in PATCHES):
            qw = -row['waterInlet']
            qa = -row['airInlet']
            ambient = -row['ambientOpen']
            qout = row['outlet']
            row['k_phi'] = qa/qw if qw>0 else math.nan
            row['balance_m3_s'] = row['airInlet']+row['waterInlet']+row['ambientOpen']+qout
            row['balance_relative'] = row['balance_m3_s']/qw if qw>0 else math.nan
            row['additional_ambient_in_m3_s'] = ambient
            output.append(row)
    return output


def parse_foam_function_object(case: Path) -> list[dict]:
    """Optional fallback for postProcessing/..../surfaceFieldValue.dat on different OpenFOAM releases."""
    collected: dict[float,dict] = defaultdict(dict)
    mapping = {'inletOutletFlux':'airInlet','waterInletFlux':'waterInlet',
               'ambientFlux':'ambientOpen','exitFlux':'outlet'}
    for directory,patch in mapping.items():
        for file in sorted((case/'postProcessing'/directory).glob('*/surfaceFieldValue.dat')):
            for line in file.read_text(encoding='utf-8',errors='replace').splitlines():
                if not line.strip() or line.lstrip().startswith('#'):
                    continue
                parts = line.split()
                if len(parts)>=2:
                    try:
                        t,flux = float(parts[0]),float(parts[1])
                    except ValueError:
                        continue
                    collected[t][patch] = flux
    rows=[]
    for t, fluxes in sorted(collected.items()):
        if all(k in fluxes for k in PATCHES):
            qw=-fluxes['waterInlet']
            fluxes.update(time_s=t,k_phi=(-fluxes['airInlet']/qw if qw>0 else math.nan),
                 balance_m3_s=sum(fluxes[k] for k in PATCHES),
                 additional_ambient_in_m3_s=-fluxes['ambientOpen'],
                 balance_relative=sum(fluxes[k] for k in PATCHES)/qw if qw>0 else math.nan)
            rows.append(dict(fluxes))
    return rows


def qc_profile(path: Path) -> dict:
    with Path(path).open(newline='', encoding='utf-8-sig') as file:
        table=list(csv.DictReader(file))
    if not table or 'Points:2' not in table[0]:
        raise ValueError(f'Not a valid ParaView Plot Over Line export: {path}')
    cols = table[0].keys()
    points=[]
    for row in table:
        if float(row.get('vtkValidPointMask',1)) <= 0:
            continue
        p={'z_m':float(row['Points:2'])}
        for name in ('Points:0','Points:1','p_rgh','alpha.water','U:2'):
            if name in cols:
                p[name]=float(row[name])
        if all(math.isfinite(v) for v in p.values()):
            points.append(p)
    if not points:
        raise ValueError('No valid finite points')
    z=np.array([x['z_m'] for x in points])
    order=np.argsort(z)
    points=[points[i] for i in order]
    z=np.sort(z)
    out={'source_file':str(path), 'n_rows':len(table), 'n_valid':len(points),
         'z_min_mm':float(z[0]*1000), 'z_max_mm':float(z[-1]*1000),
         'radius_mm':float(points[0].get('Points:0',math.nan)*1000),
         'points':points}
    for key in ('p_rgh','alpha.water','U:2'):
        if key in points[0]:
            a=np.array([p[key] for p in points]);out[key+'_min']=float(np.min(a));out[key+'_max']=float(np.max(a))
    return out


def write_csv(path: Path, rows: list[dict], columns: list[str]):
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=columns,extrasaction='ignore');w.writeheader();w.writerows(rows)


def plot_series(out: Path, title: str, xlabel: str, ylabel: str, lines: list[tuple], filename: str):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax=plt.subplots(figsize=(9,4.5))
    for x,y,label in lines:
        ax.plot(x,y,label=label)
    ax.set(title=title,xlabel=xlabel,ylabel=ylabel)
    ax.grid(True,alpha=0.3)
    if len(lines)>1:ax.legend()
    fig.tight_layout();fig.savefig(out/filename,dpi=150);plt.close(fig)


def summarize(case: Path, report: Path, profiles: dict[str,Path] | None = None,
              log_glob: str='log.interFoam*', stability_window_s: float=0.01,
              stability_limit: float=0.05) -> dict:
    case=Path(case).expanduser().resolve()
    report=Path(report).expanduser().resolve();report.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((case/'case_manifest.json').read_text(encoding='utf-8')) if (case/'case_manifest.json').exists() else {}
    logs=sorted(set([*case.glob(log_glob),*case.glob('log.v05.solve')]))
    rows=parse_flux_logs(logs)
    source='console_logs'
    if not rows:
        rows=parse_foam_function_object(case);source='function_objects'
    values={'case':str(case),'flux_source':source,'n_flux_times':len(rows),
            'assumptions':{'model':manifest.get('turbulence_model','unknown'),
                'geometry':'2D annular-air approximation',
                'mixing_flux':'OpenFOAM phi, NOT phase air volumetric flow'},
            'kQ_phase_resolved':None,'mixing_shock_confirmed':False,
            'flux_quasi_steady':False,'profiles':{},'flags':[]}
    if rows:
        cols=['time_s','waterInlet','airInlet','ambientOpen','outlet','k_phi',
              'balance_m3_s','balance_relative','additional_ambient_in_m3_s']
        write_csv(report/'flux_history.csv',rows,cols)
        ts=np.array([r['time_s'] for r in rows]);q=np.array([r['k_phi'] for r in rows]);
        values['final_time_s']=float(ts[-1]);values['k_phi_final']=float(q[-1]);
        values['final_relative_volume_balance']=float(rows[-1]['balance_relative'])
        mask=ts>=ts[-1]-stability_window_s-1e-12
        # The closed intake has exactly zero k_phi by construction. Test a nonzero
        # diagnostic outlet flux instead; never interpret stationary k_phi=0 as proof.
        zero_air = (np.max(np.abs(np.array([r['airInlet'] for r in rows]))) < 1e-15)
        observable = np.array([r['outlet'] for r in rows]) if zero_air else q
        values['flux_quasi_steady_observable'] = 'outlet' if zero_air else 'k_phi'
        if mask.sum()>=3 and np.mean(np.abs(observable[mask]))>1e-15:
            var=float(np.ptp(observable[mask])/np.mean(np.abs(observable[mask])))
            values['flux_observable_window_relative_range']=var
            values['flux_quasi_steady']=bool(var<=stability_limit)
            if not zero_air:
                values['k_phi_window_relative_range']=var
            else:
                aux=np.array([r['ambientOpen'] for r in rows])
                secondary=float(np.ptp(aux[mask])/np.mean(np.abs(aux[mask]))) if np.mean(np.abs(aux[mask]))>1e-15 else None
                values['ambient_window_relative_range']=secondary
                values['ambient_window_stable']=(secondary is not None and secondary<=stability_limit)
                if not values['ambient_window_stable']:
                    values['flags'].append('Closed outlet is stable but ambientOpen has not passed flux-window check')
        else:
            values['flags'].append('Not enough valid nonzero samples in convergence window')
        plot_series(report, 'Mixture flux ratio (not physical kQ)', 'Time, s',
                    '|Phi_airInlet| / |Phi_waterInlet| (signed inlet ratio)',
                    [(ts,q,'k_phi')], 'k_phi_history.png')
        plot_series(report,'Signed boundary mixture fluxes','Time, s','Mixture phi, m3/s',
                    [(ts,np.array([r[p] for r in rows]),p) for p in PATCHES],
                    'boundary_fluxes.png')
        plot_series(report,'Mixture volume flux balance','Time, s','Net flux, m3/s',
                    [(ts,np.array([r['balance_m3_s'] for r in rows]),'net')],
                    'flux_balance.png')
        if abs(values['final_relative_volume_balance'])>0.01:
            values['flags'].append('Net mixture flux at last time exceeds 1% of water inlet')
    else:
        values['flags'].append('No complete four-patch flux history found')
    profiles = profiles or {}
    profiles_good={}
    for label,path in profiles.items():
        p=qc_profile(Path(path))
        profiles_good[label]=p
        values['profiles'][label]={k:v for k,v in p.items() if k!='points'}
        if p['z_max_mm']<89.5:values['flags'].append(f'{label}: axial profile ends before 90 mm')
        if p['n_valid']<p['n_rows']:
            values['flags'].append(f'{label}: {p["n_rows"]-p["n_valid"]} invalid ParaView points')
    for key, unit, filename in [('p_rgh','Pa','axial_pressure.png'),
                                ('alpha.water','water volume fraction','axial_water_fraction.png'),
                                ('U:2','m/s','axial_velocity_z.png')]:
        lines=[(np.array([p['z_m']*1000 for p in v['points']]),
                np.array([p[key] for p in v['points']]), f'{label} (r={v["radius_mm"]:.2f} mm)')
               for label,v in profiles_good.items() if key in v['points'][0]]
        if lines: plot_series(report,key+' along throat','Axial coordinate z, mm',unit,lines,filename)
    if profiles_good and len(profiles_good)<3:
        values['flags'].append('Two axial samples do not resolve radial interface evolution or mixing shock')
    if not profiles_good:
        values['flags'].append('No axial/radial profile CSV supplied: mixing shock cannot be evaluated')
    values['flags'].append('No conservative phase-resolved air flux: true kQ cannot be reported')
    values['flags'].append('No mesh/time/turbulence validation: no quantitative physical validation')
    # Face flux audits are read only from solver-saved fields at identical times.
    # Do not map interpolated ParaView samples to a conservative phase flux.
    from cfd.study_v05.phase_flux import calculate as phase_calculate
    phase = phase_calculate(case, report)
    from cfd.study_v05.wall_qc import audit as wall_audit
    wall=wall_audit(case,report)
    values['wall_yplus_passed'] = wall['near_wall_resolution_satisfied']
    values['phase_face_flux_audit'] = phase['status']
    values['kQ_phase_boundary_candidate'] = phase.get('kQ_phase_boundary_candidate')
    values['kQ_phase_resolved'] = phase.get('kQ_phase_resolved')
    if phase.get('rows') == 0:
        values['flags'].append('No saved MULES alphaPhi0.water + phi face-flux pair: phase balance unavailable')
    (report/'summary.json').write_text(json.dumps(values,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    with (report/'report.md').open('w',encoding='utf-8') as f:
        f.write('# CFD v0.5 automatic diagnostic report\n\n')
        f.write(f'Case: `{case}`\n\nFlux histories: {len(rows)} times; source: {source}.\n\n')
        if rows:
            f.write(f'Last time: {values["final_time_s"]:.6g} s; '
                    f'k_phi={values["k_phi_final"]:.5g} (**mixture ratio, not kQ**); '
                    f'last relative volume imbalance={values["final_relative_volume_balance"]:.3g}.\n\n')
            f.write(f'Quasi-steady by selected mixture-flux observable only: {values["flux_quasi_steady"]}.\n\n')
        f.write('**Mixing shock: NOT CONFIRMED.** A jump in a sampled curve is insufficient evidence.\n\n')
        f.write('## Flags and missing evidence\n\n')
        for flag in values['flags']:f.write(f'- {flag}\n')
        f.write('\n## Outputs\n\n`summary.json`, `flux_history.csv` (when available), '
                '`k_phi_history.png`, `boundary_fluxes.png`, `flux_balance.png`, '
                'and axial profile figures (when supplied).\n')
    return values


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--profiles',nargs='*',default=[],help='label=/path/to/file.csv')
    ap.add_argument('--log-glob',default='log.interFoam*')
    ap.add_argument('--window-s',type=float,default=0.01)
    args=ap.parse_args()
    profiles=dict(item.split('=',1) for item in args.profiles)
    result=summarize(args.case,args.report,profiles,args.log_glob,args.window_s)
    print(json.dumps({k:v for k,v in result.items() if k!='profiles'},indent=2,ensure_ascii=False))

if __name__=='__main__':main()
