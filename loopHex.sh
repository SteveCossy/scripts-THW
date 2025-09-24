#!/bin/bash

# A script to loop through a range of numbers in hex, executing a
# command for each iteration and substituting a keyword.
# commissioned by Steve Cosgrove 25/09/2025

# --- Input Validation ---
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <start_dec> <end_dec> <command_with_keyword...>"
  echo "Example: $0 1 24 echo Processing node āe"
  echo "  The keyword 'āe' will be replaced with the hex loop variable."
  exit 1
fi

# --- Get Loop Limits and the Command ---
START_DEC=$1
END_DEC=$2
shift 2 # Removes the first two arguments, leaving only the command.
COMMAND=("$@") # Store the remaining arguments (the command) in an array.

KEYWORD="āe" # Define our special keyword.

echo "--- Running command for hex range ${START_DEC}-${END_DEC} ---"

# --- The Main Loop ---
for (( i=$START_DEC; i<=$END_DEC; i++ )); do
  
  # Convert the current loop number to hex
  hex_var=$(printf "%x" "$i")
  
  # Create a temporary copy of the command array for this iteration
  iter_command=("${COMMAND[@]}")
  
  # --- The Substitution Magic ---
  # Iterate through the command array and replace the keyword
  for j in "${!iter_command[@]}"; do
    iter_command[$j]="${iter_command[$j]//${KEYWORD}/${hex_var}}"
  done
  
  # --- Execute the Modified Command ---
  # The "${iter_command[@]}" syntax correctly handles spaces in arguments.
  "${iter_command[@]}"
  
done

echo "--- Loop finished ---"

