"""Generate k-omega SST OpenFOAM.com interFoam cases at multiple grid levels.

No solver availability/compatibility is claimed until WSL executes verify.py.
Usage: python -m cfd.study_v05.generate --out-dir ~/CAE/CFD-runs/patent_v05
"""
from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path

from cfd.baseline_v03.generate import field, hdr, write_case

HERE = Path(__file__).resolve().parent
WALLS = ('feedWall', 'diaphragmWall', 'nozzleWall', 'suctionWall', 'throatWall', 'deflectorWall')


def turbulence_parameters(geometry: dict, study: dict) -> dict:
    t = study['turbulence']
    water_u = geometry['water_inlet_speed_m_s']
    feed_d = geometry['feed_d_mm'] * 0.001
    iw, ia = t['water_inlet_intensity'], t['air_inlet_intensity']
    if not (0 < iw <= 0.3 and 0 < ia <= 0.3):
        raise ValueError('Turbulence intensities must be 0 < I <= 0.3')
    cmu = t.get('Cmu', 0.09)
    lw = t['water_length_scale_fraction_of_feed_d'] * feed_d
    la = t['air_length_scale_m']
    if lw <= 0 or la <= 0 or cmu <= 0:
        raise ValueError('Turbulence scales and Cmu must be positive')
    kw = 1.5 * (water_u * iw) ** 2
    ka = 1.5 * (t['air_reference_speed_m_s'] * ia) ** 2
    ow = math.sqrt(kw) / (cmu ** 0.25 * lw)
    oa = math.sqrt(ka) / (cmu ** 0.25 * la)
    return {'water_k': kw, 'air_k': ka, 'water_omega': ow, 'air_omega': oa,
            'length_water_m': lw, 'length_air_m': la, 'intensity_water': iw,
            'intensity_air': ia, 'formula': 'k=1.5*(U*I)^2; omega=sqrt(k)/(Cmu^0.25*L)'}


def modify_case(case: Path, geometry: dict, study: dict, meta: dict) -> dict:
    model = study['model']
    if model not in ('kOmegaSST', 'laminar'):
        raise ValueError(f'Unsupported turbulence model: {model}')
    conditions = turbulence_parameters(geometry, study)
    patches = ['waterInlet', 'airInlet', 'outlet', 'ambientOpen', 'axis', 'wedgePlus', 'wedgeMinus', *WALLS]
    closed = geometry['air_mode'] == 'closed'
    if model == 'kOmegaSST':
        (case/'constant/turbulenceProperties').write_text(
            hdr('turbulenceProperties', 'constant') +
            'simulationType RAS;\nRAS\n{\n    RASModel kOmegaSST;\n'
            '    turbulence on;\n    printCoeffs on;\n}\n', encoding='utf-8')
        for name, dim, iv, ambient in (
            ('k', '[0 2 -2 0 0 0 0]', conditions['water_k'], conditions['air_k']),
            ('omega', '[0 0 -1 0 0 0 0]', conditions['water_omega'], conditions['air_omega']),
            ('nut', '[0 2 -1 0 0 0 0]', 0.0, 0.0),
        ):
            bc = {}
            for p in patches:
                if p.startswith('wedge'):
                    bc[p] = 'type wedge;'
                elif p == 'axis':
                    bc[p] = 'type empty;'
                elif p in WALLS or (p == 'airInlet' and closed):
                    if name == 'k':
                        bc[p] = 'type kqRWallFunction; value uniform 0;'
                    elif name == 'omega':
                        bc[p] = 'type omegaWallFunction; value uniform 1;'
                    else:
                        bc[p] = 'type nutUSpaldingWallFunction; value uniform 0;'
                elif name == 'nut':
                    bc[p] = 'type calculated; value uniform 0;'
                elif p == 'waterInlet':
                    bc[p] = f'type fixedValue; value uniform {iv:.9g};'
                else:
                    bc[p] = (f'type inletOutlet; inletValue uniform {ambient:.9g}; '
                             f'value uniform {ambient:.9g};')
            (case/'0'/name).write_text(field(name, 'volScalarField', dim, f'{iv:.9g}', bc),
                                        encoding='utf-8')
        # turbulence transport equations: bounded first-order schemes for robustness
        sf = case/'system/fvSchemes'
        schemes = sf.read_text(encoding='utf-8')
        schemes = schemes.replace('    div(rhoPhi,U) Gauss linearUpwind grad(U);',
            '    div(rhoPhi,U) Gauss linearUpwind grad(U);\n'
            '    div(phi,k) Gauss upwind;\n'
            '    div(phi,omega) Gauss upwind;')
        sf.write_text(schemes, encoding='utf-8')
        fs = case/'system/fvSolution'
        solution = fs.read_text(encoding='utf-8')
        solution = solution.replace('    U { solver smoothSolver;',
            '    k { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.05; }\n'
            '    kFinal { $k; relTol 0; }\n'
            '    omega { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.05; }\n'
            '    omegaFinal { $omega; relTol 0; }\n'
            '    U { solver smoothSolver;')
        fs.write_text(solution, encoding='utf-8')
        cpath = case/'system/controlDict'
        ctrl = cpath.read_text(encoding='utf-8')
        # Function objects requiring SST only; fail early in solver dry-run if unavailable.
        diagnostic = '''
    wallYPlus
    {
        type yPlus;
        libs ("libfieldFunctionObjects.so");
        enabled true;
        executeControl writeTime;
        writeControl writeTime;
    }
'''
        ctrl = ctrl.replace('functions\n{', 'functions\n{'+diagnostic)
        cpath.write_text(ctrl, encoding='utf-8')
    cd = case/'system/controlDict'
    ctrl = cd.read_text(encoding='utf-8')
    ctrl = ctrl.replace('endTime 0.03;', f'endTime {study["end_time_s"]:.8g};')
    # Also handle the original v0.4 config's arbitrary endTime through explicit token.
    import re
    ctrl = re.sub(r'(?m)^endTime\s+[^;]+;', f'endTime {study["end_time_s"]:.8g};', ctrl)
    ctrl = re.sub(r'(?m)^writeInterval\s+[^;]+;',
                  f'writeInterval {study["write_interval_s"]:.8g};', ctrl)
    ctrl = re.sub(r'(?m)^maxCo\s+[^;]+;', f'maxCo {study["max_co"]:.8g};', ctrl)
    ctrl = re.sub(r'(?m)^maxAlphaCo\s+[^;]+;',
                  f'maxAlphaCo {study["max_alpha_co"]:.8g};', ctrl)
    ctrl = re.sub(r'(?m)^purgeWrite\s+[^;]+;', 'purgeWrite 0;', ctrl)
    cd.write_text(ctrl, encoding='utf-8')
    meta['study_version'] = 'v0.5'
    meta['turbulence_model'] = model
    meta['turbulence_initial_conditions'] = conditions if model == 'kOmegaSST' else None
    meta['mesh_convergence_warning'] = ('Mesh resolution is not synonymous with low yPlus. '
        'Check wallYPlus on every wall; mesh is uniform radial and has no targeted boundary-layer inflation.')
    meta['phase_flux_note'] = ('sum(phi) is mixture volumetric flux. No solver-conservative '
        'air-only flux has been measured; kQ is not available until measured separately.')
    meta['mixing_shock_warning'] = ('A pressure recovery or sharp jump of sampled cell values '
        'does not alone identify a two-phase mixing shock; verify phase topology and mesh sensitivity.')
    meta['status'] = 'GENERATED_UNRUN_V05'
    # Case-local documentation must describe the actual v0.5 setup, not the
    # unmodified legacy template's v0.3 explanatory text.
    (case/'README.md').write_text(
        f'# CFD v0.5 {meta.get("grid_level", "custom")} / {geometry["air_mode"]}\n\n'
        f'- turbulence: {model}; not yet OpenFOAM-verified\n'
        '- geometry: assumed 2D annular intake, not actual lateral side port\n'
        '- water feed: fixed volumetric-flow proxy, not matched pump pressure\n'
        '- true phase kQ, yPlus and mixing-shock evidence: not validated\n'
        '- all run evidence in log.v05.*, run_audit.json and postProcessing\n'
        'See cfd/study_v05/README.md for research procedures.\n', encoding='utf-8')
    for folder in ('0','constant','system'):
        for path in (case/folder).iterdir():
            if path.is_file() and not path.name.startswith('.'):
                text = path.read_text(encoding='utf-8')
                if 'CFD v0.4 INPUT' in text:
                    path.write_text(text.replace('CFD v0.4 INPUT','CFD v0.5 INPUT'), encoding='utf-8')
    (case/'case_manifest.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False)+'\n',
                                             encoding='utf-8')
    return meta


def build(out_dir: Path, study_config: Path | None = None) -> list[dict]:
    source = (study_config or (HERE/'study_config.json')).resolve()
    study = json.loads(source.read_text(encoding='utf-8'))
    geo_path = (source.parent/study['geometry_config']).resolve()
    base = json.loads(geo_path.read_text(encoding='utf-8'))
    out_dir = Path(out_dir).expanduser().resolve()
    results = []
    for grid, settings in study['mesh_levels'].items():
        for mode in study['air_modes']:
            geometry = copy.deepcopy(base)
            geometry.update(settings)
            geometry['air_mode'] = mode
            geometry['end_time_s'] = study['end_time_s']
            name = f'ejector_{grid}_{mode}'
            case = out_dir/name
            manifest = write_case(geometry, case)
            manifest['grid_level'] = grid
            manifest['air_mode'] = mode
            manifest['study_config'] = str(source)
            manifest['geometry_config'] = str(geo_path)
            modified = modify_case(case, geometry, study, manifest)
            results.append({'case':name, 'estimated_cells':modified['mesh']['cells_estimate'],
                            'model':study['model'], 'directory':str(case)})
    (out_dir/'study_manifest.json').write_text(json.dumps({'cases':results,'settings':study},
        indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    return results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out-dir', type=Path, required=True)
    ap.add_argument('--config', type=Path)
    args = ap.parse_args()
    print(json.dumps(build(args.out_dir,args.config),indent=2,ensure_ascii=False))


if __name__ == '__main__':
    main()
