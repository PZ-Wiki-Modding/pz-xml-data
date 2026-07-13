import yaml, json
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from pathlib import Path
import re


def load_yaml_schema(yaml_path: Path):
    """Load schema definition from YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def markdown_to_html(markdown_text):
    """
    Convert markdown to HTML for better VSCode tooltip display.
    
    The problem comes from Red Hat XML extension which doesn't properly support markdown
    but this may also be linked to the schemas using XML and the XML syntax being fucked.
    This issue here: https://github.com/redhat-developer/vscode-xml/issues/951#issuecomment-1818808628
    is the reason why we need to do all these convertion. What is being done here:
    - each paragraph is wrapped in <p> tags
    - each code block lines are wrapped in their own <pre><code> tags
    - all other basic markdown syntax is converted to HTML tags (bold, italic, headers, lists)
    - all HTML tags are escaped to avoid XML parsing issues
    """
    html = markdown_text
    
    # First, protect code blocks and inline code by replacing them with placeholders
    code_blocks = []
    def preserve_code_block(match):
        code_content = match.group(1)
        # Escape HTML tags inside code blocks
        code_content = code_content.replace('<', '&lt;').replace('>', '&gt;')
        # Split each line into its own <pre><code> element
        lines = code_content.split('\n')
        code_html = ''
        for line in lines:
            # Replace leading spaces with &nbsp;
            leading_spaces = len(line) - len(line.lstrip(' '))
            nbsp_line = '&nbsp;' * leading_spaces + line[leading_spaces:]
            code_html += f'__PRETAG__pre__GTTAG____PRETAG__code__GTTAG__{nbsp_line}__PRETAG__/code__GTTAG____PRETAG__/pre__GTTAG__'
        code_blocks.append(code_html)
        return f'__CODE_BLOCK_{len(code_blocks)-1}__'
    
    # Protect triple backtick code blocks
    html = re.sub(r'```\n(.*?)\n```', preserve_code_block, html, flags=re.DOTALL)
    
    # Handle inline code - escape HTML tags in inline code too
    def preserve_inline_code(match):
        code_content = match.group(1)
        code_content = code_content.replace('<', '&lt;').replace('>', '&gt;')
        return f'__PRETAG__code__GTTAG__{code_content}__PRETAG__/code__GTTAG__'
    html = re.sub(r'`([^`]+)`', preserve_inline_code, html)
    
    # Now handle markdown syntax on non-code parts
    # Handle bold with **text** only (not __text__ to avoid matching underscores)
    html = re.sub(r'\*\*([^*]+)\*\*', r'__PRETAG__strong__GTTAG__\1__PRETAG__/strong__GTTAG__', html)
    
    # Handle italic with *text* only (not _text_ to avoid matching underscores in identifiers)
    html = re.sub(r'\*([^*]+)\*', r'__PRETAG__em__GTTAG__\1__PRETAG__/em__GTTAG__', html)
    
    # Handle headers
    html = re.sub(r'^### (.+)$', r'__PRETAG__h3__GTTAG__\1__PRETAG__/h3__GTTAG__', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'__PRETAG__h2__GTTAG__\1__PRETAG__/h2__GTTAG__', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'__PRETAG__h1__GTTAG__\1__PRETAG__/h1__GTTAG__', html, flags=re.MULTILINE)
    
    # Handle unordered lists (- or *)
    lines = html.split('\n')
    result_lines = []
    in_list = False
    for line in lines:
        if re.match(r'^\s*[-*]\s+', line):
            if not in_list:
                result_lines.append('__PRETAG__ul__GTTAG__')
                in_list = True
            item_text = re.sub(r'^\s*[-*]\s+', '', line)
            result_lines.append(f'__PRETAG__li__GTTAG__{item_text}__PRETAG__/li__GTTAG__')
        else:
            if in_list and line.strip():
                result_lines.append('__PRETAG__/ul__GTTAG__')
                in_list = False
            result_lines.append(line)
    if in_list:
        result_lines.append('__PRETAG__/ul__GTTAG__')
    html = '\n'.join(result_lines)
    
    # Split by code blocks and paragraphs
    # Don't wrap code blocks in <p> tags - only wrap regular text
    parts = html.split('__CODE_BLOCK_')
    processed_parts = []
    
    # Process first part
    part = parts[0]
    if part.strip():
        # Convert double newlines to paragraph breaks
        paragraphs = re.split(r'\n\n+', part)
        for para in paragraphs:
            para = para.strip()
            if para:
                processed_parts.append(f'__PRETAG__p__GTTAG__{para}__PRETAG__/p__GTTAG__')
    
    # Process remaining parts (interleaved with code blocks)
    for i in range(1, len(parts)):
        # Extract code block number and remaining text
        match = re.match(r'(\d+)__(.*)$', parts[i], re.DOTALL)
        if match:
            block_num = match.group(1)
            remaining = match.group(2)
            
            # Add the code block back
            processed_parts.append(f'__CODE_BLOCK_{block_num}__')
            
            # Process remaining text
            if remaining.strip():
                paragraphs = re.split(r'\n\n+', remaining)
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        processed_parts.append(f'__PRETAG__p__GTTAG__{para}__PRETAG__/p__GTTAG__')
    
    html = ''.join(processed_parts)
    
    # Restore code blocks
    for i, code_block in enumerate(code_blocks):
        html = html.replace(f'__CODE_BLOCK_{i}__', code_block)
    
    return html


def add_documentation_with_html(parent, description):
    """
    Add documentation to an annotation element.
    Converts markdown to HTML and wraps in CDATA.
    """
    if not description:
        return
    
    # Convert markdown to HTML (using markers instead of actual tags)
    html = markdown_to_html(description)
    
    # Create documentation element with CDATA marker
    doc = ET.SubElement(parent, 'xs:documentation')
    doc.text = f"__CDATA_START__{html}__CDATA_END__"


def create_xsd_from_yaml(schema_data: dict, output_xsd_path: Path):
    """Generate XSD schema file from YAML definition."""
    # Create root schema element
    schema = ET.Element('xs:schema')
    schema.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema')
    
    # Add root element
    root_def = schema_data['root']
    root_elem = ET.SubElement(schema, 'xs:element')
    root_elem.set('name', root_def['name'])
    root_elem.set('type', root_def['type'])
    
    root_annotation = ET.SubElement(root_elem, 'xs:annotation')
    add_documentation_with_html(root_annotation, f"Root element for {root_def['name']} configuration.")
    
    # Collect all union types first
    union_types = {}
    union_counter = 0
    
    def get_or_create_union_type(type_list):
        """Create or get a union type for a list of types, returns the type name."""
        nonlocal union_counter
        type_key = '|'.join(sorted(str(t) for t in type_list))
        if type_key not in union_types:
            union_counter += 1
            union_type_name = f'union_{union_counter}'
            union_types[type_key] = (union_type_name, type_list)
        return union_types[type_key][0]
    
    # First pass: scan all elements for union types
    def scan_for_unions(type_def):
        if type_def is None:
            return
        elements = type_def.get('elements', [])
        for elem_def in elements:
            attrs = elem_def.get('metadata', {})
            elem_type = attrs.get('type')
            if isinstance(elem_type, list):
                get_or_create_union_type(elem_type)
        
        # Also scan attributes
        attrs_list = type_def.get('attributes', [])
        for attr_def in attrs_list:
            attrs = attr_def.get('metadata', {})
            attr_type = attrs.get('type')
            if isinstance(attr_type, list):
                get_or_create_union_type(attr_type)
    
    types = schema_data.get('types', {})
    for type_def in types.values():
        scan_for_unions(type_def)
    
    # Create union simple types
    for type_key, (union_type_name, type_list) in union_types.items():
        simple_type = ET.SubElement(schema, 'xs:simpleType')
        simple_type.set('name', union_type_name)
        union_elem = ET.SubElement(simple_type, 'xs:union')
        union_elem.set('memberTypes', ' '.join(str(t) for t in type_list))
    
    # Add type definitions (complex or simple)
    for type_name, type_def in types.items():
        # Skip incomplete type definitions
        if type_def is None:
            continue
        
        type_kind = type_def.get('type', 'complex')
        
        if type_kind == 'simple':
            # Handle simple types (enumerations, restrictions, etc.)
            simple_type = ET.SubElement(schema, 'xs:simpleType')
            simple_type.set('name', type_name)
            
            # Add restriction
            restriction = type_def.get('restrictions', {})
            if restriction:
                restriction_elem = ET.SubElement(simple_type, 'xs:restriction')
                restriction_elem.set('base', restriction.get('base', 'xs:string'))
                
                # Add enumeration values
                enumerations = restriction.get('enumeration', [])
                for enum_def in enumerations:
                    enum_metadata = enum_def.get('metadata', {})
                    enum_elem = ET.SubElement(restriction_elem, 'xs:enumeration')
                    enum_elem.set('value', str(enum_metadata.get('value', '')))
                    
                    # Add documentation
                    if 'description' in enum_def:
                        annotation = ET.SubElement(enum_elem, 'xs:annotation')
                        add_documentation_with_html(annotation, enum_def.get('description', ''))
                
                # min max restrictions
                min = restriction.get('minimum')
                max = restriction.get('maximum')
                if min is not None or max is not None:
                    # Add min/max restrictions for numeric types
                    if min is not None:
                        min_elem = ET.SubElement(restriction_elem, 'xs:minInclusive')
                        min_elem.set('value', str(min))
                    if max is not None:
                        max_elem = ET.SubElement(restriction_elem, 'xs:maxInclusive')
                        max_elem.set('value', str(max))
        elif type_kind == 'complex':
            # Handle complex types
            complex_type = ET.SubElement(schema, 'xs:complexType')
            complex_type.set('name', type_name)
            
            # Add elements using xs:all or xs:choice based on configuration
            elements = type_def.get('elements', [])
            if elements:
                # Determine which composition model to use (default: xs:all)
                composition = type_def.get('composition', 'all')
                
                if composition == 'choice':
                    # For choice composition, all elements can appear in any order and repeat
                    container_elem = ET.SubElement(complex_type, 'xs:choice')
                    container_elem.set('minOccurs', '0')
                    container_elem.set('maxOccurs', 'unbounded')
                    
                    for elem_def in elements:
                        attrs = elem_def.get('metadata', {})
                        elem = ET.SubElement(container_elem, 'xs:element')
                        elem.set('name', elem_def['name'])
                        
                        # Handle type - check if it's a union (list)
                        elem_type = attrs.get('type')
                        if isinstance(elem_type, list):
                            union_type_name = get_or_create_union_type(elem_type)
                            attrs['type'] = union_type_name
                        
                        for k, v in attrs.items():
                            elem.set(k, str(v))
                        
                        # Add documentation
                        if 'description' in elem_def:
                            annotation = ET.SubElement(elem, 'xs:annotation')
                            add_documentation_with_html(annotation, elem_def.get('description', ''))
                else:
                    # Default to xs:all
                    all_elem = ET.SubElement(complex_type, 'xs:all')
                    
                    for elem_def in elements:
                        attrs = elem_def.get('metadata', {})
                        elem = ET.SubElement(all_elem, 'xs:element')
                        elem.set('name', elem_def['name'])
                        
                        # Handle type - check if it's a union (list)
                        elem_type = attrs.get('type')
                        if isinstance(elem_type, list):
                            union_type_name = get_or_create_union_type(elem_type)
                            attrs['type'] = union_type_name
                        
                        for k, v in attrs.items():
                            elem.set(k, str(v))
                        
                        # Add documentation
                        if 'description' in elem_def:
                            annotation = ET.SubElement(elem, 'xs:annotation')
                            add_documentation_with_html(annotation, elem_def.get('description', ''))
            
            # Add attributes
            attrs_list = type_def.get('attributes', [])
            for attr_def in attrs_list:
                attrs = attr_def.get('metadata', {})
                attr = ET.SubElement(complex_type, 'xs:attribute')
                attr.set('name', attr_def['name'])
                
                # Handle type - check if it's a union (list)
                attr_type = attrs.get('type')
                if isinstance(attr_type, list):
                    union_type_name = get_or_create_union_type(attr_type)
                    attr.set('type', union_type_name)
                else:
                    attr.set('type', attr_type if attr_type else 'xs:string')
                
                if attrs.get('use'):
                    attr.set('use', attrs['use'])
                
                # Add documentation
                if 'description' in attr_def:
                    annotation = ET.SubElement(attr, 'xs:annotation')
                    add_documentation_with_html(annotation, attr_def.get('description', ''))
        else:
            raise ValueError(f"Unknown type kind '{type_kind}' for type '{type_name}'")
    
    # Pretty print the XML
    xml_str = minidom.parseString(ET.tostring(schema)).toprettyxml(indent='  ')
    
    # Remove the XML declaration and extra blank lines, then add back our own
    lines = xml_str.split('\n')[1:]  # Skip the auto-generated declaration
    xml_str = '<?xml version="1.0" encoding="utf-8"?>\n' + '\n'.join(line for line in lines if line.strip())
    
    # Post-process to convert CDATA markers to actual CDATA sections and restore HTML tags
    # Replace __CDATA_START__content__CDATA_END__ with <![CDATA[content]]>
    def convert_cdata(match):
        content = match.group(1)
        # Restore HTML tag markers to actual tags
        content = content.replace('__PRETAG__', '<').replace('__GTTAG__', '>')
        # Escape any CDATA end markers in the content
        content = content.replace(']]>', ']]>]]<![CDATA[')
        return f'<![CDATA[\n        {content}\n        ]]>'
    
    xml_str = re.sub(r'__CDATA_START__(.+?)__CDATA_END__', convert_cdata, xml_str, flags=re.DOTALL)
    
    # Remove any placeholder attributes we might have added
    xml_str = re.sub(r'\s+_placeholders="[^"]*"', '', xml_str)
    
    # Write to file
    os.makedirs(os.path.dirname(output_xsd_path), exist_ok=True)
    with open(output_xsd_path, 'w') as f:
        f.write(xml_str)
    
    print(f"Generated XSD schema: {output_xsd_path}")


if __name__ == '__main__':
    # Get the script directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    output_path = repo_root / 'out' / 'data.json'

    with open(output_path, 'r') as f:
        data = json.load(f)

    for xml_name, xml_data in data.items():
        xsd_file = repo_root / 'schemas' / f"{xml_name}.xsd"

        create_xsd_from_yaml(xml_data, xsd_file)
