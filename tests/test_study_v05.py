"""v0.5 static tests. No real solver is installed in this test environment."""
import csv
import json
from pathlib import Path

import pytest

from cfd.study_v05.generate import build, turbulence_parameters
from cfd.study_v05.analyze import parse_flux_logs, qc_profile, summarize
from cfd.study_v05.compare import compare
from cfd.study_v05.run import run_case


def test_turbulence_formula():
    c={'water_inlet_speed_m_s':2.9251875,'feed_d_mm':16.0}
    t={'turbulence':{'water_inlet_intensity':0.05,
        'water_length_scale_fraction_of_feed_d':0.07,
        'air_inlet_intensity':0.05,'air_reference_speed_m_s':1,
        'air_length_scale_m':0.003,'Cmu':0.09}}
    p=turbulence_parameters(c,t)
    assert p['water_k'] == pytest.approx(1.5*(2.9251875*0.05)**2)
    assert 0<p['air_k']<p['water_k']
    assert p['water_omega']>0 and p['air_omega']>0


def test_generator_six_cases_and_sst_settings(tmp_path):
    cases=build(tmp_path/'cases')
    assert len(cases)==6
    sizes=[x['estimated_cells'] for x in cases[::2]]
    assert sizes == sorted(sizes) and len(set(sizes))==3
    assert sizes[0]>=5000 and sizes[2]>=30000
    for c in cases:
        path=Path(c['directory'])
        bc=(path/'0/k').read_text()
        assert 'type kqRWallFunction;' in bc
        assert 'type inletOutlet;' in bc or c['case'].endswith('closed')
        assert 'type omegaWallFunction;' in (path/'0/omega').read_text()
        assert 'type nutUSpaldingWallFunction;' in (path/'0/nut').read_text()
        assert 'simulationType RAS;' in (path/'constant/turbulenceProperties').read_text()
        assert 'RASModel kOmegaSST;' in (path/'constant/turbulenceProperties').read_text()
        schemes=(path/'system/fvSchemes').read_text()
        assert 'div(phi,k)' in schemes
        assert schemes.count('wallDist') == 1
        assert 'method meshWave;' in schemes
        assert '    omega {' in (path/'system/fvSolution').read_text()
        assert 'wallYPlus' in (path/'system/controlDict').read_text()
        assert 'endTime 0.06;' in (path/'system/controlDict').read_text()
        assert 'writeInterval 0.002;' in (path/'system/controlDict').read_text()
        assert json.loads((path/'case_manifest.json').read_text())['status']=='GENERATED_UNRUN_V05'
    assert 'type wall;' in (tmp_path/'cases/ejector_coarse_closed/system/blockMeshDict').read_text()


def test_bad_turbulence_intensity_rejected():
    with pytest.raises(ValueError,match='intensit'):
        turbulence_parameters({'feed_d_mm':16,'water_inlet_speed_m_s':3},
          {'turbulence':{'water_inlet_intensity':0,'air_inlet_intensity':0.05}})


def test_flux_restart_and_volumetric_balance(tmp_path):
    a=tmp_path/'log.interFoam';b=tmp_path/'log.interFoam_60ms'
    a.write_text('Time = 0.03\nsum(airInlet) of phi = -2.5e-6\n'
      'sum(waterInlet) of phi = -8e-6\nsum(ambientOpen) of phi = 0\n'
      'sum(outlet) of phi = 10.5e-6\n')
    b.write_text('Time = 0.06\nsum(airInlet) of phi = -2e-6\n'
      'sum(waterInlet) of phi = -8e-6\nsum(ambientOpen) of phi = 0\n'
      'sum(outlet) of phi = 10e-6\nEnd\n')
    rows=parse_flux_logs([a,b])
    assert [x['time_s'] for x in rows]==[0.03,0.06]
    assert rows[-1]['k_phi']==pytest.approx(0.25)
    assert rows[-1]['balance_m3_s']==pytest.approx(0,abs=1e-19)
    r=summarize(tmp_path,tmp_path/'report')
    assert r['k_phi_final']==pytest.approx(0.25)
    assert r['kQ_phase_resolved'] is None
    assert r['mixing_shock_confirmed'] is False
    assert (tmp_path/'report/k_phi_history.png').exists()


def test_paraview_profile_checks_masks(tmp_path):
    f=tmp_path/'p.csv'
    with f.open('w',newline='') as t:
        w=csv.DictWriter(t,fieldnames=['Points:2','Points:0','Points:1','vtkValidPointMask',
                                      'p_rgh','alpha.water','U:2'])
        w.writeheader()
        w.writerows([
          {'Points:2':.010,'Points:0':.001,'Points:1':0,'vtkValidPointMask':1,
            'p_rgh':15,'alpha.water':1,'U:2':19},
          {'Points:2':.020,'Points:0':.001,'Points:1':0,'vtkValidPointMask':0,
            'p_rgh':100,'alpha.water':0,'U:2':0},
          {'Points:2':.045,'Points:0':.001,'Points:1':0,'vtkValidPointMask':1,
            'p_rgh':16,'alpha.water':1,'U:2':19},
        ])
    q=qc_profile(f)
    assert q['n_valid']==2 and q['z_max_mm']==pytest.approx(45)
    p=tmp_path/'case';p.mkdir()
    s=summarize(p,tmp_path/'report',{'axis':f})
    assert any('before 90 mm' in x for x in s['flags'])


def test_comparison_does_not_invent_data(tmp_path):
    r=compare(tmp_path/'study',tmp_path/'table')
    assert r['reports']==0
    assert (tmp_path/'table/comparison.csv').exists()
    assert 'NOT MEASURED' in (tmp_path/'table/comparison.md').read_text()


def test_runner_rejects_unbuilt_case(tmp_path):
    with pytest.raises(ValueError,match='Unknown case'):
        run_case(tmp_path,'ejector_fake_open',['mesh'])


def test_parameter_sweep_generated_safely(tmp_path):
    from cfd.study_v05.sweep import build_sweep
    rows=build_sweep(tmp_path/'sweep')
    assert 8 <= len(rows) <= 25
    assert len({x['case'] for x in rows})==len(rows)
    for row in rows:
        manifest=json.loads((tmp_path/'sweep'/row['case']/'case_manifest.json').read_text())
        assert manifest['status']=='GENERATED_UNRUN_V05'
        assert manifest['parameter_varied']==row['parameter']


def test_closed_case_quasi_steady_by_outlet_not_kphi(tmp_path):
    case=tmp_path/'closed'
    case.mkdir()
    (case/'case_manifest.json').write_text('{"turbulence_model":"kOmegaSST"}')
    logs=case/'log.interFoam'
    contents=[]
    for t, out in [(0.050, 8.270e-6), (0.052,8.275e-6), (0.054,8.271e-6),
                   (0.056,8.272e-6), (0.058,8.269e-6), (0.060,8.272e-6)]:
        contents += [f'Time = {t}', 'sum(airInlet) of phi = 0',
                     'sum(waterInlet) of phi = -8.1583e-6',
                     f'sum(ambientOpen) of phi = {8.1583e-6-out}',
                     f'sum(outlet) of phi = {out}']
    logs.write_text('\n'.join(contents)+'\n')
    r=summarize(case,tmp_path/'report')
    assert r['flux_quasi_steady'] is True
    assert r['flux_quasi_steady_observable']=='outlet'
    assert r['kQ_phase_resolved'] is None


def test_phase_flux_parser_and_fail_closed(tmp_path):
    from cfd.study_v05.phase_flux import patch_flux, calculate
    txt='''FoamFile { class surfaceScalarField; format ascii; }
    boundaryField
    {
        waterInlet { type calculated; value nonuniform List<scalar> 2 (-1 -2); }
        airInlet { type calculated; value uniform 0; }
        ambientOpen { type calculated; value nonuniform List<scalar> 1 (0.2); }
        outlet { type calculated; value nonuniform List<scalar> 1 (2.8); }
    }'''
    assert patch_flux(txt,'waterInlet',2)==-3
    assert patch_flux(txt,'airInlet',1)==0
    with pytest.raises(ValueError,match='count mismatch'):
        patch_flux(txt,'waterInlet',3)
    case=tmp_path/'case';(case/'constant/polyMesh').mkdir(parents=True)
    boundary='''4\n(\n'''
    for name,n in [('waterInlet',2),('airInlet',1),('ambientOpen',1),('outlet',1)]:
        boundary+=f'{name}\n{{\n type patch;\n nFaces {n};\n startFace 0;\n}}\n'
    (case/'constant/polyMesh/boundary').write_text(boundary+')')
    d=case/'0.06';d.mkdir()
    (d/'phi').write_text(txt)
    r=calculate(case,tmp_path/'rep')
    assert r['rows']==0
    assert r['kQ_phase_resolved'] is None
    assert any('alphaPhi0.water' in s for s in r['flags'])
    (d/'alphaPhi0.water').write_text(txt)
    r=calculate(case,tmp_path/'rep2')
    assert r['rows']==1
    assert r['status'].startswith('PHASE_FACE_FLUX_')
    assert r['kQ_phase_boundary_candidate']==pytest.approx(0)


def test_temporal_pressure_diagnostics_from_synthetic_csv(tmp_path):
    from cfd.study_v05.temporal import investigate
    base=tmp_path/'profiles'
    for ms in (40,50,60):
        p=base/f'profiles_t{ms}ms';p.mkdir(parents=True)
        for name,rad in [('axial_r1p0mm.csv',.001),('axial_r4p5mm.csv',.0045)]:
            with (p/name).open('w',newline='') as f:
                wr=csv.DictWriter(f,fieldnames=['Points:2','Points:0','vtkValidPointMask',
                    'alpha.water','U:2','p_rgh'])
                wr.writeheader()
                for z in [x/1000 for x in range(10,91)]:
                    pr=-80000+min(max((z-.020)/.010,0),1)*70000
                    wr.writerow({'Points:2':z,'Points:0':rad,'vtkValidPointMask':1,
                        'alpha.water':1,'U:2':(-2 if rad>.004 and z<.025 else 15),
                        'p_rgh':pr})
    out=investigate(base,tmp_path/'report')
    assert out['n_times']==3
    assert out['status']=='POTENTIALLY_INVALID_INCOMPRESSIBLE_GAS'
    assert out['mixing_shock_confirmed'] is False
    assert (tmp_path/'report/pressure_spacetime.png').exists()


def test_medium_fine_mesh_use_wall_grading(tmp_path):
    from cfd.study_v05.generate import build
    build(tmp_path/'generated')
    coarse=(tmp_path/'generated/ejector_coarse_open/system/blockMeshDict').read_text()
    medium=(tmp_path/'generated/ejector_medium_open/system/blockMeshDict').read_text()
    fine=(tmp_path/'generated/ejector_fine_open/system/blockMeshDict').read_text()
    assert 'simpleGrading (1 1 1)' in coarse
    assert 'simpleGrading (0.45' in medium
    assert 'simpleGrading (0.25' in fine
