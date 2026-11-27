"""Exact coordinate-compressed orthogonal gap measurements (cm, cm3).

Internal means an empty cell bounded by cargo on both sides of at least
one horizontal axis, or below cargo. Outer spare capacity is excluded.
This does not certify load restraint or global packing optimality.
"""
import numpy as np


def internal_gaps(placements, include_regions=False):
    if not placements:
        return {"internal_gap_volume_cm3": 0.0, "gap_regions": []}
    axes = (("x", "placed_length"), ("y", "placed_width"), ("z", "placed_height"))
    edges = [np.unique([v for p in placements for v in (float(p[a]), float(p[a])+float(p[d]))]) for a,d in axes]
    # Sweep vertical slabs rather than allocate a potentially huge 3D grid.
    xs, ys, zs = edges
    zs = np.unique(np.r_[0.0, zs])
    area = np.diff(xs)[:,None] * np.diff(ys)[None,:]
    total, regions = 0.0, []
    for z0,z1 in zip(zs,zs[1:]):
        occupied = np.zeros(area.shape, dtype=bool)
        overhead = np.zeros(area.shape, dtype=bool)
        for p in placements:
            ix = slice(np.searchsorted(xs,p['x']),np.searchsorted(xs,p['x']+p['placed_length']))
            iy = slice(np.searchsorted(ys,p['y']),np.searchsorted(ys,p['y']+p['placed_width']))
            if p['z'] <= z0+1e-7 and p['z']+p['placed_height'] >= z1-1e-7:
                occupied[ix,iy] = True
            if p['z'] >= z1-1e-7:
                overhead[ix,iy] = True
        gaps = overhead & ~occupied
        for axis in (0,1):
            before = np.maximum.accumulate(occupied,axis=axis)
            after = np.flip(np.maximum.accumulate(np.flip(occupied,axis=axis),axis=axis),axis=axis)
            gaps |= before & after & ~occupied
        total += float(area[gaps].sum())*(z1-z0)
        if include_regions:
            for i,j in np.argwhere(gaps):
                regions.append(dict(x=float(xs[i]),y=float(ys[j]),z=float(z0),
                                    length=float(xs[i+1]-xs[i]),width=float(ys[j+1]-ys[j]),height=float(z1-z0)))
    return {"internal_gap_volume_cm3": round(float(total),6), "gap_regions": regions}


def lateral_contact(placements):
    """Box-to-box side-face area; exclude floor/ceiling to avoid rewarding stacks."""
    contact = 0.0
    for i,a in enumerate(placements):
        for b in placements[i+1:]:
            ox=max(0,min(a['x']+a['placed_length'],b['x']+b['placed_length'])-max(a['x'],b['x']))
            oy=max(0,min(a['y']+a['placed_width'],b['y']+b['placed_width'])-max(a['y'],b['y']))
            oz=max(0,min(a['z']+a['placed_height'],b['z']+b['placed_height'])-max(a['z'],b['z']))
            if abs(a['x']+a['placed_length']-b['x'])<1e-7 or abs(b['x']+b['placed_length']-a['x'])<1e-7:
                contact += oy*oz
            if abs(a['y']+a['placed_width']-b['y'])<1e-7 or abs(b['y']+b['placed_width']-a['y'])<1e-7:
                contact += ox*oz
    return round(contact,6)
