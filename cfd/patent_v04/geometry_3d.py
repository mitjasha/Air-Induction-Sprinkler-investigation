# ruff: noqa: E701, E702, E703
"""Parametric 3D *geometry/mesh prototype* with discrete lateral air duct.

Requires gmsh Python bindings (and working OpenCASCADE). No flow BCs are
created here. A generated .msh is NOT an OpenFOAM-validated case.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def build_3d(config:Path, out:Path, *, mesh_size_mm:float=1.0):
    if mesh_size_mm <= 0: raise ValueError('mesh_size_mm must be positive')
    cfg=json.loads(Path(config).read_text())
    dn=cfg['nozzle_d_mm']*0.001;dt=cfg['throat_d_mm']*0.001
    delta=cfg['diaphragm_thickness_mm']*0.001
    rf=cfg['feed_d_mm']*0.0005
    rs=cfg['suction_chamber_d_mm']*0.0005
    gap=cfg['nozzle_to_throat_gap_mm']*0.001
    length=cfg['throat_length_mm']*0.001
    inlet=-delta-cfg['feed_length_mm']*0.001
    port_r=cfg['air_port_d_mm']*0.0005
    port_length=cfg['air_port_length_mm']*0.001
    if not (0<delta<=.2*dn and 0<dn<dt<2*rs and rf>dn/2):
        raise ValueError('Invalid nozzle / diaphragm / chamber geometry')
    if not (0<port_r<.5*rs and gap>2*port_r and port_length>port_r):
        raise ValueError('Air port too large for suction chamber / gap')
    try: import gmsh
    except ImportError as e: raise RuntimeError('gmsh module unavailable: pip install gmsh') from e
    gmsh.initialize()
    try:
        gmsh.model.add('patent_informed_ejector_v04')
        oc=gmsh.model.occ
        feed=oc.addCylinder(0,0,inlet,0,0,-delta-inlet,rf)
        nozzle=oc.addCylinder(0,0,-delta,0,0,delta,dn/2)
        chamber=oc.addCone(0,0,0,0,0,gap,rs,dt/2)
        throat=oc.addCylinder(0,0,gap,0,0,length,dt/2)
        # One physically explicit lateral port, not the axisymmetric annulus.
        port_start=rs*.55
        port_end=rs+port_length
        port=oc.addCylinder(port_start,0,gap/2,port_end-port_start,0,0,port_r)
        volumes,_=oc.fuse([(3,feed)],[(3,nozzle),(3,chamber),(3,throat),(3,port)],removeObject=True,removeTool=True)
        oc.synchronize()
        fluid=[tag for dim,tag in volumes if dim==3]
        if not fluid: raise RuntimeError('OCC fuse did not produce a fluid volume')
        gmsh.model.addPhysicalGroup(3,fluid,1)
        gmsh.model.setPhysicalName(3,1,'fluid')
        faces=gmsh.model.getBoundary([(3,i) for i in fluid],oriented=False,recursive=False)
        eps=1e-7
        groups={'waterInlet':[], 'airInlet':[], 'outlet':[], 'walls':[]}
        for dim,sid in faces:
            if dim!=2: continue
            x0,y0,z0,x1,y1,z1=gmsh.model.getBoundingBox(2,sid)
            if abs(z0-inlet)<eps and abs(z1-inlet)<eps:
                group='waterInlet'
            elif abs(z0-(gap+length))<eps and abs(z1-(gap+length))<eps:
                group='outlet'
            elif abs(x0-port_end)<eps and abs(x1-port_end)<eps:
                group='airInlet'
            else: group='walls'
            groups[group].append(sid)
        for index,(name,ids) in enumerate(groups.items(),11):
            if not ids:raise RuntimeError(f'No {name} surface identified; inspect OCC topology')
            gmsh.model.addPhysicalGroup(2,ids,index)
            gmsh.model.setPhysicalName(2,index,name)
        gmsh.option.setNumber('Mesh.CharacteristicLengthMin',mesh_size_mm*.001*.4)
        gmsh.option.setNumber('Mesh.CharacteristicLengthMax',mesh_size_mm*.001)
        gmsh.option.setNumber('Mesh.MshFileVersion',2.2)
        gmsh.model.mesh.generate(3)
        Path(out).parent.mkdir(parents=True,exist_ok=True)
        gmsh.write(str(out))
        return {'status':'MESH_GENERATED_NOT_CFD_VALIDATED','file':str(out),'fluid_volumes':len(fluid),'surface_groups':{k:len(v) for k,v in groups.items()}}
    finally:
        gmsh.finalize()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=HERE/'config_open.json')
    parser.add_argument('--out',type=Path,default=HERE/'generated/patent_ejector_3d.msh')
    parser.add_argument('--mesh-size-mm',type=float,default=1.0)
    args=parser.parse_args()
    print(json.dumps(build_3d(args.config,args.out,mesh_size_mm=args.mesh_size_mm),indent=2))
