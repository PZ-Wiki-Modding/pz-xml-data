import subprocess, shutil, argparse, json
from pathlib import Path

argument_parser = argparse.ArgumentParser(description="Validate a folder of XML files against the animNode.xsd schema.")
argument_parser.add_argument("folder", type=Path, help="Path to the folder containing XML files to validate.")
args = argument_parser.parse_args()

result = shutil.which("xmllint")
if result is None:
    print("Error: xmllint is not installed or not found in PATH.")
    exit(1)

folder = Path(args.folder)

if not folder.is_dir():
    print(f"Error: {folder} is not a valid directory.")
    exit(1)

# load all schema 
output_file = Path(__file__).parent.parent / "out" / "data.json"
schemas_path = Path(__file__).parent.parent / "schemas"

with open(output_file, "r") as f:
    xml = json.load(f)

for xml_type, xml_data in xml.items():
    schema_file = schemas_path / f"{xml_type}.xsd"
    if not schema_file.exists():
        print(f"Warning: Schema file {schema_file} does not exist. Skipping validation for {xml_type}.")
        continue

    patterns = xml_data.get("patterns", [])
    for pattern in patterns:
        # Adapt pattern to folder path
        # e.g., if folder is ".../AnimSets/player/aim" and pattern is "**/AnimSets/**/*.xml"
        # strip matching components to get "**/*.xml"
        adapted_pattern = pattern.lstrip("*/")
        
        # Check if any path part of the folder matches the pattern
        folder_parts = folder.parts
        pattern_parts = adapted_pattern.split("/")
        
        # Find where pattern starts matching folder path
        match_idx = 0
        for i, pattern_part in enumerate(pattern_parts):
            if pattern_part.startswith("*"):
                print(f"Warning: Pattern '{pattern}' contains a wildcard '*' which may not match folder structure correctly.")
                break
            # Check if this pattern part is in the folder path
            if pattern_part in folder_parts:
                match_idx = i + 1
            else:
                print(f"Warning: Pattern '{pattern}' does not match folder structure. Stopping at part '{pattern_part}'.")
                break
        
        # If we found matches, use the remaining pattern
        if match_idx > 0:
            adapted_pattern = "/".join(pattern_parts[match_idx:])
        
        for xml_file in folder.rglob(adapted_pattern):
            # print(f"Validating {xml_file} against {schema_file}...")

            validation_command = f'xmllint --schema "{schema_file}" "{xml_file}" --noout'
            validation_result = subprocess.run(validation_command, shell=True, capture_output=True, text=True)
            if validation_result.returncode != 0:
                print(f"\033[91m{xml_file} failed:\n\033[3m{validation_result.stderr}\033[0m")
            # else:
            #     print(f"\033[92m{xml_file} is valid.\033[0m")





