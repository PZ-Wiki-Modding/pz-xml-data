import yaml
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
from pathlib import Path
import re


def load_yaml_schema(yaml_path):
    """Load schema definition from YAML file."""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


def markdown_to_html(markdown_text):
    """
    Convert markdown to HTML for better VSCode tooltip display.
    Handles basic markdown syntax.
    Only escapes HTML tags inside code blocks.
    Uses markers for HTML tags to avoid XML escaping.
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


def create_xsd_from_yaml(yaml_path, output_xsd_path):
    """Generate XSD schema file from YAML definition."""
    schema_data = load_yaml_schema(yaml_path)
    
    # Create root schema element
    schema = ET.Element('xs:schema')
    schema.set('xmlns:xs', 'http://www.w3.org/2001/XMLSchema')
    
    # Add root element
    root_def = schema_data.get('root', {})
    root_elem = ET.SubElement(schema, 'xs:element')
    root_elem.set('name', root_def.get('name', 'root'))
    root_elem.set('type', root_def.get('type', 'RootType'))
    
    root_annotation = ET.SubElement(root_elem, 'xs:annotation')
    add_documentation_with_html(root_annotation, f"Root element for {root_def.get('name', 'root')} configuration.")
    
    # Add complex type definitions
    types = schema_data.get('types', {})
    for type_name, type_def in types.items():
        complex_type = ET.SubElement(schema, 'xs:complexType')
        complex_type.set('name', type_name)
        
        # Add elements using xs:all (allows any order)
        elements = type_def.get('elements', [])
        if elements:
            all_elem = ET.SubElement(complex_type, 'xs:all')
            
            for elem_def in elements:
                attrs = elem_def.get('attributes', {})
                elem = ET.SubElement(all_elem, 'xs:element')
                elem.set('name', attrs.get('name', 'element'))
                elem.set('type', attrs.get('type', 'xs:string'))
                
                min_occurs = attrs.get('minOccurs')
                if min_occurs is not None:
                    elem.set('minOccurs', str(min_occurs))
                
                max_occurs = attrs.get('maxOccurs')
                if max_occurs is not None:
                    elem.set('maxOccurs', str(max_occurs))
                
                # Add documentation
                if 'description' in elem_def:
                    annotation = ET.SubElement(elem, 'xs:annotation')
                    add_documentation_with_html(annotation, elem_def['description'])
        
        # Add attributes
        attrs_list = type_def.get('attributes', [])
        for attr_def in attrs_list:
            attrs = attr_def.get('attributes', {})
            attr = ET.SubElement(complex_type, 'xs:attribute')
            attr.set('name', attrs.get('name', 'attribute'))
            attr.set('type', attrs.get('type', 'xs:string'))
            
            if attrs.get('use'):
                attr.set('use', attrs['use'])
            
            # Add documentation
            if 'description' in attr_def:
                annotation = ET.SubElement(attr, 'xs:annotation')
                add_documentation_with_html(annotation, attr_def['description'])
    
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
    
    # Define paths
    yaml_file = repo_root / 'data' / 'animNode.yaml'
    xsd_file = repo_root / 'schemas' / 'animNode.xsd'
    
    # Generate the schema
    create_xsd_from_yaml(str(yaml_file), str(xsd_file))

