"""Optional automated profile extraction via ParaView's pvpython (not standard Python).

pvpython cfd/study_v05/sample_pvpython.py --case /path/ejector_coarse_open

ParaView API varies by release: verify exported coordinates and vtkValidPointMask.
DOES NOT compute conservative phase fluxes. For v0.5 2D wedge only.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case',type=Path,required=True)
    ap.add_argument('--output',type=Path)
    ap.add_argument('--time',type=float,help='Select saved physical time (default: last)')
    a=ap.parse_args()
    try:
        from paraview.simple import OpenFOAMReader, PlotOverLine, SaveData
    except ImportError as exc:
        raise SystemExit('Use ParaView pvpython, not the project Python interpreter') from exc
    case=a.case.expanduser().resolve()
    out=a.output or case/'sampled_profiles'
    out.mkdir(parents=True,exist_ok=True)
    foam=case/'case.foam'
    foam.touch(exist_ok=True)
    reader=OpenFOAMReader(FileName=str(foam))
    reader.UpdatePipelineInformation()
    reader.MeshRegions=['internalMesh']
    names=set(reader.CellArrays.Available)
    reader.CellArrays=[x for x in ['U','alpha.water','p_rgh','p','k','omega','nut'] if x in names]
    ts=[float(t) for t in reader.TimestepValues]
    if not ts:raise SystemExit('No OpenFOAM time steps present')
    t=float(a.time) if a.time is not None else ts[-1]
    if min(abs(t-x) for x in ts)>1e-8:
        raise SystemExit(f'Time {t} not present in OpenFOAM saved times: {ts}')
    reader.UpdatePipeline(t)
    def export(label, p1, p2, resolution):
        profile=PlotOverLine(Input=reader)
        profile.Point1=p1
        profile.Point2=p2
        profile.Resolution=resolution
        profile.UpdatePipeline(t)
        path=out/(label+'.csv')
        SaveData(str(path),proxy=profile)
        print('EXPORTED',path,'at t=',t,flush=True)
    for r in (1.0,3.0,4.5):
        export(f'axial_r{str(r).replace(".","p")}mm',
               [r*0.001,0,0.010],[r*0.001,0,0.090],200)
    for z in (10,30,50,70,90):
        export(f'radial_z{z}mm',[0.0001,0,z*0.001],[0.00465,0,z*0.001],100)

if __name__=='__main__':main()
