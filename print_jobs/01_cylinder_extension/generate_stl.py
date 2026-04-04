"""
Generate a hollow cylinder (sleeve/extension) STL that fits snugly over a 15.4mm OD cylinder.
Inner diameter: 15.6mm (0.2mm clearance for snug press fit)
Outer diameter: 19.6mm (2mm wall thickness)
Height: 25mm
"""

import numpy as np
from stl import mesh

INNER_RADIUS = 7.8     # 15.6mm ID — snug fit over 15.4mm cylinder
OUTER_RADIUS = 9.8     # 19.6mm OD — 2mm wall thickness
HEIGHT = 25.0          # mm
SEGMENTS = 64          # polygon resolution (higher = smoother)

def circle_points(radius, segments, z):
    angles = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    return np.column_stack([radius * np.cos(angles), radius * np.sin(angles), np.full(segments, z)])

def build_cylinder_mesh():
    seg = SEGMENTS
    triangles = []

    # Top/bottom ring points
    inner_bot = circle_points(INNER_RADIUS, seg, 0)
    outer_bot = circle_points(OUTER_RADIUS, seg, 0)
    inner_top = circle_points(INNER_RADIUS, seg, HEIGHT)
    outer_top = circle_points(OUTER_RADIUS, seg, HEIGHT)

    for i in range(seg):
        n = (i + 1) % seg

        # Bottom annular face (normal pointing down -Z)
        triangles.append([outer_bot[i], inner_bot[i], outer_bot[n]])
        triangles.append([inner_bot[i], inner_bot[n], outer_bot[n]])

        # Top annular face (normal pointing up +Z)
        triangles.append([inner_top[i], outer_top[i], outer_top[n]])
        triangles.append([inner_top[i], outer_top[n], inner_top[n]])

        # Outer wall
        triangles.append([outer_bot[i], outer_top[i], outer_bot[n]])
        triangles.append([outer_top[i], outer_top[n], outer_bot[n]])

        # Inner wall (normals inward)
        triangles.append([inner_bot[n], inner_top[i], inner_bot[i]])
        triangles.append([inner_bot[n], inner_top[n], inner_top[i]])

    triangles = np.array(triangles)
    cylinder = mesh.Mesh(np.zeros(len(triangles), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(triangles):
        cylinder.vectors[i] = tri

    return cylinder


if __name__ == "__main__":
    m = build_cylinder_mesh()
    out = "cylinder_extension.stl"
    m.save(out)
    print(f"Saved {out}")
    print(f"  Inner diameter : {INNER_RADIUS*2:.1f} mm  (fits over 15.4 mm cylinder)")
    print(f"  Outer diameter : {OUTER_RADIUS*2:.1f} mm")
    print(f"  Wall thickness : {OUTER_RADIUS - INNER_RADIUS:.1f} mm")
    print(f"  Height         : {HEIGHT:.1f} mm")
    print(f"  Segments       : {SEGMENTS}")
