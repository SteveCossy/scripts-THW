#!/bin/bash

# Compare files from development tree with original version
# 20 October 2024
# Modified 22 October to accept a parameter

# Define your base directories
DEVELOPED_DIR="/home/stevecos/contiki-ng"
ORIGINAL_DIR="/local/scratch/stevecos/ben/contiki-ng"

echo "Comparing files between:"
echo "Developed: $DEVELOPED_DIR"
echo "Original:  $ORIGINAL_DIR"

# Function to perform the kdiff3 comparison
compare_and_diff() {
    echo "Command On Diff: $COMMAND_ON_DIFF"
    echo "------------------------------------------------------------------"
    local original_file="$1"
    local developed_file="$2"
    local relative_path="$3"

    if [ -f "$original_file" ]; then
        echo -n "--- Diffing: $relative_path --- "
        if diff -q "$original_file" "$developed_file" >/dev/null; then
           echo "same"
        else
           echo "Showing differences in kdiff3"

        fi
    else
        echo "--- WARNING: Original file not found for $relative_path (might be new) ---"
        echo "Developed file: $developed_file"
        echo "------------------------------------------------------------------"
    fi
}

# Check if a filename parameter is supplied
if [ -n "$1" ]; then
    # A parameter was supplied, assume it's a relative filename
    PARAM_RELATIVE_PATH="$1"
    PARAM_DEVELOPED_FILE="$DEVELOPED_DIR/$PARAM_RELATIVE_PATH"
    PARAM_ORIGINAL_FILE="$ORIGINAL_DIR/$PARAM_RELATIVE_PATH"
    COMMAND_ON_DIFF="$PARAM_DEVELOPED_FILE $PARAM_ORIGINAL_FILE > /dev/null 2>&1 &"

    echo "Parameter supplied: '$PARAM_RELATIVE_PATH'. Attempting direct comparison."

    if [ -f "$PARAM_DEVELOPED_FILE" ] && [ -f "$PARAM_ORIGINAL_FILE" ]; then
        echo "Both files exist. Performing direct comparison."
        COMMAND_ON_DIFF="kdiff3 $COMMAND_ON_DIFF"
        compare_and_diff "$PARAM_ORIGINAL_FILE" "$PARAM_DEVELOPED_FILE" "$PARAM_RELATIVE_PATH"
        echo "Comparison complete."
    else
        echo "ERROR: One or both specified files do not exist."
        echo "Developed: $PARAM_DEVELOPED_FILE (Exists: $([ -f "$PARAM_DEVELOPED_FILE" ] && echo "yes" || echo "no"))"
        echo "Original:  $PARAM_ORIGINAL_FILE (Exists: $([ -f "$PARAM_ORIGINAL_FILE" ] && echo "yes" || echo "no"))"
        echo "Note that the path supplied by be relative from: $DEVELOPED_DIR"
        echo "Exiting."
        exit 1
    fi
else
    # No parameter supplied, proceed with the original logic (find files with 'hton')
    echo No parameter supplied.
    echo "See source $0 to enable logic to search for files containing specific text (such as 'hton')"
    echo "before diffing each matching file (excluding 'rpl-lite')."
    for i in {1..4} ; do echo ; done
    echo "------------------------------------------------------------------"
    echo
    echo "Usage:"
    echo "  $0 <relative file path and name>"
    echo "Base folders:"
    echo "  Original code:            $ORIGINAL_DIR"
    echo "  Modified code to compare: $DEVELOPED_DIR"
    echo "Remember that right-clicking on a file tab in vsCode enables you to 'Copy Realative Path' which works in this script."
    echo
    echo "Continue with full list of changed files? (y/N)"
    read
    if [[ "$REPLY" == "y" ]]; then
            # Find files in your developed codebase
        COMMAND_ON_DIFF="echo $COMMAND_ON_DIFF"
       find "$DEVELOPED_DIR" -type f -exec grep -lE "hton" {} + | grep -v "rpl-lite" | while read -r DEVELOPED_FILE; do
            # Get the relative path from the developed directory
            RELATIVE_PATH="${DEVELOPED_FILE#$DEVELOPED_DIR/}"

            # Construct the path to the original file
            ORIGINAL_FILE="$ORIGINAL_DIR/$RELATIVE_PATH"

            compare_and_diff "$ORIGINAL_FILE" "$DEVELOPED_FILE" "$RELATIVE_PATH"
       done
    fi
fi

echo "------------------------------------------------------------------"
