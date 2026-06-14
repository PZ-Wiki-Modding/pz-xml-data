import yaml, json, os
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent

DATA_DIR = REPO_ROOT / "data"
OUT_FILE = REPO_ROOT / "out" / "data.json"


## UTILITY

def recurse_find_desc(d: dict):
    """Recursively find '#desc' keys in a dictionary and copy their values to 'description'."""
    for key, value in d.items():
        if key == "#desc":
            d["description"] = value
        if isinstance(value, dict):
            recurse_find_desc(value)

## MAIN

out = {}
for yaml_file in DATA_DIR.rglob("*.yaml"):
    file_name = yaml_file.stem

    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # copy '#desc' to 'description'



    out[file_name] = data    


OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FILE, 'w') as f:
    json.dump(out, f, indent=2)

