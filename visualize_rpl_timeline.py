#!/usr/bin/env python3
import sys
import re
from pathlib import Path
from collections import defaultdict

# --- Configuration ---
# Map Instance IDs to recognizable names/roots based on your context
INSTANCE_MAP = {
    '30': {'name': 'DODAG 1 (fd00::)', 'root': '7'},
    '46': {'name': 'DODAG 2 (fd02::)', 'root': '8'}
}

# Output filename
OUTPUT_TEX_FILE = "RPL_Timeline.tex"

def get_latex_preamble():
    return r"""
\documentclass[a4paper, landscape]{article}
\usepackage[margin=1cm]{geometry}
\usepackage{fontspec}
\setmainfont{Latin Modern Roman}
\usepackage{tikz}
\usetikzlibrary{graphs, graphdrawing, arrows.meta}
\usegdlibrary{layered, trees} % Requires LuaLaTeX

% Visual Styles
\tikzset{
    node_style/.style={circle, draw, fill=white, minimum size=0.8cm, font=\bfseries},
    root_style/.style={rectangle, draw, fill=blue!20, minimum size=0.8cm, font=\bfseries},
    edge_style/.style={-Stealth, thick},
    loop_style/.style={-Stealth, ultra thick, red, dashed}
}

\begin{document}
"""

def get_latex_footer():
    return r"\end{document}"

class NetworkState:
    def __init__(self):
        # Structure: self.topology[instance_id][child_id] = parent_id
        self.topology = defaultdict(dict)
        self.last_written_topology = None
        
    def update_parent(self, instance_id, child_id, parent_id):
        """
        Updates the parent. 
        Returns True if this actually changed the topology, False otherwise.
        """
        current_parent = self.topology[instance_id].get(child_id)
        
        if current_parent != parent_id:
            self.topology[instance_id][child_id] = parent_id
            return True
        return False

    def get_snapshot_hash(self):
        """Create a hashable representation of the current state to detect changes."""
        # Convert dicts to sorted tuples for comparison
        snap = []
        for inst in sorted(self.topology.keys()):
            edges = sorted(self.topology[inst].items())
            snap.append((inst, tuple(edges)))
        return tuple(snap)

def generate_tikz_graph(topology, instance_id):
    """Generates TikZ code for a single Instance graph."""
    config = INSTANCE_MAP.get(instance_id, {'name': f'Instance {instance_id}', 'root': '?'})
    root_node = config['root']
    
    # Start graph block
    tikz = [
        r"\begin{tikzpicture}",
        r"\graph [layered layout, sibling distance=8mm, level distance=15mm] {",
        f"    // Root Node Definition",
        f"    {root_node} [root_style, as={root_node}];"
    ]
    
    # Add nodes and edges
    # We need to handle cases where nodes are disconnected or form loops
    nodes_in_graph = set([root_node])
    edges = []
    
    # Extract edges for this instance
    inst_topology = topology.get(instance_id, {})
    
    for child, parent in inst_topology.items():
        # Sanitize IDs (remove leading zeros if necessary)
        child = str(int(child)) 
        parent = str(int(parent))
        
        edge_style = "edge_style"
        # Simple loop detection (A->B and B->A) for styling
        if inst_topology.get(parent) == child:
             edge_style = "loop_style"

        edges.append(f"    {parent} -> [{edge_style}] {child};")
        nodes_in_graph.add(child)
        nodes_in_graph.add(parent)

    # Define non-root nodes style
    tikz.append("    // Node Styles")
    for node in nodes_in_graph:
        if node != root_node:
            tikz.append(f"    {node} [node_style, as={node}];")

    # Add Edges
    tikz.extend(edges)
    
    tikz.append("};") # End graph
    tikz.append(r"\end{tikzpicture}")
    return "\n".join(tikz)

def process_log_file(logfile_path):
    network = NetworkState()
    
    # Regex Patterns
    # Matches: 273994:00:19:56.392 Node:2 :[INFO: RPL       ] --- RPL Neighbour Set for Instance ID: 46 ---
    re_table_start = re.compile(r'(\d+:\d{2}:\d{2}\.\d{3})\s+Node:(\d+)\s+.*RPL Neighbour Set for Instance ID:\s+(\d+)')
    
    # Matches: ... Parent: 08 | ... | Fresh U, Pref Y
    re_entry = re.compile(r'Parent:\s*([0-9a-fA-F]+).*Pref\s+(Y|N)')
    
    # Matches: --- End of Table ...
    re_table_end = re.compile(r'--- End of Table')

    with open(logfile_path, 'r', encoding='utf-8') as f:
        
        latex_content = [get_latex_preamble()]
        
        current_timestamp = ""
        current_node = None
        current_instance = None
        current_preferred_found = False
        pending_change = False

        for line in f:
            # 1. Check for Table Start
            match_start = re_table_start.search(line)
            if match_start:
                current_timestamp = match_start.group(1)
                current_node = str(int(match_start.group(2))) # Normalize '02' to '2'
                current_instance = match_start.group(3)
                current_preferred_found = False
                continue

            # 2. Check for Table Entries (only if we are inside a table)
            if current_node and current_instance:
                match_entry = re_entry.search(line)
                if match_entry:
                    parent_hex = match_entry.group(1)
                    is_preferred = match_entry.group(2) == 'Y'
                    
                    if is_preferred:
                        # Convert hex parent (08) to decimal string (8)
                        parent_id = str(int(parent_hex, 16))
                        
                        # Update Network State
                        if network.update_parent(current_instance, current_node, parent_id):
                            pending_change = True
                        
                        current_preferred_found = True

                # 3. Check for Table End
                if re_table_end.search(line):
                    # Handle case where a node has NO preferred parent (lost connectivity)
                    if not current_preferred_found:
                        # If it previously had a parent in this instance, remove it
                        if current_node in network.topology[current_instance]:
                            del network.topology[current_instance][current_node]
                            pending_change = True
                    
                    # IF the network state changed effectively, write a snapshot
                    if pending_change:
                        # Only write if the global hash changed (deduplication)
                        current_hash = network.get_snapshot_hash()
                        if current_hash != network.last_written_topology:
                            
                            # --- Generate Latex Page ---
                            latex_content.append(r"\clearpage")
                            latex_content.append(f"\\section*{{Timestamp: {current_timestamp}}}")
                            latex_content.append(r"\begin{center}")
                            
                            # Side by Side layout
                            latex_content.append(r"\begin{minipage}[t]{0.48\textwidth}")
                            latex_content.append(r"\centering \textbf{DODAG 1 (fd00)}\\ \vspace{0.5cm}")
                            latex_content.append(generate_tikz_graph(network.topology, '30'))
                            latex_content.append(r"\end{minipage}\hfill")
                            latex_content.append(r"\begin{minipage}[t]{0.48\textwidth}")
                            latex_content.append(r"\centering \textbf{DODAG 2 (fd02)}\\ \vspace{0.5cm}")
                            latex_content.append(generate_tikz_graph(network.topology, '46'))
                            latex_content.append(r"\end{minipage}")
                            
                            latex_content.append(r"\end{center}")
                            
                            network.last_written_topology = current_hash
                            pending_change = False # Reset flag

                    # Reset State variables
                    current_node = None
                    current_instance = None

        latex_content.append(get_latex_footer())
        
        # Write to file
        with open(OUTPUT_TEX_FILE, 'w') as out:
            out.write("\n".join(latex_content))
            
        print(f"Generated {OUTPUT_TEX_FILE} with {len(latex_content)} lines.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 visualize_rpl_timeline.py <logfile.txt>")
        sys.exit(1)
    
    log_file = Path(sys.argv[1])
    if not log_file.exists():
        print(f"File not found: {log_file}")
        sys.exit(1)
        
    process_log_file(log_file)
