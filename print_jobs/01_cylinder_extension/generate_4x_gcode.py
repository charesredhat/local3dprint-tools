"""
GCode generator for 4x hollow cylinder extensions (4 inches / 101.6mm tall).
Prints all 4 cylinders simultaneously layer by layer.
"""

import math

INNER_RADIUS  = 7.8
OUTER_RADIUS  = 9.8
HEIGHT        = 101.6   # 4 inches
SEGMENTS      = 128
PERIMETERS    = 5

LAYER_HEIGHT  = 0.2
NOZZLE_DIA    = 0.4
FILAMENT_DIA  = 1.75
EXTRUSION_WIDTH = NOZZLE_DIA * 1.2
FILAMENT_AREA = math.pi * (FILAMENT_DIA / 2) ** 2

PRINT_SPEED   = 50
FIRST_SPEED   = 25
TRAVEL_SPEED  = 150
BED_TEMP      = 60
NOZZLE_TEMP   = 210
RETRACT_LEN   = 1.0
RETRACT_SPEED = 45

# 2x2 grid centers
CENTERS = [
    (85.0,  85.0),
    (115.0, 85.0),
    (85.0,  115.0),
    (115.0, 115.0),
]

def extrude(dx, dy):
    dist = math.sqrt(dx*dx + dy*dy)
    return (dist * LAYER_HEIGHT * EXTRUSION_WIDTH) / FILAMENT_AREA

def ring_pts(cx, cy, radius, segments):
    return [(cx + radius * math.cos(2*math.pi*i/segments),
             cy + radius * math.sin(2*math.pi*i/segments))
            for i in range(segments)]

def write_ring(f, pts, speed, e):
    x0, y0 = pts[0]
    # retract, travel, unretract
    e -= RETRACT_LEN
    f.write(f"G1 E{e:.5f} F{RETRACT_SPEED*60:.0f}\n")
    f.write(f"G0 X{x0:.3f} Y{y0:.3f} F{TRAVEL_SPEED*60:.0f}\n")
    e += RETRACT_LEN
    f.write(f"G1 E{e:.5f} F{RETRACT_SPEED*60:.0f}\n")
    for i in range(1, len(pts) + 1):
        x1, y1 = pts[i % len(pts)]
        px, py = pts[(i-1) % len(pts)]
        e += extrude(x1-px, y1-py)
        f.write(f"G1 X{x1:.3f} Y{y1:.3f} E{e:.5f} F{speed*60:.0f}\n")
    return e

def generate(output="cylinder_extension_4x.gcode"):
    layers = int(round(HEIGHT / LAYER_HEIGHT))

    with open(output, "w") as f:
        f.write(f"""; 4x Cylinder Extension — 4 inches tall, fits over 15.4mm OD
; Inner: {INNER_RADIUS*2}mm  Outer: {OUTER_RADIUS*2}mm  Height: {HEIGHT}mm
; 4 cylinders in 2x2 grid, printed simultaneously
M104 S{NOZZLE_TEMP}
M140 S{BED_TEMP}
M190 S{BED_TEMP}
M109 S{NOZZLE_TEMP}
G28
G90
M82
G92 E0
; Purge line
G1 Z0.3 F1200
G1 X5 Y5 F3000
G1 X5 Y200 E15 F900
G92 E0
G1 Z0.5 F1200
""")
        e = 0.0

        for layer_num in range(layers):
            z = (layer_num + 1) * LAYER_HEIGHT
            speed = FIRST_SPEED if layer_num == 0 else PRINT_SPEED
            f.write(f"\n; Layer {layer_num+1}/{layers}  z={z:.2f}\n")
            f.write(f"G1 Z{z:.2f} F1200\n")

            # For each cylinder, print all perimeters outer→inner
            for cx, cy in CENTERS:
                for p in range(PERIMETERS):
                    r = OUTER_RADIUS - p * EXTRUSION_WIDTH
                    if r < INNER_RADIUS + EXTRUSION_WIDTH / 2:
                        break
                    pts = ring_pts(cx, cy, r, SEGMENTS)
                    e = write_ring(f, pts, speed, e)

        f.write(f"""
; End
M104 S0
M140 S0
G91
G1 Z10 F1200
G90
G1 X10 Y200 F3000
M84
""")

    total_layers = layers
    vol_cm3 = (e * FILAMENT_AREA) / 1000
    print(f"Saved {output}")
    print(f"  Cylinders  : 4")
    print(f"  Layers     : {total_layers}")
    print(f"  Est E      : {e:.1f} mm filament")
    print(f"  Est volume : {vol_cm3:.1f} cm³  (~{vol_cm3*1.24:.1f}g PLA)")
    hrs = (total_layers * len(CENTERS) * PERIMETERS * (2*math.pi*OUTER_RADIUS) / SEGMENTS) / (PRINT_SPEED * 60)
    print(f"  Est time   : ~{(total_layers * 4 * PERIMETERS * 2*math.pi*OUTER_RADIUS/SEGMENTS/PRINT_SPEED)/60:.0f} min (rough)")

if __name__ == "__main__":
    generate()
