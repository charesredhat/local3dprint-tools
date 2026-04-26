# local3dprint-tools

Local 3D print management tools for an OctoPrint-connected Creality Ender 3 V2.

## Setup

```bash
pip install requests python-dotenv numpy numpy-stl
cp .env.example .env
# edit .env — set OCTOPRINT_URL and OCTOPRINT_API_KEY
```

---

## octoprint_manager.py

Interactive CLI for managing prints via the OctoPrint REST API.

```bash
python octoprint_manager.py
```

**Menu options:**

| # | Action |
| - | ------ |
| 1 | Show printer status (state, temps, progress) |
| 2 | List all files on OctoPrint server |
| 3 | Start cylinder_extension print and monitor |
| 4 | Upload a local `.gcode` file to OctoPrint |
| 5 | Cancel current print |
| 6 | Monitor current print (polls every 30 s) |
| 7 | Show local `print_jobs/` tree |
| q | Quit |

**Programmatic use:**

```python
from octoprint_manager import upload_gcode, select_and_print, monitor

upload_gcode("print_jobs/cathelmet/gcode/katzenhelm4inchs.gcode", "cathelmet")
select_and_print("cathelmet/katzenhelm4inchs.gcode")
monitor()
```

---

## Camera Feed

OctoPrint streams webcam video via mjpg-streamer on port 8080.

| URL | Purpose |
| --- | ------- |
| `http://192.168.1.192:8080/?action=stream` | Live MJPEG stream |
| `http://192.168.1.192:8080/?action=snapshot` | Single JPEG snapshot |

Grab a snapshot from the terminal:

```bash
curl http://192.168.1.192:8080/?action=snapshot -o snapshot.jpg
```

**Note:** Camera is currently mounted sideways. Enable rotation in OctoPrint under
Settings → Webcam → Rotate 90°, or set `rotate90: true` via the API.

---

## print_jobs/01_cylinder_extension/

Hollow sleeve that press-fits over a 15.4 mm OD cylinder (15.6 mm ID, 19.6 mm OD, 2 mm wall).

### generate_stl.py — single cylinder, 25 mm tall

```bash
cd print_jobs/01_cylinder_extension
python generate_stl.py
# → cylinder_extension.stl
```

Outputs a single hollow cylinder STL. Edit `INNER_RADIUS`, `OUTER_RADIUS`, `HEIGHT`, or `SEGMENTS` at the top of the file to change geometry.

### generate_gcode.py — single cylinder GCode

```bash
python generate_gcode.py
# → cylinder_extension.gcode
```

Generates ready-to-print GCode for the Ender 3. Print settings (layer height, speeds, temps, perimeters) are constants at the top of the file.

| Setting | Value |
|---------|-------|
| Layer height | 0.2 mm |
| Nozzle | 0.4 mm / 210 °C |
| Bed | 60 °C |
| Speed | 50 mm/s (25 mm/s first layer) |
| Perimeters | 5 (solid walls, no infill) |

### generate_4x_stl.py — 4-cylinder batch, 4 inches tall

```bash
python generate_4x_stl.py
# → cylinder_extension_4x.stl
```

Same ID/OD as the single cylinder but 101.6 mm (4 in) tall. Arranges 4 cylinders in a 2×2 grid (30 mm center-to-center) sized to fit the Ender 3 220×220 mm bed.

### generate_4x_gcode.py — 4-cylinder batch GCode

```bash
python generate_4x_gcode.py
# → cylinder_extension_4x.gcode
```

Prints all 4 cylinders simultaneously, layer by layer. Same print settings as the single-cylinder script.

---

## print_jobs/cathelmet/

Cat helmet model (`katzenhelm`), sliced with Simplify3D 5.1.2. See [print_jobs/cathelmet/README.md](print_jobs/cathelmet/README.md) for full print parameters.

GCode files in `gcode/`:

| File | Description |
|------|-------------|
| `katzenhelm.gcode` | Original size (~48 mm tall, 3 h 25 min) |
| `katzenhelm4inchs.gcode` | Scaled to 4 inches (~101.6 mm tall) |

Upload to OctoPrint:

```bash
python octoprint_manager.py
# choose option 4
# local path : print_jobs/cathelmet/gcode/katzenhelm4inchs.gcode
# remote folder : cathelmet
```
