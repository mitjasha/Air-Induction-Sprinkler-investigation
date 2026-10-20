"""Phase-resolved *face-flux* audit for OpenFOAM.com interFoam.

Read the MULES water flux alphaPhi0.water if it was actually AUTO_WRITE-saved,
not alpha-interpolated velocity from ParaView. Complementary air volume flux is
phi - alphaPhi0.water, per oriented face. These are incompressible phase volume
fluxes in m^3/s; use face data from identical saved times only.

Without a recorded water-phase inventory history, instantaneous net water flux
is NOT a phase-conservation validation for an unsteady calculation.
No result is produced for missing/non-ASCII/unverified fields.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import json
import math
import re
from pathlib import Path

PATCHES = ('waterInlet', 'airInlet', 'ambientOpen', 'outlet')


def _read(path: Path) -> str:
    gz = Path(str(path) + '.gz')
    if path.is_file():
        raw = path.read_bytes()
    elif gz.is_file():
        raw = gzip.decompress(gz.read_bytes())
    else:
        raise FileNotFoundError(path)
    if b'format      binary' in raw or re.search(rb'format\s+binary\s*;', raw):
        raise ValueError(f'Binary OpenFOAM field unsupported by ASCII audit: {path}')
    return raw.decode('utf-8')


def _balanced(text: str, idx: int) -> str:
    start = text.find('{', idx)
    if start < 0:
        raise ValueError('Missing OpenFOAM dictionary opening brace')
    depth = 0
    for i in range(start, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i]
    raise ValueError('Unclosed OpenFOAM dictionary')


def _patch_dict(text: str, patch: str) -> str:
    head = re.search(r'\bboundaryField\b\s*\{', text)
    if not head:
        raise ValueError('No boundaryField in saved surfaceScalarField')
    body = _balanced(text, head.start())
    entry = re.search(r'(?m)^\s*' + re.escape(patch) + r'\s*\{', body)
    if not entry:
        raise ValueError(f'Missing {patch} patch in saved surfaceScalarField')
    return _balanced(body, entry.start())


def patch_flux(text: str, patch: str, n_faces: int | None = None) -> float:
    body = _patch_dict(text, patch)
    m = re.search(r'\bvalue\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)\s*;', body, re.S)
    if m:
        n = int(m.group(1))
        values = [float(x) for x in m.group(2).split()]
        if n != len(values) or (n_faces is not None and n != n_faces):
            raise ValueError(f'{patch}: face count mismatch ({n} declared, {len(values)} values, {n_faces} mesh)')
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Nonfinite saved phase flux')
        return math.fsum(values)
    m = re.search(r'\bvalue\s+uniform\s+([-+\d.eE]+)\s*;', body)
    if m:
        if n_faces is None:
            raise ValueError('uniform flux needs a trustworthy mesh patch-face count')
        return float(m.group(1)) * n_faces
    raise ValueError(f'{patch}: no saved scalar face values (not a conservative flux)')


def face_counts(case: Path) -> dict[str, int]:
    text = _read(case / 'constant/polyMesh/boundary')
    counts = {}
    for patch in PATCHES:
        m = re.search(r'(?m)^\s*' + re.escape(patch) + r'\s*\{', text)
        if not m:
            raise ValueError(f'Mesh missing patch {patch}')
        body = _balanced(text, m.start())
        n = re.search(r'\bnFaces\s+(\d+)\s*;', body)
        if not n:
            raise ValueError('nFaces missing')
        counts[patch] = int(n.group(1))
    return counts


def _num_times(case: Path) -> list[tuple[float, Path]]:
    out = []
    for folder in case.iterdir():
        if not folder.is_dir():
            continue
        try:
            t = float(folder.name)
        except ValueError:
            continue
        if t > 0:
            out.append((t, folder))
    return sorted(out)


def water_inventory(case: Path) -> dict[float, float]:
    """Read solver volIntegrate(alpha.water) written at the time of the CFD solve."""
    values = {}
    for f in (case/'postProcessing/waterInventory').glob('*/volFieldValue.dat'):
        for line in f.read_text(encoding='utf-8', errors='replace').splitlines():
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            cols = line.split()
            if len(cols) >= 2:
                try:
                    t, v = float(cols[0]), float(cols[1])
                except ValueError:
                    continue
                if t >= 0 and math.isfinite(v):
                    values[t] = v
    return values


def calculate(case: Path, report: Path) -> dict:
    case = Path(case).expanduser().resolve()
    report = Path(report).expanduser().resolve()
    report.mkdir(parents=True, exist_ok=True)
    result = {'case': str(case), 'source': 'saved solver surfaceScalarField alphaPhi0.water',
              'status': 'UNVERIFIED', 'kQ_phase_resolved': None, 'rows': 0, 'flags': []}
    if not (case / 'constant/polyMesh/boundary').exists():
        result['flags'].append('Missing polyMesh: must run blockMesh first')
    else:
        counts = face_counts(case)
        history = []
        for t, folder in _num_times(case):
            try:
                water = _read(folder / 'alphaPhi0.water')
                mixture = _read(folder / 'phi')
                row = {'time_s': t}
                for p in PATCHES:
                    qw = patch_flux(water, p, counts[p])
                    qp = patch_flux(mixture, p, counts[p])
                    row[f'{p}_water'] = qw
                    row[f'{p}_air'] = qp - qw
                    row[f'{p}_mixture'] = qp
                w = -row['waterInlet_water']
                a = -row['airInlet_air']
                row['kQ_phase_boundary'] = a / w if w > 0 else math.nan
                row['net_water_face_flux'] = sum(row[f'{p}_water'] for p in PATCHES)
                row['net_air_face_flux'] = sum(row[f'{p}_air'] for p in PATCHES)
                history.append(row)
            except (FileNotFoundError, ValueError) as exc:
                result['flags'].append(f'{folder.name}: {exc}')
        if history:
            columns = list(history[0])
            with (report / 'phase_flux_history.csv').open('w', newline='', encoding='utf-8') as dest:
                writer = csv.DictWriter(dest, fieldnames=columns)
                writer.writeheader()
                writer.writerows(history)
            result['rows'] = len(history)
            result['latest_time_s'] = history[-1]['time_s']
            result['kQ_phase_boundary_candidate'] = history[-1]['kQ_phase_boundary']
            result['status'] = 'PHASE_FACE_FLUX_SAMPLED_NOT_CONSERVATION_VERIFIED'
            inventory = water_inventory(case)
            available = [r for r in history if any(abs(t-r['time_s']) < 1e-8 for t in inventory)]
            if len(available) >= 3:
                cons = []
                for row0, row1 in zip(available[:-1], available[1:]):
                    t0, t1 = row0['time_s'], row1['time_s']
                    vol0 = inventory[min(inventory, key=lambda x:abs(x-t0))]
                    vol1 = inventory[min(inventory, key=lambda x:abs(x-t1))]
                    if t1 <= t0:
                        continue
                    # A trapezoidal face-flux approximation between saved field times.
                    net = 0.5*(row0['net_water_face_flux']+row1['net_water_face_flux'])
                    residual = (vol1-vol0)/(t1-t0) + net
                    scale = max(abs(row1['waterInlet_water']), 1e-16)
                    cons.append(abs(residual)/scale)
                if cons:
                    result['water_phase_conservation_rel_max'] = max(cons)
                    result['water_phase_conservation_rel_last'] = cons[-1]
                    if max(cons) < 0.05 and cons[-1] < 0.02:
                        result['status'] = 'WATER_PHASE_BUDGET_NUMERICALLY_CONSISTENT'
                    else:
                        result['flags'].append('Phase water inventory/face-flux residual exceeds 5% over saved snapshots')
            else:
                result['flags'].append('No paired waterInventory volIntegrate(alpha.water) history; phase conservation unverified')
            # A phase flux through the air port is only entrained air if backflow water is negligible.
            last = history[-1]
            if abs(last['airInlet_water']) > max(1e-10, .01*abs(last['airInlet_mixture'])):
                result['flags'].append('Water present at airInlet: phase entrainment cannot use net port flux as pure air')
            result['flags'].append('MULES flux alphaPhi0.water and phi must represent compatible solver time levels; verify v2606')
        else:
            result['flags'].append('No verified saved water and mixture phase surface fluxes; kQ unavailable')
    (report / 'phase_summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    print(json.dumps(calculate(args.case, args.report), indent=2))


if __name__ == '__main__':
    main()
