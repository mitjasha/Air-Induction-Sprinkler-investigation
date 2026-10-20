# ruff: noqa: E701, E702, E703
"""Reproducible temporal diagnostics of a suspected ejector pressure transition.

Input: directories profiles_t0p04/, profiles_t42ms/, etc, containing ParaView
PlotOverLine CSVs at r=1, r=4.5 mm and radial sections. No shock is assumed.
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np


def get_time(path: Path) -> float | None:
    match = re.fullmatch(r'profiles_t0p(\d+)', path.name)
    if match:
        return float('0.' + match.group(1))
    match = re.fullmatch(r'profiles_t(\d+)ms', path.name)
    if match:
        return int(match.group(1)) * 0.001
    return None


def load_profile(path: Path, xkey: str) -> tuple[np.ndarray, dict[str, np.ndarray], int]:
    with path.open(newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    if not rows or xkey not in rows[0]:
        raise ValueError(f'Invalid ParaView profile: {path}')
    good = [r for r in rows if int(float(r.get('vtkValidPointMask', 1))) == 1
            and all(math.isfinite(float(r[k])) for k in (xkey, 'p_rgh', 'U:2', 'alpha.water'))]
    if not good:
        raise ValueError(f'No finite, valid samples: {path}')
    out = {k: np.array([float(r[k]) for r in good]) for k in (xkey, 'p_rgh', 'U:2', 'alpha.water')}
    order = np.argsort(out[xkey]); out = {k: v[order] for k, v in out.items()}
    return out[xkey], out, len(rows) - len(good)


def crossing_upstream(x: np.ndarray, u: np.ndarray, lower: float, upper: float) -> float | None:
    mask = (x >= lower) & (x <= upper)
    xx, yy = x[mask], u[mask]
    for i in range(1, len(xx)):
        if yy[i-1] < 0 <= yy[i] and yy[i] != yy[i-1]:
            return float(xx[i-1] - yy[i-1]*(xx[i] - xx[i-1])/(yy[i] - yy[i-1]))
    return None


def investigate(directory: Path, report: Path, p_ref_abs: float = 101325.0,
                z_start: float = 0.020, z_end: float = 0.030) -> dict:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    directory = Path(directory).expanduser().resolve()
    report = Path(report).expanduser().resolve()
    report.mkdir(parents=True, exist_ok=True)
    arrays = []
    flags = []
    for folder in sorted(directory.iterdir()):
        t = get_time(folder) if folder.is_dir() else None
        if t is None:
            continue
        axis_path, wall_path = folder / 'axial_r1p0mm.csv', folder / 'axial_r4p5mm.csv'
        if not axis_path.exists() or not wall_path.exists():
            flags.append(f'{folder.name}: missing axis/wall CSV')
            continue
        za, a, dropped_a = load_profile(axis_path, 'Points:2')
        zw, w, dropped_w = load_profile(wall_path, 'Points:2')
        if dropped_a + dropped_w:
            flags.append(f'{folder.name}: {dropped_a+dropped_w} rejected samples')
        if za[0] > z_start or za[-1] < z_end:
            flags.append(f'{folder.name}: pressure transition not fully covered')
            continue
        pa, uz = a['p_rgh'], a['U:2']
        p0 = float(np.interp(z_start, za, pa)); p1 = float(np.interp(z_end, za, pa))
        portion = (za >= z_start) & (za <= z_end)
        dz = np.diff(za[portion]); dp = np.diff(pa[portion]); grad = dp/dz
        zgrad = (za[portion][1:] + za[portion][:-1])/2
        maximum = float(zgrad[int(np.argmax(grad))]) if len(grad) else math.nan
        # The continuous 50% pressure-recovery location is less grid-pinned than argmax(dp/dz).
        half = 0.5*(p0+p1)
        recovered = za[portion]; pres = pa[portion]
        ids = np.where((pres[:-1]-half)*(pres[1:]-half) <= 0)[0]
        half_z = None
        if len(ids):
            i = int(ids[0]); denom = pres[i+1]-pres[i]
            if denom != 0:
                half_z = float(recovered[i]+(half-pres[i])*(recovered[i+1]-recovered[i])/denom)
        recirc = crossing_upstream(zw, w['U:2'], 0.012, 0.045)
        v0 = float(np.interp(z_start, za, uz)); v1 = float(np.interp(z_end, za, uz))
        pmin = float(pa.min())
        row = dict(time_s=t, p20_pa=p0, p30_pa=p1, delta_p_pa=p1-p0,
                   max_dp_dz_z_mm=maximum*1000, pressure_half_z_mm=half_z*1000 if half_z else None,
                   recirculation_end_z_mm=recirc*1000 if recirc else None,
                   water_velocity20_m_s=v0, water_velocity30_m_s=v1,
                   minimum_sampled_p_gauge_pa=pmin,
                   minimum_estimated_p_abs_pa=p_ref_abs+pmin,
                   minimum_p_abs_fraction=(p_ref_abs+pmin)/p_ref_abs)
        radial = folder / 'radial_z90mm.csv'
        if radial.exists():
            _, radial_data, _ = load_profile(radial, 'Points:0')
            row['outlet_section_min_alpha_water'] = float(radial_data['alpha.water'].min())
        arrays.append((row, za, pa, w))
    if not arrays:
        raise ValueError('No valid sampled temporal profiles')
    rows = [x[0] for x in arrays]
    keys = sorted({k for row in rows for k in row})
    with (report/'temporal_metrics.csv').open('w', newline='', encoding='utf-8') as f:
        writer=csv.DictWriter(f, fieldnames=keys); writer.writeheader(); writer.writerows(rows)
    times=np.array([r['time_s']*1000 for r in rows])
    zcommon=np.linspace(max(x[1][0] for x in arrays)*1000,min(x[1][-1] for x in arrays)*1000,350)
    pressure=np.array([np.interp(zcommon,x[1]*1000,x[2])/1000 for x in arrays])
    fig,ax=plt.subplots(figsize=(9,5))
    chart=ax.imshow(pressure, origin='lower', aspect='auto', interpolation='nearest',
                    extent=(zcommon[0],zcommon[-1],times[0],times[-1]),cmap='viridis')
    fig.colorbar(chart,ax=ax,label='p_rgh, kPa (gauge reference)')
    ax.plot([r['pressure_half_z_mm'] for r in rows],times,'w--',label='50% pressure recovery')
    ax.set(xlabel='Axial z, mm',ylabel='Time, ms',title='Closed: pressure evolution, r=1 mm')
    ax.legend();fig.tight_layout();fig.savefig(report/'pressure_spacetime.png',dpi=150);plt.close(fig)
    fig,ax=plt.subplots(figsize=(8,4))
    ax.plot(times,[r['pressure_half_z_mm'] for r in rows],'o-',label='50% pressure recovery')
    ax.plot(times,[r['recirculation_end_z_mm'] for r in rows],'s-',label='U_z=0 near wall')
    ax.set(xlabel='Time, ms',ylabel='Position z, mm',title='Pressure transition and recirculation')
    ax.grid(alpha=.2);ax.legend();fig.tight_layout();fig.savefig(report/'transition_recirculation.png',dpi=150);plt.close(fig)
    min_ratio=min(r['minimum_p_abs_fraction'] for r in rows)
    status='POTENTIALLY_INVALID_INCOMPRESSIBLE_GAS' if min_ratio < 0.8 else 'REFERENCE_DEPENDENT_CHECK'
    if min_ratio <= 0:
        status='NONPOSITIVE_ABSOLUTE_PRESSURE_ESTIMATE'
    if status!='REFERENCE_DEPENDENT_CHECK':
        flags.append(f'Gauge-to-absolute assumed p_ref={p_ref_abs:.0f} Pa; min p_abs/p_ref={min_ratio:.3f}. Incompressible air not defensible for quantitative pressure.')
    flags.append('Potential pressure jump is not automatically a two-phase mixing shock')
    output={'status':status,'n_times':len(rows),'p_ref_abs_pa_assumed':p_ref_abs,
            'minimum_assumed_p_abs_ratio':min_ratio,'max_pressure_half_motion_mm':
            max(r['pressure_half_z_mm'] for r in rows)-min(r['pressure_half_z_mm'] for r in rows),
            'warnings':flags, 'mixing_shock_confirmed':False}
    (report/'temporal_summary.json').write_text(json.dumps(output,indent=2,ensure_ascii=False)+'\n')
    return output


def main() -> None:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--profiles-dir',type=Path,required=True)
    ap.add_argument('--report',type=Path,required=True)
    ap.add_argument('--p-ref-abs',type=float,default=101325)
    a=ap.parse_args()
    print(json.dumps(investigate(a.profiles_dir,a.report,a.p_ref_abs),indent=2))


if __name__ == '__main__':
    main()
