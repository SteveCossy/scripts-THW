#!/bin/bash

# ==============================================================================
# process_rpl_log.sh
#
# Processes a specific RPL log file to generate analysis and PDF
#   reports in timeline format.
#
# Usage:
#   ./process_timeline.sh <path/to/logfile.txt>
#
# 26 November 2025
#
# ==============================================================================

# --- Script Configuration ---
# Stop the script if any command fails
set -e
# Ensure that a pipeline command fails if any of its components fail
set -o pipefail

# --- Path Variables (Easier to change later) ---
          BASE_DIR="$HOME"
       WORKING_DIR="$BASE_DIR/data/timeline"
     PYTHON_SCRIPT="$BASE_DIR/Documents/scripts/process_timeline.sh"
PYTHON_SCRIPT_LOGS="$BASE_DIR/Documents/scripts/process_timeline.log"
#     GRAPH_TEX_FILE="$BASE_DIR/data/rpl_graph.tex"
#     TABLE_TEX_FILE="$BASE_DIR/data/rpl_table.tex"
  OUTPUT_FILE_PATH="$BASE_DIR/data/timeline"
#        CONFIG_FILE="$BASE_DIR/contiki-ng/os/net/routing/rpl-classic/rpl-conf.h"
#         CONFIG_END=" head -59 "
#         CONFIG_NBR=" tail -8 "
      SUMMARY_FILE="$BASE_DIR/data/timeline/RPL_timeline"
  SUMMARY_FILE_TEX="$SUMMARY_FILE.tex"


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
    $SUMMARY_FILE_PDF="$SUMMARY_FILE-$SUFFIX.pdf"
else
    echo "Error: Filename '$FILE' does not contain a valid YYYYMMDDHHMMSS timestamp."
    echo "       Expected format example: '...-20250702210825.txt'"
    exit 1
fi

# --- Define Output Filenames ---
#     TREE_FILE="${OUTPUT_FILE_PATH}text_${SUFFIX}.txt"
#   ROUTES_FILE="${OUTPUT_FILE_PATH}routes_${SUFFIX}.txt"
# GRAPH_PDF_OUT="${OUTPUT_FILE_PATH}graph_${SUFFIX}.pdf"
# TABLE_PDF_OUT="${OUTPUT_FILE_PATH}table_${SUFFIX}.pdf"

# --- Create temp OF file ---
# pdftotext /home/stevecos/data/table_${SUFFIX}.pdf /tmp/table.txt
# grep DAG /tmp/table.txt > /tmp/OFs.txt

# --- Main Processing Steps ---
echo "--> Step 1: Generating tex file $SUMMARY_FILE_TEX"
cd $WORKING_DIR
PYTHONIOENCODING=UTF-8 python3 "$PYTHON_SCRIPT" "$FILE"

echo "--> Step 2: Compiling LaTeX files to PDF"
# The latexmk commands generate `rpl_graph.pdf` and `rpl_table.pdf` in the current directory.
latexmk -lualatex "$SUMMARY_FILE_TEX"

echo "--> Step 3: Copying and renaming generated PDF to $SUMMARY_FILE_PDF"
# Copy the freshly made PDFs to new names using the extracted suffix.
# Note: I removed the redundant `cp rpl_*.pdf ...` as the next two lines are more specific and safer.
cp "$SUMMARY_FILE.pdf" "$SUMMARY_FILE_PDF"

echo "--> Step 5: Opening PDF for review"
okular "$SUMMARY_FILE_PDF" > /dev/null 2>&1 &

echo ""
echo "--> Script finished successfully!"
