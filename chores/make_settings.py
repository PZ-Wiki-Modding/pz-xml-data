import json
from pathlib import Path

repo_root = Path(__file__).parent.parent
output_path = repo_root / 'out' / 'data.json'

setting_path = repo_root / 'out' / 'settings.json'

base_link = r"https://raw.githubusercontent.com/PZ-Wiki-Modding/pz-xml-data/refs/heads/main/schemas/"

with open(output_path, 'r') as f:
    data = json.load(f)

out = {
    'xml.fileAssociations': []
}
for xml_name, xml_data in data.items():
    patterns = xml_data.get('patterns', [])

    for pattern in patterns:
        out['xml.fileAssociations'].append({
            'pattern': pattern,
            'systemId': f"{base_link}{xml_name}.xsd"
        })

with open(setting_path, 'w') as f:
    json.dump(out, f, indent=2)
