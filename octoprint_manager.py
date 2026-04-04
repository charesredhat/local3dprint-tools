"""
OctoPrint automation manager.
Handles selecting, uploading, and starting print jobs from the local tree.

Configuration is loaded from a .env file (never committed to git):
  OCTOPRINT_URL=http://192.168.x.x:5000
  OCTOPRINT_API_KEY=your_api_key_here
"""

import os
import sys
import json
import time
import pathlib
import requests
from dotenv import load_dotenv

load_dotenv()

# ── Config (from environment — never hardcode secrets) ────────────────────────
OCTOPRINT_URL = os.environ.get("OCTOPRINT_URL", "").rstrip("/")
API_KEY       = os.environ.get("OCTOPRINT_API_KEY", "")

if not OCTOPRINT_URL or not API_KEY:
    sys.exit(
        "ERROR: OCTOPRINT_URL and OCTOPRINT_API_KEY must be set.\n"
        "Copy .env.example to .env and fill in your values."
    )

HEADERS = {"X-Api-Key": API_KEY}

JOBS_DIR = pathlib.Path(__file__).parent / "print_jobs"

# ── Security helpers ──────────────────────────────────────────────────────────

def safe_local_path(user_input):
    """
    Resolve a user-supplied local path and reject path traversal attempts.
    The resolved path must be within JOBS_DIR.
    """
    try:
        resolved = pathlib.Path(user_input).expanduser().resolve()
    except Exception as exc:
        raise ValueError(f"Invalid path: {exc}")
    try:
        resolved.relative_to(JOBS_DIR.resolve())
    except ValueError:
        raise ValueError(
            f"Path must be inside {JOBS_DIR}. "
            "Paths outside the print_jobs directory are not allowed."
        )
    return resolved

def safe_remote_path(user_input):
    """
    Sanitize a remote OctoPrint path.
    Strips leading slashes, rejects '..' components and null bytes.
    """
    path = user_input.strip().strip("/")
    if not path:
        raise ValueError("Remote path must not be empty.")
    if "\x00" in path:
        raise ValueError("Remote path contains null bytes.")
    parts = path.split("/")
    for part in parts:
        if part in ("", ".", ".."):
            raise ValueError(f"Unsafe path component: {repr(part)}")
    return path

# ── Low-level helpers ─────────────────────────────────────────────────────────

def api(method, endpoint, **kwargs):
    url = f"{OCTOPRINT_URL}/api/{endpoint}"
    r = requests.request(method, url, headers=HEADERS, timeout=15, **kwargs)
    r.raise_for_status()
    return r.json() if r.content else {}

def get_printer_state():
    data = api("GET", "printer")
    return data["state"]["text"], data["state"]["flags"], data["temperature"]

def list_files(path=""):
    endpoint = f"files/local/{path}" if path else "files/local"
    return api("GET", endpoint)

def ensure_remote_folder(path):
    """Create folder hierarchy on OctoPrint if it doesn't already exist."""
    parts = safe_remote_path(path).split("/")
    built = ""
    for part in parts:
        payload = {"foldername": part}
        if built:
            payload["path"] = built
        try:
            r = requests.post(
                f"{OCTOPRINT_URL}/api/files/local",
                headers=HEADERS,
                data=payload,
                timeout=15,
            )
            # 409 Conflict = folder already exists, that's fine
            if r.status_code not in (200, 201, 409):
                r.raise_for_status()
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 409:
                pass  # folder exists
            else:
                raise
        built = f"{built}/{part}".lstrip("/")

def upload_gcode(local_path_str, remote_folder=""):
    """Upload a local .gcode file to OctoPrint (path-traversal safe)."""
    local_path = safe_local_path(local_path_str)

    if not local_path.is_file():
        raise FileNotFoundError(f"File not found: {local_path}")
    if local_path.suffix.lower() != ".gcode":
        raise ValueError("Only .gcode files may be uploaded.")

    if remote_folder:
        remote_folder = safe_remote_path(remote_folder)
        ensure_remote_folder(remote_folder)

    with local_path.open("rb") as fh:
        data = {"path": remote_folder} if remote_folder else {}
        r = requests.post(
            f"{OCTOPRINT_URL}/api/files/local",
            headers=HEADERS,
            files={"file": (local_path.name, fh)},
            data=data,
            timeout=60,
        )
        r.raise_for_status()
        return r.json()

def select_and_print(remote_path):
    """Select a file and start printing (path-traversal safe)."""
    remote_path = safe_remote_path(remote_path)
    endpoint = f"files/local/{remote_path}"
    api("POST", endpoint, json={"command": "select", "print": True})
    print(f"  Started: {remote_path}")

def cancel_print():
    api("POST", "job", json={"command": "cancel"})

def pause_print():
    api("POST", "job", json={"command": "pause", "action": "pause"})

def resume_print():
    api("POST", "job", json={"command": "pause", "action": "resume"})

def get_job_status():
    return api("GET", "job")

# ── High-level helpers ────────────────────────────────────────────────────────

def print_status():
    state, flags, temps = get_printer_state()
    job = get_job_status()
    print(f"\n=== Printer Status ===")
    print(f"  State  : {state}")
    print(f"  Nozzle : {temps.get('tool0',{}).get('actual','?')}°C / {temps.get('tool0',{}).get('target','?')}°C")
    print(f"  Bed    : {temps.get('bed',{}).get('actual','?')}°C / {temps.get('bed',{}).get('target','?')}°C")
    if flags.get("printing"):
        prog = job.get("progress", {})
        name = job.get("job", {}).get("file", {}).get("name", "?")
        pct  = prog.get("completion") or 0
        left = prog.get("printTimeLeft") or 0
        print(f"  File   : {name}")
        print(f"  Done   : {pct:.1f}%  ({left//60:.0f} min remaining)")

def monitor(interval=30):
    """Poll and print status until print finishes."""
    print("Monitoring print... Ctrl+C to stop.\n")
    try:
        while True:
            print_status()
            _, flags, _ = get_printer_state()
            if not flags.get("printing") and not flags.get("paused"):
                print("\nPrint finished (or not printing).")
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")

def print_tree(base_dir):
    """Print a visual tree of the local print_jobs folder."""
    base = pathlib.Path(base_dir)
    print(f"\n{base}/")
    for root, dirs, files in os.walk(base):
        dirs.sort()
        level = pathlib.Path(root).relative_to(base).parts.__len__()
        indent = "│   " * (level - 1) + "├── " if level > 0 else ""
        if level > 0:
            print(f"{indent}{os.path.basename(root)}/")
        for i, f in enumerate(sorted(files)):
            connector = "└── " if i == len(files) - 1 else "├── "
            print(f"{'│   ' * level}{connector}{f}")

# ── CLI ───────────────────────────────────────────────────────────────────────

MENU = """
OctoPrint Manager
─────────────────
1) Show printer status
2) List remote files
3) Start cylinder_extension print
4) Upload a local GCode file
5) Cancel current print
6) Monitor current print
7) Show local job tree
q) Quit
"""

def main():
    while True:
        print(MENU)
        choice = input("Choice: ").strip().lower()

        if choice == "1":
            print_status()

        elif choice == "2":
            data = list_files()
            def _list(items, indent=0):
                for item in items:
                    kind = "/" if item.get("type") == "folder" else ""
                    print("  " * indent + item["name"] + kind)
                    if "children" in item:
                        _list(item["children"], indent + 1)
            _list(data.get("files", []))

        elif choice == "3":
            remote = "print_jobs/01_cylinder_extension/cylinder_extension.gcode"
            state, flags, _ = get_printer_state()
            if flags.get("printing"):
                print("Printer is already printing! Cancel first.")
            else:
                select_and_print(remote)
                monitor()

        elif choice == "4":
            path = input("Local GCode path (must be inside print_jobs/): ").strip()
            folder = input("Remote folder (e.g. print_jobs/02_mypart): ").strip()
            try:
                result = upload_gcode(path, folder)
                print(f"Uploaded: {result['files']['local']['path']}")
            except (ValueError, FileNotFoundError) as exc:
                print(f"ERROR: {exc}")

        elif choice == "5":
            cancel_print()
            print("Print cancelled.")

        elif choice == "6":
            monitor()

        elif choice == "7":
            print_tree(JOBS_DIR)

        elif choice == "q":
            break

if __name__ == "__main__":
    main()
