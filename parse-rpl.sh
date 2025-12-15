#!/bin/bash

# Check if input file is provided
if [ -z "$1" ]; then
    echo "Usage: ./parse_rpl.sh <logfile>"
    exit 1
fi

# Header row

printf "Timestamp, Node, DAG, Parent, Rank, Metric, Cost"

# grep -n "Pref Y" "$1" | grep fd00 |
grep -n "Node:5" "$1" | grep fd00 |

# You can pipe your grep directly into this script:
# grep "RPL: DAG:" logfile.txt | ./parse_dag.sh

awk '
{
    # --- 1. TIMESTAMP ---
    # Split 70984:00:18:16.081 by ":"
    split($1, t, ":");
    timestamp = t[2] ":" t[3] ":" t[4];

    # --- 2. REPORTING NODE ---
    # Format: Node:5
    split($2, n, ":");
    node_id = n[2];

    # --- 3. DYNAMIC FIELD EXTRACTION ---
    # We define defaults just in case a field is missing
    dag="?"; parent="?"; rank="?"; lnkm="?"; pathcost="?";

    # Loop through all fields in the line to find key identifiers
    for (i=1; i<=NF; i++) {

        if ($i == "DAG:") {
            dag = $(i+1);
        }
        else if ($i == "Parent:") {
            parent = $(i+1);
            # Optional: Remove leading zeros (e.g., "07" becomes "7")
            # sub(/^0+/, "", parent);
        }
        else if ($i == "Rank:") {
            rank = $(i+1);
            gsub(",", "", rank); # Remove the comma
        }
        else if ($i == "LnkM:") {
            lnkm = $(i+1);
            gsub(",", "", lnkm); # Remove the comma
        }
        else if ($i == "PathCost:") {
            pathcost = $(i+1);
        }
    }

    # --- 4. OUTPUT LOGIC ---

    # Insert linebreak if the Reporting Node changes
    if (NR > 1 && node_id != prev_node) {
        print "";
    }
    prev_node = node_id;

    # Header-style output: Timestamp, Node, DAG, Parent, Rank, Metric, Cost
    printf "%s, %s, %s, %s, %s, %s, %s\n", timestamp, node_id, dag, parent, rank, lnkm, pathcost;

}'
# "${1:-/dev/stdin}" here would allow it to read from a file arg OR from a pipe
