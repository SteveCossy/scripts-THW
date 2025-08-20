#!/bin/bash

# ==============================================================================
# process_rpl_log.sh
#
# Processes a specific RPL log file to generate analysis and PDF reports.
#
# Usage:
#   ./process_rpl_log.sh <path/to/logfile.txt>
#
# Example:
#   ./process_rpl_log.sh 10-RPL-20250702210825.txt
#
# ==============================================================================

# --- Script Configuration ---
# Stop the script if any command fails
set -e
# Ensure that a pipeline command fails if any of its components fail
set -o pipefail

# --- Path Variables (Easier to change later) ---
          BASE_DIR="$HOME"
     PYTHON_SCRIPT="$BASE_DIR/Documents/references/parse_rpl_log_fixed.py"
PYTHON_SCRIPT_LOGS="$BASE_DIR/Documents/references/parse_rpl_log_routes.py"
    GRAPH_TEX_FILE="$BASE_DIR/data/rpl_graph.tex"
    TABLE_TEX_FILE="$BASE_DIR/data/rpl_table.tex"
  OUTPUT_FILE_PATH="$BASE_DIR/data/"
       CONFIG_FILE="$BASE_DIR/contiki-ng/os/net/routing/rpl-classic/rpl-conf.h"
        CONFIG_END=" head -59 "
        CONFIG_NBR=" tail -8 "
      SUMMARY_FILE="$BASE_DIR/data/SimSummary.pdf"


# --- Input Validation ---
# Check if a file argument was provided
if [ "$#" -ne 1 ]; then
    echo "Error: Incorrect number of arguments."
    echo "Usage: $0 <filename>"
    exit 1
fi

FILE="$1"

# Check if the provided file actually exists
if [ ! -f "$FILE" ]; then
    echo "Error: File not found: '$FILE'"
    exit 1
fi

# --- Date Extraction ---
echo "--> Processing file: $FILE"

# Use a regular expression to find a 14-digit timestamp (YYYYMMDDHHMMSS)
if [[ "$FILE" =~ ([0-9]{14}) ]]; then
    SUFFIX="${BASH_REMATCH[1]}"
    echo "--> Extracted date suffix: $SUFFIX"
else
    echo "Error: Filename '$FILE' does not contain a valid YYYYMMDDHHMMSS timestamp."
    echo "       Expected format example: '...-20250702210825.txt'"
    exit 1
fi

# --- Define Output Filenames ---
    TREE_FILE="${OUTPUT_FILE_PATH}text_${SUFFIX}.txt"
  ROUTES_FILE="${OUTPUT_FILE_PATH}routes_${SUFFIX}.txt"
GRAPH_PDF_OUT="${OUTPUT_FILE_PATH}graph_${SUFFIX}.pdf"
TABLE_PDF_OUT="${OUTPUT_FILE_PATH}table_${SUFFIX}.pdf"

# --- Create temp OF file ---
# pdftotext /home/stevecos/data/table_${SUFFIX}.pdf /tmp/table.txt
# grep DAG /tmp/table.txt > /tmp/OFs.txt

# --- Main Processing Steps ---
echo "--> Step 1: Generating tree file: $TREE_FILE"
# Run head and ls, redirecting output to the tree file.
# The file is created/truncated by the first command (>), and appended to by the second (>>).
head -1 "$FILE" > "$TREE_FILE"
echo -n "    Run finished at " >> "$TREE_FILE"
ls -l "$FILE" | awk '{print $7, $6, $8}' >> "$TREE_FILE"
echo -n "Routing at " >> "$TREE_FILE"
ls -l /home/stevecos/contiki-ng/os/net/routing/rpl-classic/rpl-conf.h | awk '{print $7, $6, $8}' >> "$TREE_FILE"
cat -n $CONFIG_FILE | $CONFIG_END | $CONFIG_NBR >> "$TREE_FILE"
# echo -n "Objective Functions: " >> "$TREE_FILE"
# paste -s -d ' '  /tmp/OFs.txt >> "$TREE_FILE"
echo -n "Edit options: nano +53 /home/stevecos/contiki-ng/os/net/routing/rpl-classic/rpl-conf.h" >> "$TREE_FILE"

echo "--> Step 2a: Running Python parser and appending to text tree file"
# Run the Python script, ensuring its output is appended to the same tree file.
# PYTHONIOENCODING=UTF-8 is good practice if your log has special characters.
PYTHONIOENCODING=UTF-8 python3 "$PYTHON_SCRIPT" "$FILE" >> "$TREE_FILE"
echo "--> Step 2b: Running Python IPv6 parser and appending to route file"
python3 "$PYTHON_SCRIPT_LOGS" "$FILE" >> "$ROUTES_FILE"

echo "--> Step 3: Compiling LaTeX files to PDF"
# The latexmk commands generate `rpl_graph.pdf` and `rpl_table.pdf` in the current directory.
latexmk -lualatex "$GRAPH_TEX_FILE"
latexmk -pdflatex "$TABLE_TEX_FILE"

echo "--> Step 4: Copying and renaming generated PDFs"
# Copy the freshly made PDFs to new names using the extracted suffix.
# Note: I removed the redundant `cp rpl_*.pdf ...` as the next two lines are more specific and safer.
cp rpl_graph.pdf "$GRAPH_PDF_OUT"
cp rpl_table.pdf "$TABLE_PDF_OUT"
echo "    - Created $GRAPH_PDF_OUT"
echo "    - Created $TABLE_PDF_OUT"

# echo "--> Step 5: Opening PDFs for review"
# Use okcular (or another PDF viewer) to open the final, timestamped files.
# nohup 
# okular "$GRAPH_PDF_OUT" "$TABLE_PDF_OUT" "$TREE_FILE" "$ROUTES_FILE" > /dev/null 2>&1 &
echo "--> Step 5: Adding the latest run to the summary file and opening that file
/home/stevecos/scripts/summarize_run.py $TREE_FILE
okular "$SUMMARY_FILE"

echo ""
echo "--> Script finished successfully!"
