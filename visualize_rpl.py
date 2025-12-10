#!/usr/bin/env python3
import sys
import re
import argparse
from pathlib import Path

# --- Configuration ---
OUTPUT_FILENAME = "Compare_graph.tex"

# --- LEFT GRAPH ---
L_INST = "30"
L_DAG  = "fd00"

# --- RIGHT GRAPH ---
R_INST = "46"
R_DAG  = "fd02"

# --- Visualization Settings ---
Y_SCALE_CM = 0.6
PAGE_HEIGHT_CM = 24.0   # A3 Landscape height
A3_WIDTH_CM = 39.0      # Usable width (leaving margins)
MIN_LABEL_DIST_CM = 0.5
ARROW_BEND = 10         # Flatness
GAP_WIDTH = 4           # Node slots between graphs

# TikZ Colors
COLORS = ["red", "blue", "orange", "teal", "violet", "cyan!70!black", "magenta"]

def parse_time(timestr):
    h, m, s = timestr.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def extract_node_id(ipv6_str):
    clean_ip = ipv6_str.replace("from:", "").strip()
    parts = clean_ip.split(':')
    try:
        return int(parts[-1], 16)
    except ValueError:
        return 0

def parse_log_file(filepath):
    events_left = []
    events_right = []
    nodes = set()

    re_base = re.compile(r"^(\d{2}:\d{2}:\d{2}\.\d+)\s+Node:(\d+)\s+:(.*)")
    re_dio = re.compile(r"Incoming DIO \(id, ver, rank\) = \((\d+),.*\) (from:[\w:]+)")
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

            # --- DIO Parsing ---
            if "Incoming DIO" in message:
                dio_match = re_dio.search(message)
                if dio_match:
                    instance_id, from_ip = dio_match.groups()
                    tx_node = extract_node_id(from_ip)
                    nodes.add(tx_node)

                    evt = {
                        'time': rel_time,
                        'timestamp_str': time_str,
                        'rx_node': rx_node,
                        'tx_node': tx_node,
                        'type': 'DIO'
                    }
                    if instance_id == L_INST:
                        events_left.append(evt)
                    elif instance_id == R_INST:
                        events_right.append(evt)

            # --- Parent Parsing (Pref Y Only) ---
            if "RPL: DAG:" in message and "Pref Y" in message:
                dag_match = re_dag_chk.search(message)
                if dag_match:
                    dag_prefix = dag_match.group(1)
                    parts = message.split()
                    parent_id = 0
                    try:
                        if "Parent:" in parts:
                            p_idx = parts.index("Parent:") + 1
                            parent_str = parts[p_idx].replace(",", "")
                            parent_id = int(parent_str, 16) if parent_str.lower() != "none" else 0

                        evt = {
                            'time': rel_time,
                            'timestamp_str': time_str,
                            'node': rx_node,
                            'parent': parent_id,
                            'type': 'PARENT'
                        }
                        if dag_prefix == L_DAG:
                            events_left.append(evt)
                        elif dag_prefix == R_DAG:
                            events_right.append(evt)
                    except:
                        pass

    return sorted(list(nodes)), events_left, events_right

def generate_tikz_pages(nodes, events_left, events_right, output_path):
    if not nodes:
        print("No nodes found.")
        return

    # --- 1. Layout & Scaling Calculation ---
    node_max = max(nodes)

    # Total units needed: Left Graph + Gap + Right Graph
    # Each graph needs space from 0 to node_max+1
    # Note: nodes start at 1 usually, but grid starts at 0
    units_per_graph = node_max + 2
    total_units_width = (units_per_graph * 2) + GAP_WIDTH

    # Calculate offset for Right Graph
    right_offset = units_per_graph + GAP_WIDTH

    # Calculate Scale Factor to fit A3
    x_scale = A3_WIDTH_CM / total_units_width

    # Cap scale at 1.0 (don't stretch small networks too wide)
    if x_scale > 1.2: x_scale = 1.2

    print(f"Layout Info: Total Units={total_units_width}, Scale={x_scale:.2f} cm/unit")

    # --- 2. Merge Data ---
    all_events = []
    for e in events_left:
        e['graph'] = 'LEFT'
        e['offset'] = 0
        all_events.append(e)
    for e in events_right:
        e['graph'] = 'RIGHT'
        e['offset'] = right_offset
        all_events.append(e)

    all_events.sort(key=lambda x: x['time'])

    time_per_page = PAGE_HEIGHT_CM / Y_SCALE_CM
    content = []

    # --- Helper: Header ---
    def add_header(current_time_offset):
        c = []
        # Apply the calculated X scale
        c.append(fr"\begin{{tikzpicture}}[x={x_scale:.3f}cm, y=-1cm]")

        # Grid - Left
        c.append(fr"\draw[lightgray, dotted] (0,0) grid ({node_max+1}, {PAGE_HEIGHT_CM});")
        # Grid - Right
        c.append(fr"\draw[lightgray, dotted] ({right_offset},0) grid ({right_offset + node_max + 1}, {PAGE_HEIGHT_CM});")

        # Divider Line
        # Centered in the gap
        mid_gap = right_offset - (GAP_WIDTH / 2) - 1 # approximate adjustment
        c.append(fr"\draw[thick, gray] ({mid_gap}, 0) -- ({mid_gap}, {PAGE_HEIGHT_CM});")

        # Text Headers
        c.append(fr"\node[font=\bfseries\large, anchor=west] at (0, -1.5) {{Instance {L_INST} ({L_DAG})}};")
        c.append(fr"\node[font=\bfseries\large, anchor=west] at ({right_offset}, -1.5) {{Instance {R_INST} ({R_DAG})}};")

        # Node Labels
        for n in nodes:
            # Left
            c.append(fr"\node[font=\bfseries, fill=white, inner sep=1pt] at ({n}, 0) {{{n}}};")
            # Right
            c.append(fr"\node[font=\bfseries, fill=white, inner sep=1pt] at ({n + right_offset}, 0) {{{n}}};")

        return c

    def close_page():
        return [r"\end{tikzpicture}", r"\newpage"]

    current_page_idx = 0
    current_page_start_time = 0.0
    current_page_end_time = time_per_page

    content.extend(add_header(0))
    last_label_y = -999

    # Sender deduplication tracker (per page/timestamp)
    # Stores tuples: (timestamp_float, tx_node_id, graph_side)
    drawn_senders = set()

    i = 0
    while i < len(all_events):
        evt = all_events[i]
        t = evt['time']

        # Pagination
        if t > current_page_end_time:
            content.extend(close_page())
            current_page_idx += 1
            current_page_start_time = current_page_end_time
            current_page_end_time += time_per_page
            content.extend(add_header(current_page_start_time))
            last_label_y = -999
            drawn_senders.clear() # Clear dedupe cache for new page

        y_pos = (t - current_page_start_time) * Y_SCALE_CM
        x_shift = evt['offset']

        # Timestamp (Left Axis)
        if abs(y_pos - last_label_y) > MIN_LABEL_DIST_CM:
            label = evt['timestamp_str']
            # We put this at x=-1 to ensure it sits left of the grid
            content.append(fr"\node[anchor=east, font=\tiny, color=gray] at (-0.5, {y_pos:.2f}) {{{label}}};")
            last_label_y = y_pos

        if evt['type'] == 'DIO':
            rx = evt['rx_node'] + x_shift
            tx = evt['tx_node'] + x_shift

            # 1. Draw Receiver (Small Filled)
            content.append(fr"\fill[green!60!black] ({rx}, {y_pos:.2f}) circle (2pt);")

            # 2. Draw Sender (Large Hollow) - Deduplicated
            sender_key = (t, evt['tx_node'], evt['graph'])
            if sender_key not in drawn_senders:
                content.append(fr"\draw[green!60!black, thick] ({tx}, {y_pos:.2f}) circle (4pt);")
                drawn_senders.add(sender_key)

        elif evt['type'] == 'PARENT':
            child = evt['node'] + x_shift
            parent_raw = evt['parent']

            if parent_raw == 0:
                content.append(fr"\node[cross out, draw=black, thick, inner sep=2pt] at ({child}, {y_pos:.2f}) {{}};")
            else:
                parent = parent_raw + x_shift

                # Simultaneous check
                simul_count = 0
                idx_in_batch = 0

                j = i
                while j < len(all_events) and abs(all_events[j]['time'] - t) < 0.001 \
                      and all_events[j]['type'] == 'PARENT' and all_events[j]['graph'] == evt['graph']:
                    simul_count += 1
                    j += 1

                k = i
                while k >= 0 and abs(all_events[k]['time'] - t) < 0.001 \
                      and all_events[k]['type'] == 'PARENT' and all_events[k]['graph'] == evt['graph']:
                    idx_in_batch += 1
                    k -= 1

                color = COLORS[(idx_in_batch - 1) % len(COLORS)]

                bend_deg = ARROW_BEND + ((idx_in_batch - 1) * 15)
                bend_cmd = f"bend right={bend_deg}"

                content.append(fr"\draw[->, thick, {color}, >={latex_arrow_head()}, {bend_cmd}] ({child}, {y_pos:.2f}) to ({parent}, {y_pos:.2f});")

        i += 1

    content.append(r"\end{tikzpicture}")

    with open(output_path, 'w') as f:
        f.write("\n".join(content))
    print(f"Generated side-by-side TikZ: {output_path}")

def latex_arrow_head():
    return "stealth"

def main():
    parser = argparse.ArgumentParser(description="Visualize RPL Log Comparison")
    parser.add_argument("logfile", type=Path, help="Path to raw log")
    args = parser.parse_args()

    if not args.logfile.exists():
        print("Error: File not found.")
        sys.exit(1)

    print(f"Parsing {args.logfile}...")
    nodes, ev_l, ev_r = parse_log_file(args.logfile)

    if not nodes:
        print("No nodes found.")
        sys.exit(1)

    print(f"Nodes: {len(nodes)}")
    print(f"Left ({L_DAG}): {len(ev_l)} events. Right ({R_DAG}): {len(ev_r)} events.")

    generate_tikz_pages(nodes, ev_l, ev_r, OUTPUT_FILENAME)

if __name__ == "__main__":
    main()
