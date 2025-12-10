#!/usr/bin/env python3
import sys
import re
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# --- Configuration ---
# Only parse lines relevant to this Instance/DAG
TARGET_INSTANCE = "30"
TARGET_DAG_PREFIX = "fd00"

def parse_time(timestr):
    """
    Converts 'HH:MM:SS.ms' to total seconds (float).
    """
    h, m, s = timestr.split(':')
    return float(h) * 3600 + float(m) * 60 + float(s)

def extract_node_id(ipv6_str):
    """
    Extracts the last segment of an IPv6 string to get the node ID.
    e.g., 'fe80::201:1:1:5' -> 5
    """
    # Remove 'from:' prefix if present
    clean_ip = ipv6_str.replace("from:", "").strip()
    parts = clean_ip.split(':')
    try:
        # Get last part, convert hex to int (handle cases like 'a' or '10')
        return int(parts[-1], 16)
    except ValueError:
        return 0

def parse_log_file(filepath):
    """
    Parses the raw log file for DIOs and Parent changes.
    Returns:
        nodes (set): All unique node IDs found.
        dio_events (list): {'time', 'rx_node', 'tx_node'}
        parent_events (list): {'time', 'node', 'parent', 'rank', 'cost'}
    """

    dio_events = []
    parent_events = []
    nodes = set()

    # Regex Patterns
    # 1. Base format: 39851:00:07:34.307 Node:6 ...
    re_base = re.compile(r"^\d+:(\d{2}:\d{2}:\d{2}\.\d+)\s+Node:(\d+)\s+:(.*)")

    # 2. DIO: Incoming DIO (id, ver, rank) = (30,240,434) from:fe80::201:1:1:1
    re_dio = re.compile(r"Incoming DIO \(id, ver, rank\) = \((\d+),.*\) (from:[\w:]+)")

    # 3. DAG: RPL: DAG: fd00 ... Parent: 07 | Rank: 128 ...
    # Flexible regex to catch fields even if order changes slightly
    re_dag_chk = re.compile(r"RPL: DAG:\s*([0-9a-fA-F]+)")

    start_time_offset = None

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            base_match = re_base.match(line)
            if not base_match:
                continue

            time_str, node_str, message = base_match.groups()
            current_time = parse_time(time_str)
            rx_node = int(node_str)
            nodes.add(rx_node)

            # Normalize time to start at 0 for the graph
            if start_time_offset is None:
                start_time_offset = current_time
            rel_time = current_time - start_time_offset

            # --- Check for DIO Reception ---
            if "Incoming DIO" in message:
                dio_match = re_dio.search(message)
                if dio_match:
                    instance_id, from_ip = dio_match.groups()

                    # Filter: Only care about specific Instance
                    if instance_id == TARGET_INSTANCE:
                        tx_node = extract_node_id(from_ip)
                        nodes.add(tx_node)
                        dio_events.append({
                            'time': rel_time,
                            'rx_node': rx_node,
                            'tx_node': tx_node
                        })

            # --- Check for Parent / DAG Update ---
            if "RPL: DAG:" in message:
                dag_match = re_dag_chk.search(message)
                if dag_match and dag_match.group(1) == TARGET_DAG_PREFIX:
                    # Extract fields manually to be robust against "Pref Y" etc
                    # Logic: Find "Parent:", take next word. Find "Rank:", take next word.
                    parts = message.split()
                    parent_id = 0
                    rank_val = 0

                    try:
                        if "Parent:" in parts:
                            p_idx = parts.index("Parent:") + 1
                            # Strip leading zeros, handle '07' -> 7
                            parent_str = parts[p_idx].replace(",", "")
                            parent_id = int(parent_str, 16) if parent_str.lower() != "none" else 0

                        if "Rank:" in parts:
                            r_idx = parts.index("Rank:") + 1
                            rank_val = int(parts[r_idx].replace(",", ""))

                        parent_events.append({
                            'time': rel_time,
                            'node': rx_node,
                            'parent': parent_id,
                            'rank': rank_val
                        })
                    except (ValueError, IndexError):
                        pass # parsing failed for this specific line

    return sorted(list(nodes)), dio_events, parent_events

def generate_png(nodes, dio_events, parent_events, output_path):
    """Generates a Matplotlib space-time diagram."""
    fig, ax = plt.subplots(figsize=(12, 10))

    # Grid Setup
    ax.set_xlim(0, max(nodes) + 1)
    # We invert Y so time goes down (like your whiteboard)
    ax.invert_yaxis()

    ax.xaxis.set_major_locator(ticker.MultipleLocator(1))
    ax.grid(True, which='both', linestyle='--', alpha=0.3)

    ax.set_title(f"RPL Convergence (Instance {TARGET_INSTANCE}, DAG {TARGET_DAG_PREFIX})")
    ax.set_xlabel("Node ID")
    ax.set_ylabel("Time (seconds from start of log)")

    # 1. Plot DIO Receptions (Green Dots)
    # Whiteboard: Green dots are RX.
    # We use small green markers.
    rx_x = [d['rx_node'] for d in dio_events]
    rx_y = [d['time'] for d in dio_events]
    ax.scatter(rx_x, rx_y, c='green', s=10, alpha=0.5, label='DIO Received')

    # Optional: Draw lines from TX to RX? (Can be messy if too many)
    # for d in dio_events:
    #    ax.annotate("", xy=(d['rx_node'], d['time']), xytext=(d['tx_node'], d['time']),
    #                arrowprops=dict(arrowstyle="->", color='green', alpha=0.1))

    # 2. Plot Parent Changes (Red/Black logic)
    # We plot the NODE changing the parent
    p_x = [p['node'] for p in parent_events]
    p_y = [p['time'] for p in parent_events]

    # We can color code: Red = valid parent, Black/X = lost parent (0)
    colors = ['red' if p['parent'] != 0 else 'black' for p in parent_events]
    markers = ['o' if p['parent'] != 0 else 'x' for p in parent_events]

    for i, p in enumerate(parent_events):
        m = 'o' if p['parent'] != 0 else 'x'
        c = 'red' if p['parent'] != 0 else 'black'

        ax.scatter(p['node'], p['time'], c=c, marker=m, s=40, zorder=10)

        # Annotation: "P:7 (128)" -> Parent 7, Rank 128
        label = f"{p['parent']}" # Just parent ID to keep it clean
        ax.annotate(label, (p['node'], p['time']),
                    textcoords="offset points", xytext=(5,0),
                    fontsize=8, color='darkred')

    # Legend (Custom proxy artists)
    from matplotlib.lines import Line2D
    legend_elements = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='green', label='RX DIO (Phy)'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='red', label='Selected Parent'),
        Line2D([0], [0], marker='x', color='black', label='Lost Parent (NULL)'),
    ]
    ax.legend(handles=legend_elements, loc='upper right')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"Generated PNG: {output_path}")

def generate_tikz(nodes, dio_events, parent_events, output_path):
    """Generates a TikZ file for high-quality LaTeX plotting."""

    # Scale time for TikZ (1 second = 0.5cm vertical, for example)
    yscale = 0.2

    tikz_content = [
        r"\begin{tikzpicture}[x=1cm, y=-" + str(yscale) + "cm]", # Inverted Y
        r"\draw[help lines, step=1, lightgray] (0,0) grid (" + str(max(nodes)+1) + "," + str(max(d['time'] for d in dio_events)) + ");",
        r"% Axis Labels",
    ]

    # X Axis Labels
    for n in nodes:
        tikz_content.append(fr"\node at ({n}, -2) {{\textbf{{{n}}}}};")

    tikz_content.append(r"% --- DIO Receptions (Green) ---")
    for d in dio_events:
        # Plotting tiny green dots for reception
        t = d['time']
        n = d['rx_node']
        # Commenting the source for debugging in latex
        tikz_content.append(fr"\fill[green!70!black] ({n}, {t:.3f}) circle (2pt); % From {d['tx_node']}")

    tikz_content.append(r"% --- Parent Changes (Red) ---")
    for p in parent_events:
        t = p['time']
        n = p['node']
        par = p['parent']
        rank = p['rank']

        if par == 0:
            # Lost parent (Black X)
            tikz_content.append(fr"\node[cross out, draw=black, thick, inner sep=2pt] at ({n}, {t:.3f}) {{}};")
        else:
            # New Parent (Red Circle)
            tikz_content.append(fr"\draw[red, thick] ({n}, {t:.3f}) circle (4pt);")
            # Label the parent ID to the right
            tikz_content.append(fr"\node[right, font=\tiny, color=red] at ({n}, {t:.3f}) {{{par}}};")

    tikz_content.append(r"\end{tikzpicture}")

    with open(output_path, 'w') as f:
        f.write("\n".join(tikz_content))
    print(f"Generated TikZ: {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Visualize RPL Log")
    parser.add_argument("logfile", type=Path, help="Path to raw Contiki log file")
    args = parser.parse_args()

    if not args.logfile.exists():
        print("Error: File not found.")
        sys.exit(1)

    print(f"Parsing {args.logfile} for Instance {TARGET_INSTANCE}...")
    nodes, dios, parents = parse_log_file(args.logfile)

    if not nodes:
        print("No nodes found. Check log format.")
        sys.exit(1)

    print(f"Found {len(nodes)} nodes, {len(dios)} DIO RX events, {len(parents)} Parent changes.")

    # Output filenames
    png_out = args.logfile.with_suffix('.png')
    tikz_out = args.logfile.with_suffix('.tex')

    generate_png(nodes, dios, parents, png_out)
    generate_tikz(nodes, dios, parents, tikz_out)

if __name__ == "__main__":
    main()
