# 3dprinting — Claude Project Context

Local 3D print management tools for an OctoPrint-connected Creality Ender 3 V2.

## Repository layout

```
3dprinting/
├── CLAUDE.md                   ← this file
├── README.md                   ← project overview
├── octoprint_manager.py        ← OctoPrint API wrapper
├── .env                        ← API keys (gitignored)
├── .env.example                ← env template
├── info/                       ← session changelogs and notes
└── print_jobs/                 ← one folder per print job
    ├── 01_cylinder_extension/  ← hollow sleeve print
    └── cathelmet/              ← cat helmet (katzenhelm)
```

## Print job folder convention

Each print job folder contains:
- `README.md` — print parameters, filament usage, notes
- `*.stl` — source mesh (gitignored, regenerate locally)
- `gcode/` or `*.gcode` — sliced output (gitignored, regenerate locally)
- `generate_*.py` — scripts used to produce STL/gcode (committed)

## Environment

- `OCTOPRINT_URL` — base URL of local OctoPrint instance
- `OCTOPRINT_API_KEY` — OctoPrint API key

## Key file

- [octoprint_manager.py](octoprint_manager.py) — upload, start, monitor prints via OctoPrint REST API
