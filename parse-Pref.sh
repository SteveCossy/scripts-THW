#!/bin/bash

# Check if input file is provided
if [ -z "$1" ]; then
    echo "Usage: ./parse_rpl.sh <logfile>"
    exit 1
fi

printf "timestamp, tx_node, rx_node, instance, rank\n";

#grep "Incoming DIO (id" "$1" | awk '
grep "Incoming DIO (id" "$1" | grep -E "(5,|3,|1,)  | awk '

{
    # --- 1. TIMESTAMP ---
    # Input format: 39851:00:07:34.307
    # We split by ":" to remove the simulation tick count (39851)
    # and keep the time (00:07:34.307).
    split($1, t, ":");
    timestamp = t[2] ":" t[3] ":" t[4];

    # --- 2. RECEIVING NODE ---
    # Input format: Node:6
    split($2, n, ":");
    rx_node = n[2];

    # --- 3. DIO DATA (Instance, Rank) ---
    # The format is always: ... (id, ver, rank) = (30,240,434) ...
    # This is the second to last field ($NF-1)
    dio_str = $(NF-1);

    # Remove parentheses
    gsub(/[()]/, "", dio_str);

    # Split by comma to get values
    split(dio_str, d, ",");
    instance = d[1];
    # version = d[2]; # We ignore version as requested
    rank = d[3];

    # --- 4. SOURCE NODE ---
    # Input format: from:fe80::201:1:1:1
    # This is the last field ($NF)
    ip_field = $NF;

    # Remove "from:" prefix
    sub("from:", "", ip_field);

    # Extract the last segment of the IPv6 address to get the Node ID
    # (e.g., fe80::201:1:1:1 -> 1)
    num_parts = split(ip_field, ip_parts, ":");
    tx_node = ip_parts[num_parts];

    # --- 5. LOGIC & OUTPUT ---

    # If source changes (and it is not the very first line), print an empty line
    if (NR > 1 && tx_node != prev_tx_node) {
        print "";
    }

    # Update previous source tracker
    prev_tx_node = tx_node;

    # Print formatted output
    # Format: Timestamp, Source, Receiver, Instance, Rank
    printf "%s, t->%s, r->%s, %s, %s\n", timestamp, tx_node, rx_node, instance, rank;

}'
