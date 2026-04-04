"""
Generate a single STL containing 4 hollow cylinder extensions arranged in a 2x2 grid.
Same ID/OD as the single cylinder but 4 inches (101.6mm) tall.
Grid spacing: 30mm center-to-center (19.6mm OD + 10.4mm gap)
Grid centers: (85,85), (115,85), (85,115), (115,115) — fits Ender 3 220x220 bed
"""

import numpy as np
from stl import mesh

INNER_RADIUS = 7.8      # 15.6mm ID
OUTER_RADIUS = 9.8      # 19.6mm OD
HEIGHT       = 101.6    # 4 inches in mm
SEGMENTS     = 64
SPACING      = 30.0     # center-to-center mm

# 2x2 grid offsets (centered around 100,100 on bed)
OFFSETS = [
    (85.0,  85.0),
    (115.0, 85.0),
    (85.0,  115.0),
    (115.0, 115.0),
]

def circle_pts(radius, segments, z, cx=0, cy=0):
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    x = cx + radius * np.cos(angles)
    y = cy + radius * np.sin(angles)
    return np.column_stack([x, y, np.full(segments, z)])

def build_single_cylinder(cx, cy):
    seg = SEGMENTS
    tris = []

    ib = circle_pts(INNER_RADIUS, seg, 0,      cx, cy)
    ob = circle_pts(OUTER_RADIUS, seg, 0,      cx, cy)
    it = circle_pts(INNER_RADIUS, seg, HEIGHT, cx, cy)
    ot = circle_pts(OUTER_RADIUS, seg, HEIGHT, cx, cy)

    for i in range(seg):
        n = (i + 1) % seg
        # Bottom face
        tris += [ob[i], ib[i], ob[n]]
        tris += [ib[i], ib[n], ob[n]]
        # Top face
        tris += [it[i], ot[i], ot[n]]
        tris += [it[i], ot[n], it[n]]
        # Outer wall
        tris += [ob[i], ot[i], ob[n]]
        tris += [ot[i], ot[n], ob[n]]
        # Inner wall
        tris += [ib[n], it[i], ib[i]]
        tris += [ib[n], it[n], it[i]]

    return tris

def build_all():
    all_tris = []
    for cx, cy in OFFSETS:
        all_tris.extend(build_single_cylinder(cx, cy))

    tris = np.array(all_tris).reshape(-1, 3, 3)
    m = mesh.Mesh(np.zeros(len(tris), dtype=mesh.Mesh.dtype))
    for i, t in enumerate(tris):
        m.vectors[i] = t
    return m

if __name__ == "__main__":
    m = build_all()
    out = "cylinder_extension_4x.stl"
    m.save(out)
    print(f"Saved {out}")
    print(f"  Cylinders      : 4")
    print(f"  Inner diameter : {INNER_RADIUS*2:.1f} mm")
    print(f"  Outer diameter : {OUTER_RADIUS*2:.1f} mm")
    print(f"  Height         : {HEIGHT:.1f} mm (4 inches)")
    print(f"  Grid           : 2x2, {SPACING}mm spacing")
    print(f"  Bed footprint  : ~{SPACING*2+OUTER_RADIUS*2:.0f} x {SPACING*2+OUTER_RADIUS*2:.0f} mm")
