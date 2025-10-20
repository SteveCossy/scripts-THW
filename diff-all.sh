#!/bin/bash

# Compare files from development tree with original version
# 20 October 2024

# Define your base directories
DEVELOPED_DIR="/home/stevecos/contiki-ng"
ORIGINAL_DIR="/local/scratch/stevecos/ben/contiki-ng"

echo "Comparing files containing 'hton' (excluding 'rpl-lite') between:"
echo "Developed: $DEVELOPED_DIR"
echo "Original:  $ORIGINAL_DIR"
echo "------------------------------------------------------------------"

# Find files in your developed codebase
find "$DEVELOPED_DIR" -type f -exec grep -lE "hton" {} + | grep -v "rpl-lite" | while read -r DEVELOPED_FILE; do
    # Get the relative path from the developed directory
    RELATIVE_PATH="${DEVELOPED_FILE#$DEVELOPED_DIR/}"

    # Construct the path to the original file
    ORIGINAL_FILE="$ORIGINAL_DIR/$RELATIVE_PATH"

    # Check if the original file exists before trying to diff
    if [ -f "$ORIGINAL_FILE" ]; then
        echo "--- Diffing: $RELATIVE_PATH ---"
        diff -u "$ORIGINAL_FILE" "$DEVELOPED_FILE"
        echo "" # Add a newline for better readability between diffs
    else
        echo "--- WARNING: Original file not found for $RELATIVE_PATH (might be new) ---"
        echo "Developed file: $DEVELOPED_FILE"
        echo "------------------------------------------------------------------"
    fi
done

echo "------------------------------------------------------------------"
echo "Comparison complete."
