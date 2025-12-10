#!/usr/bin/env python3
import sys
import re
import argparse
import math
from pathlib import Path

# --- Configuration ---
OUTPUT_FILENAME = "DIO_graph.tex" # Fixed output name
TARGET_INSTANCE = "30"
TARGET_DAG_PREFIX = "fd00"

# --- Visualization Settings ---
Y_SCALE_CM = 0.6         # How many cm per second (vertical)
PAGE_HEIGHT_CM = 22.0    # Max height of drawing area per page
MIN_LABEL_DIST_CM = 0.5  # Don't print timestamps closer than this

# TikZ Colors to cycle through for arrows
COLORS = ["red", "blue", "orange", "teal", "violet", "cyan!70!black", "magenta"]

def parse_time(timestr):
    """Converts 'HH:MM:SS.ms' to total seconds (float)."""
    h, m, s = timestr.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def extract_node_id(ipv6_str):
    """Extracts node ID from IPv6 string."""
    clean_ip = ipv6_str.replace("from:", "").strip()
    parts = clean_ip.split(':')
    try:
        return int(parts[-1], 16)
    except ValueError:
        return 0

def parse_log_file(filepath):
    """Parses log file for DIOs and Parent changes."""
    dio_events = []
    parent_events = []
    nodes = set()

    # Regex 1: Time and Node (Updated per your request)
    # Matches: 00:07:34.307 Node:6 ...
    re_base = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d+)\s+Node:(\d+)\s+:(.*)")

    # Regex 2: Incoming DIO
    re_dio = re.compile(r"Incoming DIO \(id, ver, rank\) = \((\d+),.*\) (from:[\w:]+)")

    # Regex 3: DAG Info
    re_dag_chk = re.compile(r"RPL: DAG:\s*([0-9a-fA-F]+)")

    start_time_abs = None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            base_match = re_base.match(line)
            if not base_match:
                continue

            time_str, node_str, message = base_match.groups()
            current_time = parse_time(time_str)
            rx_node = int(node_str)
            nodes.add(rx_node)

            if start_time_abs is None:
                start_time_abs = current_time

            # Relative time from start of log
            rel_time = current_time - start_time_abs

            # --- DIO Events ---
            if "Incoming DIO" in message:
                dio_match = re_dio.search(message)
                if dio_match:
                    instance_id, from_ip = dio_match.groups()
                    if instance_id == TARGET_INSTANCE:
                        tx_node = extract_node_id(from_ip)
                        nodes.add(tx_node)
                        dio_events.append({
                            'time': rel_time,
                            'timestamp_str': time_str,
                            'rx_node': rx_node,
                            'tx_node': tx_node
                        })

            # --- Parent Events ---
            if "RPL: DAG:" in message:
                dag_match = re_dag_chk.search(message)
                if dag_match and dag_match.group(1) == TARGET_DAG_PREFIX:
                    parts = message.split()
                    parent_id = 0
                    try:
                        if "Parent:" in parts:
                            p_idx = parts.index("Parent:") + 1
                            parent_str = parts[p_idx].replace(",", "")
                            parent_id = int(parent_str, 16) if parent_str.lower() != "none" else 0

                        parent_events.append({
                            'time': rel_time,
                            'timestamp_str': time_str,
                            'node': rx_node,
                            'parent': parent_id
                        })
                    except (ValueError, IndexError):
                        pass

    return sorted(list(nodes)), dio_events, parent_events

def generate_tikz_pages(nodes, dio_events, parent_events, output_path):
    """Generates a paginated TikZ file."""

    # Combine all events to sort them by time
    # We add a 'type' tag to distinguish them
    all_events = []
    for d in dio_events:
        d['type'] = 'DIO'
        all_events.append(d)
    for p in parent_events:
        p['type'] = 'PARENT'
        all_events.append(p)

    # Sort chronologically
    all_events.sort(key=lambda x: x['time'])

    if not all_events:
        print("No events found.")
        return

    max_time = all_events[-1]['time']

    # Calculate Pagination
    # Time per page = Height / Scale
    time_per_page = PAGE_HEIGHT_CM / Y_SCALE_CM

    content = []

    # Header helper function
    def add_header(current_time_offset):
        """Draws the Node IDs at the top of the page."""
        c = []
        c.append(r"\begin{tikzpicture}[x=1cm, y=-1cm]") # Note y=-1cm, we handle scaling manually
        # Draw vertical grid lines for the whole page length
        c.append(fr"\draw[lightgray, dotted] (0,0) grid ({max(nodes)+1}, {PAGE_HEIGHT_CM});")

        # Draw Node Headers
        for n in nodes:
            c.append(fr"\node[font=\bfseries, fill=white, inner sep=2pt] at ({n}, 0) {{{n}}};")
        return c

    # Footer/Closer helper
    def close_page():
        return [r"\end{tikzpicture}", r"\newpage"]

    current_page_idx = 0
    current_page_start_time = 0.0
    current_page_end_time = time_per_page

    # Start Page 1
    content.extend(add_header(0))

    last_label_y = -999 # To track timestamp overlap

    # Group events by timestamp for the arrow curvature logic
    # We iterate through indices to look ahead/behind if needed
    i = 0
    while i < len(all_events):
        evt = all_events[i]
        t = evt['time']

        # --- Pagination Check ---
        if t > current_page_end_time:
            # Close current page
            content.extend(close_page())

            # Start new page
            current_page_idx += 1
            current_page_start_time = current_page_end_time
            current_page_end_time += time_per_page
            content.extend(add_header(current_page_start_time))
            last_label_y = -999 # Reset label tracker

        # Calculate Y coordinate relative to current page top
        # y = (Absolute Time - Page Start Time) * Scale
        y_pos = (t - current_page_start_time) * Y_SCALE_CM

        # --- Time Label Logic ---
        # Only print if far enough from last label
        if abs(y_pos - last_label_y) > MIN_LABEL_DIST_CM:
            # Print label on left axis
            label = evt['timestamp_str']
            # Optional: Trim .000 ms if you want shorter labels
            # label = label.split('.')[0]
            content.append(fr"\node[anchor=east, font=\tiny, color=gray] at (0, {y_pos:.2f}) {{{label}}};")
            last_label_y = y_pos

        # --- Draw Events ---
        if evt['type'] == 'DIO':
            # Green dots
            content.append(fr"\fill[green!60!black] ({evt['rx_node']}, {y_pos:.2f}) circle (2pt);")

        elif evt['type'] == 'PARENT':
            # Arrow Logic
            child = evt['node']
            parent = evt['parent']

            if parent == 0:
                # Lost Parent -> Black Cross
                content.append(fr"\node[cross out, draw=black, thick, inner sep=2pt] at ({child}, {y_pos:.2f}) {{}};")
            else:
                # Valid Parent -> Arrow

                # Check for "simultaneous" arrows to adjust curve
                # Look ahead to see how many events match this timestamp & type
                simul_count = 0
                idx_in_batch = 0

                # Simple loop to count simultaneous parent switches
                j = i
                while j < len(all_events) and abs(all_events[j]['time'] - t) < 0.001 and all_events[j]['type'] == 'PARENT':
                    simul_count += 1
                    j += 1

                # Find current index in this batch
                # (We re-scan slightly, but n is small)
                k = i
                while k >= 0 and abs(all_events[k]['time'] - t) < 0.001 and all_events[k]['type'] == 'PARENT':
                    idx_in_batch += 1
                    k -= 1
                # idx_in_batch is 1-based index of this specific arrow in the group

                # Determine Bend Angle and Color
                # Cycle colors based on batch index
                color = COLORS[(idx_in_batch - 1) % len(COLORS)]

                # Base bend logic
                # If simultaneous arrows exist, we increase bend for each subsequent one
                # to separate them visually.
                base_bend = 45
                bend_deg = base_bend + ((idx_in_batch - 1) * 15)

                # Direction of bend
                # Convention: Child on Left, Parent on Right -> Bend Left (Arc Up)
                # But TikZ 'bend left' is relative to the path direction.
                # Standard visual: arcs shouldn't cross straight lines if possible.

                # Let's standardize: always arc "downward" relative to the graph
                # (which visually looks like arcing between columns)
                # Actually, standardizing 'bend right' usually looks cleaner.
                bend_cmd = f"bend right={bend_deg}"

                # Specific Overrides:
                # If distance is huge (>3 nodes), make line dashed or thinner?
                # Keep simple for now.

                content.append(fr"\draw[->, thick, {color}, >={latex_arrow_head()}, {bend_cmd}] ({child}, {y_pos:.2f}) to ({parent}, {y_pos:.2f});")

        i += 1

    # Close final page
    content.append(r"\end{tikzpicture}")

    # Write File
    with open(output_path, 'w') as f:
        f.write("\n".join(content))
    print(f"Generated paginated TikZ: {output_path}")

def latex_arrow_head():
    """Returns the LaTeX string for the arrow tip style."""
    return "stealth"

def main():
    parser = argparse.ArgumentParser(description="Visualize RPL Log (TikZ)")
    parser.add_argument("logfile", type=Path, help="Path to raw Contiki log file")
    args = parser.parse_args()

    if not args.logfile.exists():
        print("Error: File not found.")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    nodes, dios, parents = parse_log_file(args.logfile)

    if not nodes:
        print("No nodes found.")
        sys.exit(1)

    print(f"Nodes: {nodes}")
    print(f"Events: {len(dios)} DIOs, {len(parents)} Switches.")

    generate_tikz_pages(nodes, dios, parents, OUTPUT_FILENAME)

if __name__ == "__main__":
    main()
