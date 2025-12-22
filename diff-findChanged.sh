#!/bin/bash

# Compare files from development tree with original version
# 20 October 2024
# Modified 22 October to accept a parameter
# Modified 23 October to walk tree and log diff commands
# Find all changed files added 22 December 2025

# Define your base directories
DEVELOPED_DIR="/home/stevecos/contiki-ng"
ORIGINAL_DIR="/local/scratch/stevecos/ben/contiki-ng"
# Where to put the file holding kdiff3 commands
TEMPFILE="/tmp/SteveCosDiffs.sh"

echo "Comparing files between:"
echo "Developed: $DEVELOPED_DIR"
echo "Original:  $ORIGINAL_DIR"

# Function to perform the comparison
# Returns 0 if same, 1 if different, 2 if original missing
compare_and_diff() {
    local original_file="$1"
    local developed_file="$2"
    local relative_path="$3"

    if [ -f "$original_file" ]; then
        if diff -q "$original_file" "$developed_file" >/dev/null; then
           echo "OK: $relative_path (No changes)"
           return 0
        else
           echo "CHANGED: $relative_path (Added to $TEMPFILE)"
           return 1
        fi
    else
        echo "NEW: $relative_path (Original not found)"
        return 2
    fi
}

# Check if a filename parameter is supplied
if [ -n "$1" ]; then
    # A parameter was supplied, assume it's a relative filename
    PARAM_RELATIVE_PATH="$1"
    PARAM_DEVELOPED_FILE="$DEVELOPED_DIR/$PARAM_RELATIVE_PATH"
    PARAM_ORIGINAL_FILE="$ORIGINAL_DIR/$PARAM_RELATIVE_PATH"

    echo "Parameter supplied: '$PARAM_RELATIVE_PATH'. Attempting direct comparison."

    if [ -f "$PARAM_DEVELOPED_FILE" ]; then
        compare_and_diff "$PARAM_ORIGINAL_FILE" "$PARAM_DEVELOPED_FILE" "$PARAM_RELATIVE_PATH"
        RET=$?
        if [ $RET -eq 1 ]; then
            echo "kdiff3 $PARAM_ORIGINAL_FILE $PARAM_DEVELOPED_FILE &"
            kdiff3 "$PARAM_ORIGINAL_FILE" "$PARAM_DEVELOPED_FILE" > /dev/null 2>&1 &
        fi
    else
        echo "ERROR: Developed file $PARAM_DEVELOPED_FILE does not exist."
        exit 1
    fi
else
    # No parameter supplied, proceed with walking the directory
    echo "------------------------------------------------------------------"
    echo "Preparing to scan $DEVELOPED_DIR"
    echo "Excluding 'rpl-lite' and '.git' directories."
    echo "Press Enter to continue or Ctrl+C to abort..."
    read
    # Initialize/Clear the temp file and make it executable
    echo "#!/bin/bash" > "$TEMPFILE"
    chmod +x "$TEMPFILE"

    # Walk the folder structure
    # 1. find all files
    # 2. exclude .git and rpl-lite
    # 3. exclude build artifacts (.o, .d, .a)
    find "$DEVELOPED_DIR" -type f \
        -not -path '*/.*' \
        -not -path '*rpl-lite*' \
        -not -name "*.o" \
        -not -name "*.d" \
        -not -name "*.a" | while read -r DEVELOPED_FILE; do

        # Get the relative path from the developed directory
        RELATIVE_PATH="${DEVELOPED_FILE#$DEVELOPED_DIR/}"

        # Construct the path to the original file
        ORIGINAL_FILE="$ORIGINAL_DIR/$RELATIVE_PATH"

        # Check for differences
        compare_and_diff "$ORIGINAL_FILE" "$DEVELOPED_FILE" "$RELATIVE_PATH"
        RESULT=$?

        # If files are different (Status 1), write kdiff3 command to file
        if [ $RESULT -eq 1 ]; then
            MOD_DATE=$(date -r "$DEVELOPED_FILE" "+%Y-%m-%d")
            echo "kdiff3 \"$ORIGINAL_FILE\" \"$DEVELOPED_FILE\" & # Last mod: $MOD_DATE" >> "$TEMPFILE"
        fi
    done

    echo "------------------------------------------------------------------"
    echo "Scan Complete."
    COUNT=$(grep -c "kdiff3" "$TEMPFILE")
    echo "Found $COUNT changed files."
    echo "To review changes, run: $TEMPFILE"
    echo "To view file list in date order, run: sort -k 7 -r $TEMPFILE"
fi

echo "------------------------------------------------------------------"
