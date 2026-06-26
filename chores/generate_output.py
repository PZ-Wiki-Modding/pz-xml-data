import yaml, json, os
from pathlib import Path


SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent

DATA_DIR = REPO_ROOT / "data"
OUT_FILE = REPO_ROOT / "out" / "data.json"


## UTILITY

def find_description(source: dict, code: str) -> str:
    code_segments = code.split('/')
    objects = code_segments[1] # attributes or elements
    
    # search in types of source
    for type_name, type_data in source.get('types', {}).items():
        # check if searching in this type
        if type_name != code_segments[0]:
            continue
        # parse objects in this type
        for obj in type_data.get(objects, []):
            # check if the name matches
            if obj.get('info', {}).get('name') != code_segments[2]:
                continue
            return obj.get('description', code)

    raise ValueError(f"Description not found for code: {code}")



def recurse_find_desc(source: dict, d: dict):
    """Recursively find '#desc' keys in a dictionary and copy their values to 'description'."""
    to_set = None
    for key, value in d.items():
        if key == "#desc":
            to_set = (key, value)
            # d["description"] = value
        if isinstance(value, dict):
            recurse_find_desc(source, value)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    recurse_find_desc(source, item)
    if to_set is not None:
        key, value = to_set
        d["description"] = find_description(source, value)
        # del d[key]

## MAIN

out = {}
for yaml_file in DATA_DIR.rglob("*.yaml"):
    file_name = yaml_file.stem

    with open(yaml_file, 'r') as f:
        data = yaml.safe_load(f)

    # copy '#desc' to 'description'
    recurse_find_desc(data, data)


    out[file_name] = data    


OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_FILE, 'w') as f:
    json.dump(out, f, indent=2)

