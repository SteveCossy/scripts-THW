#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <filename> <block_size> <grep_pattern>"
    echo "Example: $0 my_log.log 20000 'ERROR|WARNING'"
    exit 1
fi

filename="$1"
block_size="$2"
grep_pattern="$3"
start_time=`date +%x-%X`
temp_dir="/local/scratch/stevecos/"
temp_file=".current_block_temp.log"
temp_fullpath=$temp_dir$temp_file

# Validate block_size is a positive integer
if ! [[ "$block_size" =~ ^[0-9]+$ ]] || [ "$block_size" -eq 0 ]; then
    echo "Error: Block size must be a positive integer."
    exit 1
fi

# Validate file exists
if [ ! -f "$filename" ]; then
    echo "Error: File '$filename' not found."
    exit 1
fi

current_line=0
total_matches=0
block_number=0

echo "At $start_time, starting analysis of '$filename' with block size '$block_size' and pattern '$grep_pattern'..."
echo "---------------------------------------------------------------------------------------------------------"

# Loop through the file in blocks
while IFS= read -r line; do
    ((current_line++))
    echo "$line" >> $temp_fullpath # Write line to a temporary file for the current block

    if [ "$((current_line % block_size))" -eq 0 ]; then
        ((block_number++))
        # Use grep -c to count matches in the temporary block file
        block_matches=$(grep -c "$grep_pattern" $temp_fullpath)
        total_matches=$((total_matches + block_matches))

        echo "At `date +%X`, Block $((block_number * block_size / block_size)) (lines $(( (block_number - 1) * block_size + 1 )) - $((block_number * block_size))): Matches = $block_matches, Running Total = $total_matches"
        rm $temp_fullpath # Clear the temporary file for the next block
    fi
done < "$filename"

# Handle any remaining lines in the last block
if [ -f $temp_fullpath ]; then
    ((block_number++))
    block_matches=$(grep -c "$grep_pattern" $temp_fullpath)
    total_matches=$((total_matches + block_matches))
    start_line=$(( (block_number - 1) * block_size + 1 ))
    end_line=$current_line
    echo "Block $block_number (lines $start_line - $end_line): Matches = $block_matches, Running Total = $total_matches (Partial Block)"
    rm $temp_fullpath
fi

echo "--------------------------------------------------------------------------------"
echo "Analysis complete. Final total matches: $total_matches"

exit 0