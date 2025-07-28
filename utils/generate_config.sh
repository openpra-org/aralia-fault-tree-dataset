#!/bin/bash

# A script to generate configuration files from a template
# by creating a cartesian product of models and scripts.

# --- Functions ---
usage() {
  echo "Usage: $0 <template_file> <models_list_file> <scripts_list_file>"
  echo ""
  echo "Arguments:"
  echo "  template_file        Path to the template file."
  echo "  models_list_file     Path to a file containing a list of model file paths."
  echo "  scripts_list_file    Path to a file containing a list of script file paths."
  echo ""
  echo "Path Structure Requirements:"
  echo "  - Model paths must end in '<MODEL_ID>.xml'."
  echo "    Example: /path/to/my_model_name.xml -> ID: 'my_model_name'"
  echo "  - Script paths must follow the format '<SCRIPT_ID>.xfta2'."
  echo "    Example: /path/to/some_script.xfta2 -> ID: 'some_script'"
  echo ""
  echo "Options:"
  echo "  -h, --help           Display this help message and exit."
  exit 1
}

# --- Argument Parsing ---
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
fi

if [ "$#" -ne 3 ]; then
  echo "Error: Incorrect number of arguments."
  usage
fi

TEMPLATE_FILE="$1"
MODELS_LIST_FILE="$2"
SCRIPTS_LIST_FILE="$3"

# --- Input Validation ---
for file in "$TEMPLATE_FILE" "$MODELS_LIST_FILE" "$SCRIPTS_LIST_FILE"; do
  if ! [ -f "$file" ]; then
    echo "Error: Input file not found at '$file'"
    exit 1
  fi
done

# --- Main Logic ---
while IFS= read -r model_path; do
  while IFS= read -r script_path; do
    # Extract IDs from file paths
    model_filename=$(basename "$model_path")
    model_id=${model_filename%.xml}

    script_filename=$(basename "$script_path")
    script_id=${script_filename%.xfta2}

    # Generate the output filename
    output_filename="${model_id}.${script_id}.xfta2"
    echo "Generating ==> ${output_filename}"

    # Use sed to substitute placeholders. Using '#' as the delimiter avoids issues with '/' in paths.
    sed -e "s#<MODEL>#${model_path}#" \
        -e "s#<SCRIPT>#${script_path}#" \
        "${TEMPLATE_FILE}" > "${output_filename}"

  done < "$SCRIPTS_LIST_FILE"
done < "$MODELS_LIST_FILE"

echo "Done."
