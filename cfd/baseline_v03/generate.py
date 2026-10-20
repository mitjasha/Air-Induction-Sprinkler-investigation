# ruff: noqa: E701, E702, E703
"""Axisymmetric annular-air-inlet ejector baseline, OpenFOAM.com interFoam.

This *generator* is Python-validated, not OpenFOAM-run-validated.
The 2D wedge idealises discrete air ports as a single annular intake at
water-nozzle lip.  A conical deflector (optional) is geometric hypothesis.
"""
from __future__ import annotations
import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

SUPPORTED = ('v2512', 'v2606')
HEADER = '''/*--------------------------------*- C++ -*----------------------------------*\\
| CFD v0.4 INPUT: GENERATED / CHECK WITH OPENFOAM                        |
\\*---------------------------------------------------------------------------*/
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    location "{location}";
    object {object};
}
// ************************************************************************* //
'''


def hdr(obj, location='system', cls='dictionary'):
    return HEADER.replace("{location}",location).replace("{object}",obj).replace('class dictionary;',f'class {cls};')


def ensure(cond, msg):
    if not cond: raise ValueError(msg)


def mesh_geometry(cfg, with_deflector):
    dn, dt, L = cfg['nozzle_d_mm']*1e-3, cfg['throat_d_mm']*1e-3, cfg['throat_length_mm']*1e-3
    ensure(0 < dn < dt and dn >= 0.001 and dt <= 0.030, 'Require 1 mm <= nozzle diameter < throat diameter <= 30 mm')
    ensure(0.015 <= L <= 0.25, 'Throat length must be 15–250 mm')
    rw, rt = dn/2, dt/2
    patent_mode = 'feed_d_mm' in cfg
    if patent_mode:
        fd=cfg['feed_d_mm']*1e-3
        delta=cfg['diaphragm_thickness_mm']*1e-3
        feed_length=cfg['feed_length_mm']*1e-3
        ensure(fd>dn and fd<=0.05, 'Feed diameter must exceed nozzle diameter')
        ensure(0<delta<=0.2*dn, 'Diaphragm thickness must be at most 0.2 nozzle diameter')
        ensure(0.005<=feed_length<=0.15, 'Feed length out of range')
    rs=cfg['suction_chamber_d_mm']*0.0005
    ensure(rs > rt and rs <= 0.02, 'Suction chamber must be wider than throat and <= 40mm diameter')
    gap = cfg['nozzle_to_throat_gap_mm']*1e-3
    ensure(0.002 <= gap <= 0.020, 'Gap must be 2–20 mm in this resolved geometry')
    # Air enters the annular entrance of a wider suction chamber at z=0,
    # followed by convergence over gap toward the narrower throat.
    # The throat starts at gap and is L long: its exit is gap+L.
    z_throat_exit = gap+L
    zlist = [0.0, gap, z_throat_exit] if patent_mode else [-0.012, 0.0, gap, z_throat_exit]
    if with_deflector:
        z_tip = z_throat_exit + cfg['deflector_standoff_mm']*1e-3
        ensure(z_tip > z_throat_exit + 0.003, 'Deflector standoff must exceed 3 mm')
        lend = cfg['deflector_length_mm']*1e-3
        re = cfg['deflector_radius_mm']*1e-3
        ensure(lend > 0.004 and re > 0 and re < 0.035, 'Invalid deflector')
        zlist += [z_tip, z_tip+lend]
    else:
        zlist += [z_throat_exit+0.015]
    ensure(len(set(zlist)) == len(zlist), 'Axial stations must be strictly increasing')
    # Radius tuples (inner wall, internal zoning radius, outer wall).
    radii = [(0.,rw,rs), (0.,rw,rt), (0.,rw,rt)] if patent_mode else [(0.,rw,rw), (0.,rw,rs), (0.,rw,rt), (0.,rw,rt)]
    if with_deflector:
        radii += [(0.,rw*1.5, max(rt*2.,0.016)), (re,(re+0.035)/2.,0.035)]
    else:
        radii += [(0.,rw,rt)]
    ensure(all(a<b<c for a,b,c in radii[1:]) and radii[0][0] < radii[0][1], 'Invalid radial partition')
    ncore = int(cfg['radial_cells_core']); nair = int(cfg['radial_cells_air'])
    ensure(ncore >= 3 and nair >= 2, 'Insufficient radial cells')
    angle=math.radians(float(cfg['wedge_angle_deg']))/2
    ensure(math.radians(1)<=2*angle<=math.radians(6),'Wedge angle must be 1–6°')
    xyz=[]; verts={}; cells=[]
    def vid(z,rad,side):
        if abs(rad)<1e-14: side=0
        key=(round(z,11), round(rad,11),side)
        if key not in verts:
            th=side*angle
            verts[key]=len(xyz); xyz.append((rad*math.cos(th),rad*math.sin(th),z))
        return verts[key]
    def block(z0,z1,rin0,rout0,rin1,rout1,ni,kind):
        v0=vid(z0,rin0,+1); v1=vid(z0,rout0,+1)
        v2=vid(z1,rout1,+1); v3=vid(z1,rin1,+1)
        v4=vid(z0,rin0,-1); v5=vid(z0,rout0,-1)
        v6=vid(z1,rout1,-1); v7=vid(z1,rin1,-1)
        vs=(v0,v1,v2,v3,v4,v5,v6,v7)
        ensure(len(set(vs))>=6,'Collapsed hex unexpectedly')
        # end caps, inner/outer cylindrical-conical faces, +/- wedge faces
        faces={
            'start':(v0,v1,v5,v4), 'end':(v3,v7,v6,v2),
            'inner':(v0,v4,v7,v3), 'outer':(v1,v2,v6,v5),
            'wedgePlus':(v0,v3,v2,v1), 'wedgeMinus':(v4,v5,v6,v7),
        }
        cell={'vs':vs,'faces':faces,'kind':kind,'z0':z0,'z1':z1,'inner':(rin0,rin1),'outer':(rout0,rout1),'nr':ni,'nz':max(3, round((z1-z0)/cfg['axial_cell_size_mm']*1e3))}
        cells.append(cell)
    # Patent-mode intake: upstream water feed terminates against an annular
    # diaphragm face; only the aperture continues through the thin plate.
    if patent_mode:
        z_plate=-delta
        z_feed=-delta-feed_length
        block(z_feed,z_plate,0,rw,0,rw,ncore,'feedCore')
        block(z_feed,z_plate,rw,fd/2,rw,fd/2,nair,'feedAnnulus')
        block(z_plate,0,0,rw,0,rw,ncore,'nozzle')
    else:
        block(zlist[0],zlist[1],0,rw,0,rw,ncore,'nozzle')
    for i in range(0 if patent_mode else 1,len(zlist)-1):
        a,b=zlist[i],zlist[i+1]
        r0,r1=radii[i],radii[i+1]
        block(a,b,r0[0],r0[1],r1[0],r1[1],ncore,'core')
        block(a,b,r0[1],r0[2],r1[1],r1[2],nair,'annulus')
    # Classify block faces. Identical vertex sets correspond to internal faces.
    faces=defaultdict(list)
    for c in cells:
        for key,face in c['faces'].items():
            if len(set(face))<3: continue  # zero-area axis face
            faces[tuple(sorted(face))].append((c,key,face))
    patches=defaultdict(list)
    for matches in faces.values():
        if len(matches)==2:continue
        ensure(len(matches)==1,'Nonmanifold shared face')
        c,key,face=matches[0]
        if key.startswith('wedge'): label=key
        elif key=='start':label='waterInlet' if c['kind'] in ('nozzle','feedCore','feedAnnulus') else 'airInlet'
        elif key=='end':label='diaphragmWall' if c['kind']=='feedAnnulus' else 'outlet'
        elif key=='inner':label='deflectorWall' if with_deflector and c['inner'][1]>1e-12 else 'axis'
        elif key=='outer':
            if c['kind']=='feedAnnulus':label='feedWall'
            elif c['kind']=='nozzle':label='nozzleWall'
            elif c['z1']<=gap+1e-11:label='suctionWall'
            elif c['z1']<=z_throat_exit+1e-11:label='throatWall'
            else:label='ambientOpen'
        else:raise RuntimeError(key)
        patches[label].append(face)
    # axis patch contains no faces; all axis edges collapse to vertices.
    patches.setdefault('axis', [])
    required=['waterInlet','airInlet','outlet','nozzleWall','suctionWall','throatWall','ambientOpen','deflectorWall','axis','wedgePlus','wedgeMinus']
    if patent_mode: required += ['feedWall','diaphragmWall']
    for key in required:patches.setdefault(key,[])
    ensure(len(patches['waterInlet'])==(2 if patent_mode else 1),'Unexpected water inlet face count')
    ensure(len(patches['airInlet'])==1,'One air inlet required')
    ensure(not with_deflector or len(patches['deflectorWall'])>=1,'Conical deflector wall absent')
    for key in ('nozzleWall','suctionWall','throatWall')+ (('feedWall','diaphragmWall') if patent_mode else ()):ensure(len(patches[key])>=1,f'Missing wall patch {key}')
    # Validate paired wedge boundaries and zero-area axis.
    ensure(len(patches['wedgePlus'])==len(patches['wedgeMinus']), 'Unequal wedge faces')
    return xyz,cells,patches,{'suction_chamber_radius_m':rs,'throat_start_z_m':gap,'throat_exit_z_m':z_throat_exit,'axial_stations_m':zlist,'radii_m':radii,'wedge_angle_deg':2*math.degrees(angle),'cells_estimate':sum(c['nr']*c['nz'] for c in cells),'diaphragm_thickness_m':delta if patent_mode else None,'feed_radius_m':fd/2 if patent_mode else None,'patch_face_counts':{p:len(v) for p,v in patches.items()}}


def blockmesh_text(cfg, with_deflector):
    xyz,cells,patches,meta=mesh_geometry(cfg,with_deflector)
    vertices='\n'.join('    (%.10g %.10g %.10g)'%v for v in xyz)
    def grading(cell):
        # OpenFOAM simpleGrading ratios are last/first cell sizes.
        # Radial coordinate increases toward a wall for core and annulus blocks.
        radial = float(cfg.get('radial_grading_core', 1.0) if cell['kind'] in ('core', 'nozzle', 'feedCore')
                       else cfg.get('radial_grading_annulus', 1.0))
        axial = 1.0
        if cell['kind'] in ('feedCore', 'feedAnnulus'):
            # Smaller last cell at the upstream diaphragm when ratio < 1.
            axial = float(cfg.get('axial_grading_feed', 1.0))
        elif cell['kind'] in ('core', 'annulus') and abs(cell['z0']) < 1e-12:
            # Smaller first cell at the nozzle/entrance when ratio > 1.
            axial = float(cfg.get('axial_grading_suction', 1.0))
        if not (0.05 <= radial <= 20 and 0.05 <= axial <= 20):
            raise ValueError('Mesh grading ratios must be in [0.05, 20]')
        return f'{radial:.8g} {axial:.8g} 1'
    blocks='\n'.join(f"    hex ({' '.join(map(str,c['vs']))}) ({c['nr']} {c['nz']} 1) simpleGrading ({grading(c)})" for c in cells)
    patch_text=[]
    for p,fl in patches.items():
        ptype= 'wedge' if p.startswith('wedge') else ('empty' if p=='axis' else ('wall' if p.endswith('Wall') or (p=='airInlet' and cfg['air_mode']=='closed') else 'patch'))
        f='\n'.join('            ('+' '.join(map(str,face))+')' for face in fl)
        patch_text.append(f'    {p}\n    {{\n        type {ptype};\n        faces\n        (\n{f}\n        );\n    }}')
    result=hdr('blockMeshDict')+'scale 1;\nvertices\n(\n'+vertices+'\n);\nblocks\n(\n'+blocks+'\n);\nedges ();\nboundary\n(\n'+'\n'.join(patch_text)+'\n);\nmergePatchPairs ();\n'
    return result,meta


def field(name,cl,dims,internal,bc):
    return hdr(name,'0',cl)+f'dimensions {dims};\ninternalField uniform {internal};\nboundaryField\n{{\n'+''.join(f'    {p} {{ {spec} }}\n' for p,spec in bc.items())+'}\n'


def write_case(cfg,out,with_deflector=False):
    p=Path(out)
    for folder in ('0','constant','system'): (p/folder).mkdir(parents=True,exist_ok=True)
    meshtxt,meta=blockmesh_text(cfg,with_deflector)
    (p/'system/blockMeshDict').write_text(meshtxt)
    patches=['waterInlet','airInlet','outlet','nozzleWall','suctionWall','throatWall','ambientOpen','deflectorWall','axis','wedgePlus','wedgeMinus']
    if 'feed_d_mm' in cfg: patches.extend(['feedWall','diaphragmWall'])
    waterv=float(cfg['water_inlet_speed_m_s'])
    ensure(0<waterv<40,'Water inlet speed must be (0,40) m/s')
    closed=cfg['air_mode']=='closed'
    ensure(cfg['air_mode'] in ('open','closed'),'air_mode must be open or closed')
    bc_u={k:'type noSlip;' for k in ('nozzleWall','suctionWall','throatWall','deflectorWall', 'feedWall','diaphragmWall') if k in patches}
    bc_u.update(waterInlet=f'type fixedValue; value uniform (0 0 {waterv:.8g});',airInlet='type noSlip;' if closed else 'type pressureInletOutletVelocity; value uniform (0 0 0);',outlet='type pressureInletOutletVelocity; value uniform (0 0 0);',ambientOpen='type pressureInletOutletVelocity; value uniform (0 0 0);',axis='type empty;',wedgePlus='type wedge;',wedgeMinus='type wedge;')
    bc_p={k:'type fixedFluxPressure; value uniform 0;' for k in ('waterInlet','nozzleWall','suctionWall','throatWall','deflectorWall','feedWall','diaphragmWall') if k in patches}
    bc_p.update(airInlet='type fixedFluxPressure; value uniform 0;' if closed else 'type prghTotalPressure; p0 uniform 0; value uniform 0;',outlet='type prghTotalPressure; p0 uniform 0; value uniform 0;',ambientOpen='type prghTotalPressure; p0 uniform 0; value uniform 0;',axis='type empty;',wedgePlus='type wedge;',wedgeMinus='type wedge;')
    bc_a={k:'type zeroGradient;' for k in ('nozzleWall','suctionWall','throatWall','deflectorWall', 'feedWall','diaphragmWall') if k in patches}
    bc_a.update(waterInlet='type fixedValue; value uniform 1;',airInlet='type zeroGradient;' if closed else 'type inletOutlet; inletValue uniform 0; value uniform 0;',outlet='type inletOutlet; inletValue uniform 0; value uniform 0;',ambientOpen='type inletOutlet; inletValue uniform 0; value uniform 0;',axis='type empty;',wedgePlus='type wedge;',wedgeMinus='type wedge;')
    (p/'0/U').write_text(field('U','volVectorField','[0 1 -1 0 0 0 0]','(0 0 0)',bc_u))
    (p/'0/p_rgh').write_text(field('p_rgh','volScalarField','[1 -1 -2 0 0 0 0]','0',bc_p))
    (p/'0/alpha.water').write_text(field('alpha.water','volScalarField','[0 0 0 0 0 0 0]','0',bc_a))
    (p/'constant/g').write_text(hdr('g','constant','uniformDimensionedVectorField')+'dimensions [0 1 -2 0 0 0 0];\nvalue (0 0 0);\n')
    (p/'constant/transportProperties').write_text(hdr('transportProperties','constant')+'''phases (water air);
water
{
    transportModel Newtonian;
    nu [0 2 -1 0 0 0 0] 1.003e-6;
    rho [1 -3 0 0 0 0 0] 998.2;
}
air
{
    transportModel Newtonian;
    nu [0 2 -1 0 0 0 0] 1.52e-5;
    rho [1 -3 0 0 0 0 0] 1.205;
}
sigma [1 0 -2 0 0 0 0] 0.0728;
''')
    (p/'constant/turbulenceProperties').write_text(hdr('turbulenceProperties','constant')+'simulationType laminar;\n')
    T=float(cfg['end_time_s']); ensure(0.001 <=T<= 5, 'end_time_s out of range')
    end=f'{T:g}'
    (p/'system/controlDict').write_text(hdr('controlDict')+f'''application interFoam;
startFrom startTime;
startTime 0;
stopAt endTime;
endTime {end};
deltaT 1e-8;
writeControl adjustableRunTime;
writeInterval 0.003;
purgeWrite 4;
writeFormat ascii;
writePrecision 10;
adjustTimeStep yes;
maxCo 0.2;
maxAlphaCo 0.2;
maxDeltaT 1e-5;
runTimeModifiable yes;
functions
{{
    inletOutletFlux
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        enabled true;
        writeControl writeTime;
        regionType patch;
        name airInlet;
        operation sum;
        fields (phi);
        writeFields false;
    }}
    waterInletFlux
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        enabled true;
        writeControl writeTime;
        regionType patch;
        name waterInlet;
        operation sum;
        fields (phi);
        writeFields false;
    }}
    ambientFlux
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        enabled true;
        writeControl writeTime;
        regionType patch;
        name ambientOpen;
        operation sum;
        fields (phi);
        writeFields false;
    }}
    exitFlux
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        enabled true;
        writeControl writeTime;
        regionType patch;
        name outlet;
        operation sum;
        fields (phi);
        writeFields false;
    }}
}}
''')
    (p/'system/fvSchemes').write_text(hdr('fvSchemes')+'''ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    default none;
    div(rhoPhi,U) Gauss linearUpwind grad(U);
    div(phi,alpha) Gauss vanLeer;
    div(phirb,alpha) Gauss interfaceCompression;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
''')
    (p/'system/fvSolution').write_text(hdr('fvSolution')+'''solvers
{
    "alpha.water.*"
    {
        nAlphaCorr 2;
        nAlphaSubCycles 2;
        cAlpha 1;
        MULESCorr no;
        nLimiterIter 3;
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-8;
        relTol 0;
    }
    pcorr { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0; }
    pcorrFinal { $pcorr; relTol 0; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-8; relTol 0.01; }
    p_rghFinal { $p_rgh; relTol 0; }
    U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0.05; }
    UFinal { $U; relTol 0; }
}
PIMPLE
{
    momentumPredictor no;
    nOuterCorrectors 1;
    nCorrectors 3;
    nNonOrthogonalCorrectors 0;
}
''')
    (p/'Allrun').write_text('''#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v blockMesh >/dev/null || { echo "ERROR: OpenFOAM environment not sourced" >&2; exit 127; }
command -v interFoam >/dev/null || { echo "ERROR: interFoam missing" >&2; exit 127; }
blockMesh > log.blockMesh 2>&1
checkMesh -allTopology -allGeometry > log.checkMesh 2>&1
interFoam > log.interFoam 2>&1
echo "Finished; inspect logs and residuals BEFORE interpreting any physical outputs"
''')
    (p/'Allrun').chmod(0o755)
    derived={'status':'INPUTS_GENERATED_NOT_CFD_RUN','solver':'OpenFOAM.com interFoam','solver_versions_supported_expected':SUPPORTED,'model':'2D axisymmetric wedge; incompressible VOF; entrainment at annular intake','case_type':'with_deflector' if with_deflector else 'ejector_only','geometry_source':{'nozzle_d_mm':'historical range 7.6–8.8 mm (example 7.9)','throat_d_mm':'historical approximate 9–10 mm','throat_length_mm':'historical 85 mm','other_dimensions':'exploratory assumptions, NOT historical measurement','patent_references':['BY 22927 (sprinkler nozzle)','BY 22747 (hydrojet ejector)'] if 'feed_d_mm' in cfg else []},'nominal_water_flow_m3_s':math.pi*(cfg.get('feed_d_mm',cfg['nozzle_d_mm'])*1e-3)**2/4*waterv,'mesh':meta,'parameters':cfg}
    (p/'case_manifest.json').write_text(json.dumps(derived,indent=2,ensure_ascii=False)+'\n')
    (p/'README.md').write_text('''# CFD baseline v0.3 — OpenFOAM.com `interFoam` input

**Status: generated, statically checked, NOT CFD-executed.**

Axisymmetric 3-D single-wedge representation (wedgePlus/wedgeMinus): water passes
through a finite cylindrical nozzle, exits at its lip; an annular atmospheric
intake at the same axial station approximates the aggregate 3-D discrete air
ports. A converging suction chamber occupies the nozzle-to-throat gap and
then transitions to a straight mixing throat of specified length. When enabled,
a conical **assumed** deflector is inside an expanding external domain.

This does *not* capture real discrete ports, gas compressibility, bubble-size
spectra, wall wetting laws, or sheet breakup. `air_mode=closed` changes the
annular intake to a wall; this is a controlled comparison.

`waterInlet`: prescribed pure-liquid normal velocity; `airInlet`: ambient
(gauge) total pressure with entrainment/outflow allowed; `outlet` and
`ambientOpen`: pressure openings (pure-air on backflow); walls: no slip;
wedge +/- axisymmetric, axis collapsed at r=0. Gravity intentionally 0 to
isolate the entrainment baseline (NOT a gravity-driven rainfall CFD).

After sourcing OpenFOAM.com and **verifying the version/turbulence dictionaries**:

```bash
./Allrun
```

Quality checks required before claims: checkMesh, phase bounds, flux sign,
Co/alphaCo, time residuals, water/air accumulation, grid/time convergence,
air pressure boundary sensitivity, an open-vs-closed comparison, and
independent experimental comparison. Flux function objects sum **mixture**
volumetric `phi` on specified inlet patches (not phase flux at outlet).

Absolute volumetric air suction calculated from this incompressible VOF
simulation is only a *screening* output; significant suction requires
compressible-gas or Euler–Euler validation.
''')
    return derived


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--config',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--with-deflector',action='store_true')
    args=ap.parse_args()
    cfg=json.loads(args.config.read_text())
    print(json.dumps(write_case(cfg,args.out,args.with_deflector),indent=2))


if __name__=='__main__':main()
