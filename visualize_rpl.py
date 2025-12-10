







#!/usr/bin/env python3
import sys
import re
import argparse
from pathlib import Path

# --- Configuration ---
OUTPUT_FILENAME = "DIO_graph.tex"
TARGET_INSTANCE = "30"
TARGET_DAG_PREFIX = "fd00"

# --- Visualization Settings ---
Y_SCALE_CM = 0.6         # cm per second (vertical)
PAGE_HEIGHT_CM = 22.0    # Max height per page
MIN_LABEL_DIST_CM = 0.5  # Min distance between timestamps

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

    # Regex 1: Time and Node
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

                # --- FILTER APPLIED HERE ---
                # We strictly ignore entries unless they are marked 'Pref Y'
                if "Pref Y" not in message:
                    continue

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

    all_events = []
    for d in dio_events:
        d['type'] = 'DIO'
        all_events.append(d)
    for p in parent_events:
        p['type'] = 'PARENT'
        all_events.append(p)

    all_events.sort(key=lambda x: x['time'])

    if not all_events:
        print("No events found (Check filter settings).")
        return

    time_per_page = PAGE_HEIGHT_CM / Y_SCALE_CM
    content = []

    def add_header(current_time_offset):
        c = []
        c.append(r"\begin{tikzpicture}[x=1cm, y=-1cm]")
        c.append(fr"\draw[lightgray, dotted] (0,0) grid ({max(nodes)+1}, {PAGE_HEIGHT_CM});")
        for n in nodes:
            c.append(fr"\node[font=\bfseries, fill=white, inner sep=2pt] at ({n}, 0) {{{n}}};")
        return c

    def close_page():
        return [r"\end{tikzpicture}", r"\newpage"]

    current_page_idx = 0
    current_page_start_time = 0.0
    current_page_end_time = time_per_page

    content.extend(add_header(0))
    last_label_y = -999

    i = 0
    while i < len(all_events):
        evt = all_events[i]
        t = evt['time']

        if t > current_page_end_time:
            content.extend(close_page())
            current_page_idx += 1
            current_page_start_time = current_page_end_time
            current_page_end_time += time_per_page
            content.extend(add_header(current_page_start_time))
            last_label_y = -999

        y_pos = (t - current_page_start_time) * Y_SCALE_CM

        # Draw Timestamp
        if abs(y_pos - last_label_y) > MIN_LABEL_DIST_CM:
            label = evt['timestamp_str']
            content.append(fr"\node[anchor=east, font=\tiny, color=gray] at (0, {y_pos:.2f}) {{{label}}};")
            last_label_y = y_pos

        if evt['type'] == 'DIO':
            content.append(fr"\fill[green!60!black] ({evt['rx_node']}, {y_pos:.2f}) circle (2pt);")

        elif evt['type'] == 'PARENT':
            child = evt['node']
            parent = evt['parent']

            if parent == 0:
                content.append(fr"\node[cross out, draw=black, thick, inner sep=2pt] at ({child}, {y_pos:.2f}) {{}};")
            else:
                simul_count = 0
                idx_in_batch = 0

                # Check simultaneous events
                j = i
                while j < len(all_events) and abs(all_events[j]['time'] - t) < 0.001 and all_events[j]['type'] == 'PARENT':
                    simul_count += 1
                    j += 1

                k = i
                while k >= 0 and abs(all_events[k]['time'] - t) < 0.001 and all_events[k]['type'] == 'PARENT':
                    idx_in_batch += 1
                    k -= 1

                color = COLORS[(idx_in_batch - 1) % len(COLORS)]

                # --- CURVATURE SETTING ---
                base_bend = 10  # Reduced from 45 as requested
                bend_deg = base_bend + ((idx_in_batch - 1) * 15)
                bend_cmd = f"bend right={bend_deg}"

                content.append(fr"\draw[->, thick, {color}, >={latex_arrow_head()}, {bend_cmd}] ({child}, {y_pos:.2f}) to ({parent}, {y_pos:.2f});")

        i += 1

    content.append(r"\end{tikzpicture}")

    with open(output_path, 'w') as f:
        f.write("\n".join(content))
    print(f"Generated paginated TikZ: {output_path}")

def latex_arrow_head():
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
    print(f"Events: {len(dios)} DIOs, {len(parents)} Switches (Preferred Only).")

    generate_tikz_pages(nodes, dios, parents, OUTPUT_FILENAME)

if __name__ == "__main__":
    main()
