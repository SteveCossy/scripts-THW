#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from pathlib import Path

# --- Configuration ---
SUMMARY_TEX_FILE = Path.home() / "data" / "SimSummary.tex"
DATA_DIR = Path.home() / "data"

# --- LaTeX Preamble (MODIFIED FOR LUALATEX) ---
LATEX_PREAMBLE = r"""
\documentclass[a4paper]{article}
\usepackage[margin=2cm]{geometry}

% --- FIX 1: Use fontspec for modern fonts and UTF-8 support with lualatex ---
\usepackage{fontspec}
% Latin Modern is a great default with excellent Unicode coverage but not good enough ...
\setmainfont{Latin Modern Roman}

% Set the monospaced font (used by \texttt and listings) to one
% with better Unicode character coverage, like DejaVu Sans Mono.
\setmonofont{DejaVu Sans Mono} % For \texttt and listings

\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{hyperref}

\lstset{
    basicstyle=\ttfamily\small,
    breaklines=true,
}

\begin{document}
\title{Simulation Run Summary}
\author{Contiki-NG RPL Project}
\maketitle

"""

def parse_summary_file(filepath):
    """Parses the text summary file to extract key information."""
    data = {
        'start_time': 'N/A',
        'finish_time': 'N/A',
        'mop': 'N/A',
        'ofs': 'N/A',
        'topology': [],
        'filename': Path(filepath).name
    }
    
    in_mop_section = False
    in_topo_section = False

    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()

            if line.startswith("--- New Simulation Run Started at"):
                match = re.search(r"Started at (.+) ---", line)
                if match:
                    data['start_time'] = match.group(1).strip()
            
            elif line.startswith("Run finished at"):
                data['finish_time'] = line.replace("Run finished at", "").strip()

            elif "Objective Functions:" in line:
                data['ofs'] = line.replace("Objective Functions:", "").strip()
                in_mop_section = False

            if "Options at" in line:
                in_mop_section = True
            elif in_mop_section and line.startswith("#define RPL_CONF_MOP"):
                data['mop'] = line.split()[-1]
                in_mop_section = False
            
            if "--- Final RPL Network Topology Summary ---" in line:
                in_topo_section = True
                continue
            
            if in_topo_section and line:
                if line.startswith('[+] TikZ standalone graph'):
                    in_topo_section = False
                else:
                    # REVERTED: We no longer need to clean the UTF-8 characters.
                    # We just clean the [+] prefix for neatness.
                    clean_line = line.replace('[+]', '')
                    data['topology'].append(clean_line)

    return data

def escape_latex(text):
    """A simple function to escape characters for LaTeX."""
    return text.replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')

def append_to_latex(data, timestamp):
    """Formats the parsed data and appends it to the summary LaTeX file."""
    
    if not SUMMARY_TEX_FILE.exists():
        with open(SUMMARY_TEX_FILE, 'w') as f:
            f.write(LATEX_PREAMBLE)

    topology_str = "\n".join(data['topology'])
    graph_pdf_path = DATA_DIR / f"graph_{timestamp}.pdf"

    latex_entry = f"""
\\section*{{Simulation Run: {escape_latex(timestamp)}}}
\\subsection*{{Source: \\texttt{{{escape_latex(data['filename'])}}}}}

\\begin{{tabular}}{{@{{}}ll}}
\\textbf{{Start Time:}} & {escape_latex(data['start_time'])} \\\\
\\textbf{{Finish Time:}} & {escape_latex(data['finish_time'])} \\\\
\\textbf{{Mode of Op:}} & \\texttt{{{escape_latex(data['mop'])}}} \\\\
\\textbf{{Objective Funcs:}} & \\texttt{{{escape_latex(data['ofs'])}}} \\\\
\\end{{tabular}}

\\subsection*{{Final Topology Summary}}
\\begin{{lstlisting}}
{topology_str}
\\end{{lstlisting}}

\\subsection*{{Visual Topology}}
\\begin{{figure}}
    \\centering
    \\begin{{minipage}}{{0.48\\textwidth}}
        \\centering
        \\includegraphics[page=1, width=\\textwidth, trim=0 1cm 0 1cm, clip]{{{graph_pdf_path}}}
        \\caption*{{DODAG 1}}
    \\end{{minipage}}
    \\hfill
    \\begin{{minipage}}{{0.48\\textwidth}}
        \\centering
        \\includegraphics[page=2, width=\\textwidth, trim=0 1cm 0 1cm, clip]{{{graph_pdf_path}}}
        \\caption*{{DODAG 2 (if present)}}
    \\end{{minipage}}
\\end{{figure}}

\\hrule
\\clearpage

"""
    with open(SUMMARY_TEX_FILE, 'a') as f:
        f.write(latex_entry)
    
    print(f"Successfully appended entry for {timestamp} to {SUMMARY_TEX_FILE}")

def compile_latex():
    """Compiles the LaTeX document using latexmk."""
    print(f"Compiling {SUMMARY_TEX_FILE} with lualatex...")
    
    try:
        # --- FIX 2: Change the command to use lualatex ---
        latexmk_command = [
            'latexmk',
            '-lualatex', # Use the LuaLaTeX engine
            '-interaction=nonstopmode',
            SUMMARY_TEX_FILE.name
        ]
        
        result = subprocess.run(
            latexmk_command,
            cwd=SUMMARY_TEX_FILE.parent,
            capture_output=True,
            text=True,
            check=True
        )
        print("Compilation successful!")
        print(f"Output saved to {SUMMARY_TEX_FILE.with_suffix('.pdf')}")
    except FileNotFoundError:
        print("\nError: 'latexmk' command not found.")
    except subprocess.CalledProcessError as e:
        print("\n--- LaTeX Compilation Failed ---")
        print("latexmk exited with an error. The script will not hang.")
        print("Review the log for details. A common cause is a missing graph PDF file.")
        
def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_text_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.exists():
        print(f"Error: Input file not found at {input_file}")
        sys.exit(1)

    match = re.search(r"text_(\d+)\.txt", input_file.name)
    if not match:
        print(f"Error: Could not extract timestamp from filename '{input_file.name}'")
        sys.exit(1)
    
    timestamp = match.group(1)
    
    graph_pdf = DATA_DIR / f"graph_{timestamp}.pdf"
    if not graph_pdf.exists():
        print(f"Warning: Graph PDF not found at {graph_pdf}. The diagram will be missing.")

    print(f"Parsing data for run {timestamp}...")
    parsed_data = parse_summary_file(input_file)
    
    append_to_latex(parsed_data, timestamp)
    
    compile_latex()

if __name__ == "__main__":
    main()
