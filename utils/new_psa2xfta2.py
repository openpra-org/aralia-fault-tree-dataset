#!/usr/bin/env python3
import argparse
import sys
import xml.etree.ElementTree as ET
import copy

def transform_openpsa_to_xfta2(input_path, output_path):
    """
    Transforms an OpenPSA XML file to an XFTA2 XML file based on a set of rules.

    Args:
        input_path (str): The file path for the input OpenPSA XML.
        output_path (str): The file path for the output XFTA2 XML.
    """
    try:
        # We parse the XML file into an ElementTree object.
        original_tree = ET.parse(input_path)
        original_root = original_tree.getroot()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{input_path}'", file=sys.stderr)
        sys.exit(1)
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML file '{input_path}'.\n{e}", file=sys.stderr)
        sys.exit(1)

    # --- 1. Extract existing basic event definitions from the original model-data ---
    defined_basic_events = {}
    original_model_data = original_root.find('model-data')
    if original_model_data is not None:
        for event in original_model_data.findall('define-basic-event'):
            name = event.get('name')
            if name:
                defined_basic_events[name] = event

    # --- 2. Extract fault tree definitions ---
    fault_trees = original_root.findall('define-fault-tree')
    if not fault_trees:
        print("Error: No <define-fault-tree> element found in the input file.", file=sys.stderr)
        sys.exit(1)

    if len(fault_trees) > 1:
        print("Warning: Multiple <define-fault-tree> elements found. "
              "Only the first one will be processed to generate the output file.", file=sys.stderr)

    source_fault_tree = fault_trees[0]

    # --- 3. Build the new XFTA2 XML structure ---
    new_root = ET.Element('opsa-mef')
    used_basic_events = set()

    # Transfer all elements from inside <define-fault-tree> to the new root
    for element in source_fault_tree:
        new_root.append(element)
        # While transferring, find all used basic-events to build the new model-data
        for basic_event in element.findall('.//basic-event'):
            used_basic_events.add(basic_event.get('name'))

    # --- 4. Adjust 'define-CCF-group' elements in the new structure ---
    for ccf_group in new_root.findall('.//define-CCF-group'):
        members = ccf_group.find('members')
        factors = ccf_group.find('factors')
        distribution = ccf_group.find('distribution')
        
        children_to_reorder = {}
        if members is not None:
            children_to_reorder['members'] = members
        
        if factors is not None:
            new_factors = ET.Element('factors')
            for factor in factors.findall('factor'):
                for child in factor:
                    new_factors.append(child)
            children_to_reorder['factors'] = new_factors

        if distribution is not None:
            dist_child = next(iter(distribution), None)
            if dist_child is not None:
                 children_to_reorder['distribution_child'] = dist_child

        for child in list(ccf_group):
            ccf_group.remove(child)

        if 'members' in children_to_reorder:
            ccf_group.append(children_to_reorder['members'])
        if 'factors' in children_to_reorder:
            ccf_group.append(children_to_reorder['factors'])
        if 'distribution_child' in children_to_reorder:
             ccf_group.append(children_to_reorder['distribution_child'])

    # --- 5. Transform XOR gates ---
    # We find all gates with an <xor> child first, then iterate over the collected list
    # to safely modify the XML tree.
    gates_to_transform = []
    for define_gate in new_root.findall('.//define-gate'):
        xor_element = define_gate.find('xor')
        if xor_element is not None:
            gates_to_transform.append((define_gate, xor_element))

    for define_gate, xor_element in gates_to_transform:
        children = list(xor_element)
        # This transformation is only defined for 2-input XOR gates.
        if len(children) != 2:
            print(f"Warning: Found <xor> gate in '{define_gate.get('name')}' with {len(children)} children. "
                  "The XOR -> AND/OR/NAND transformation only supports 2 inputs. Skipping this gate.", file=sys.stderr)
            continue
        
        print(f"Info: Transforming 2-input XOR gate in '{define_gate.get('name')}'.", file=sys.stderr)
        
        # Create the new <and> element that will replace the <xor>
        # A XOR B  =>  (A OR B) AND (A NAND B)
        new_and_gate = ET.Element('and')
        
        # Create the <or> sub-gate and populate it with deep copies of the children
        or_sub_gate = ET.SubElement(new_and_gate, 'or')
        or_sub_gate.append(copy.deepcopy(children[0]))
        or_sub_gate.append(copy.deepcopy(children[1]))
        
        # Create the <nand> sub-gate and populate it with deep copies of the children
        nand_sub_gate = ET.SubElement(new_and_gate, 'nand')
        nand_sub_gate.append(copy.deepcopy(children[0]))
        nand_sub_gate.append(copy.deepcopy(children[1]))
        
        # Replace the original <xor> element with the new <and> gate structure
        define_gate.remove(xor_element)
        define_gate.append(new_and_gate)

    # --- 6. Create and populate the new 'model-data' element ---
    new_model_data = ET.SubElement(new_root, 'model-data')
    for event_name in sorted(list(used_basic_events)): # Sort for consistent output
        if event_name in defined_basic_events:
            new_model_data.append(defined_basic_events[event_name])
        else:
            # If a basic event is used but not defined, create a default definition.
            print(f"Info: Basic event '{event_name}' was not defined in the original "
                  f"<model-data>. A default definition will be created.", file=sys.stderr)
            new_event = ET.SubElement(new_model_data, 'define-basic-event', {'name': event_name})
            ET.SubElement(new_event, 'float', {'value': '0.5'})

    # --- 7. Write the transformed XML to the output file ---
    # Use ET.indent for pretty-printing (available in Python 3.9+)
    try:
        ET.indent(new_root, space="    ", level=0)
    except AttributeError:
        # Fallback for older Python versions
        print("Warning: 'xml.etree.ElementTree.indent' not available (requires Python 3.9+). "
              "Output will not be pretty-printed.", file=sys.stderr)

    final_tree = ET.ElementTree(new_root)
    try:
        final_tree.write(output_path, encoding='unicode', xml_declaration=True)
        print(f"Successfully transformed '{input_path}' to '{output_path}'")
    except IOError as e:
        print(f"Error: Could not write to output file '{output_path}'.\n{e}", file=sys.stderr)
        sys.exit(1)


def main():
    """
    Main function to parse command-line arguments and run the transformation.
    """
    parser = argparse.ArgumentParser(
        description='Converts an OpenPSA XML file to an XFTA2 XML file.',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        'input_file',
        type=str,
        help='The path to the input OpenPSA XML file.'
    )
    parser.add_argument(
        'output_file',
        type=str,
        help='The path to the destination XFTA2 XML file.'
    )
    args = parser.parse_args()

    transform_openpsa_to_xfta2(args.input_file, args.output_file)


if __name__ == '__main__':
    main()
