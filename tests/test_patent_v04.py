"""CFD v0.4 checks are static; OpenFOAM is not installed in the CI runner."""
import json
from pathlib import Path
import pytest

from cfd.baseline_v03.generate import blockmesh_text
from cfd.patent_v04.generate import build, HERE


def config():
    return json.loads((HERE/'config_open.json').read_text())


def test_open_closed_patent_cases(tmp_path):
    reports=build(tmp_path)
    assert len(reports)==2
    for mode in ('open','closed'):
        case=tmp_path/f'diaphragm_ejector_{mode}'
        mesh=(case/'system/blockMeshDict').read_text()
        assert 'diaphragmWall' in mesh and 'feedWall' in mesh
        assert 'scale 1;' in mesh
        assert 'convertToMeters' not in mesh
        assert 'pcorrFinal' in (case/'system/fvSolution').read_text()
        assert 'ambientFlux' in (case/'system/controlDict').read_text()
        assert 'diaphragmWall' in (case/'0/U').read_text()
        meta=json.loads((case/'case_manifest.json').read_text())
        assert meta['status']=='INPUTS_GENERATED_NOT_SOLVER_VALIDATED'
        assert meta['mesh']['patch_face_counts']['waterInlet']==2
        assert meta['mesh']['patch_face_counts']['diaphragmWall']==1
        assert meta['mesh']['cells_estimate']>2500
        assert ('type wall;' if mode=='closed' else 'type patch;') in mesh.split('airInlet')[1].split('}')[0]


def test_diaphragm_bound_rejects_unphysical_thickness(tmp_path):
    c=config()
    c['diaphragm_thickness_mm']=0.21*c['nozzle_d_mm']
    p=tmp_path/'config.json';p.write_text(json.dumps(c))
    with pytest.raises(ValueError,match='Diaphragm thickness'):
        build(tmp_path/'generated',p)


def test_feed_and_diaphragm_are_independent_parameters():
    c=config(); mesh,_=blockmesh_text(c,False)
    c['feed_d_mm']=18.;b,_=blockmesh_text(c,False)
    assert mesh!=b
    c=config();c['diaphragm_thickness_mm']=0.9;d,_=blockmesh_text(c,False)
    assert mesh!=d


def test_3d_is_optional():
    from cfd.patent_v04.geometry_3d import build_3d
    with pytest.raises(ValueError):
        build_3d(HERE/'config_open.json', Path('/tmp/not_created.msh'),mesh_size_mm=0)
