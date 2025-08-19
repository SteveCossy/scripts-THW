#!/usr/bin/env python3
import sys
import os
import re
import subprocess
from pathlib import Path
from PyPDF2 import PdfReader

# --- Configuration ---
DATA_DIR = Path.home() / "data"
SUMMARY_TEX_FILE = DATA_DIR / "SimSummary.tex"

# --- LaTeX Preamble (Cleaned up) ---
LATEX_PREAMBLE = r"""
\documentclass[a4paper, landscape]{article}
\usepackage[margin=1.5cm, top=2cm, bottom=2cm]{geometry}
\usepackage{fontspec}
\setmainfont{Latin Modern Roman}
\setmonofont{DejaVu Sans Mono}

\usepackage{graphicx}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{hyperref}
\usepackage{tabularx}

\begin{document}
\title{Simulation Run Summary}
\author{Contiki-NG RPL Project}
\date{\today}
\maketitle
\setlength{\extrarowheight}{3pt} % Add a little extra vertical space to all table rows

"""

def get_pdf_page_count(pdf_path):
    """Safely checks if a PDF exists and returns its page count."""
    try:
        if pdf_path.is_file():
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                return len(reader.pages)
        return 0
    except Exception:
        return 0

def parse_summary_file(filepath):
    """Parses the summary file with the most robust logic yet."""
    data = {'mop': 'N/A', 'ofs': 'N/A', 'start_time': 'N/A', 
            'finish_time': 'N/A', 'run_date': 'N/A'}

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- FIX 1: Final robust parsing logic, line by line ---
    start_match = re.search(r"Started at \w+\s+(\w+\s+\d+)\s+.*?(\d{2}:\d{2}:\d{2})", content)
    finish_match = re.search(r"Run finished at .*?(\d{2}:\d{2})", content)
    
    # Iterate through lines to find MOP and OFs without complex regex
    for line in content.splitlines():
#        if "#define RPL_CONF_MOP" in line and not line.strip().startswith("//"):
        if "#define RPL_CONF_MOP" in line and not "//" in line:
            data['mop'] = line.split()[-1]
        if "fd00" in line:
            of1 = line.split(":", 1)[1].strip()
        if "fd02" in line:
            data['ofs'] = of1 +line.split(":", 1)[1].strip()

    if start_match:
        data['run_date'] = start_match.group(1)
        data['start_time'] = start_match.group(2)
    if finish_match:
        data['finish_time'] = finish_match.group(1).strip()
            
    return data

def escape_latex(text):
    """Escapes special LaTeX characters."""
    return text.replace('_', r'\_').replace('%', r'\%').replace('#', r'\#')

def generate_latex_entry(data, timestamp):
    """Creates the LaTeX string for a single simulation entry table."""
    graph_pdf_path = DATA_DIR / f"graph_{timestamp}.pdf"
    page_count = get_pdf_page_count(graph_pdf_path)

    graphics_row = ""
    if page_count > 0:
        graph1 = f"\\includegraphics[page=1, width=0.48\\linewidth, height=4cm, keepaspectratio]{{{graph_pdf_path}}}"
    else:
        graph1 = "\\textit{(Graph 1 not found)}"
    if page_count > 1:
        graph2 = f"\\includegraphics[page=2, width=0.48\\linewidth, height=4cm, keepaspectratio]{{{graph_pdf_path}}}"
    else:
        graph2 = ""
    
    graphics_row = f"""
\\hline
\\multicolumn{{4}}{{|p{{\\dimexpr\\textwidth-2\\tabcolsep-1.2pt\\relax}}|}}{{%
    \\centering
    \\begin{{minipage}}[t]{{0.49\\linewidth}}
        \\centering \\textbf{{DODAG 1 Graph}}\\\\ {graph1}
    \\end{{minipage}}
    \\hfill
    \\begin{{minipage}}[t]{{0.49\\linewidth}}
        \\centering \\textbf{{DODAG 2 Graph}}\\\\ {graph2}
    \\end{{minipage}}
}} \\\\"""

    # --- FIX 2: Better vertical alignment and \cline fix ---
    mop_ofs_cell = (f"\\begin{{minipage}}[t]{{\\linewidth}}\\raggedright " # Use minipage for top alignment
                    f"\\texttt{{{escape_latex(data['mop'])}}} \\\\ \n"
                    f"\\texttt{{{escape_latex(data['ofs'])}}}"
                    f"\\end{{minipage}}")

    latex_entry = f"""
% --- Entry for simulation {timestamp} ---
\\noindent
\\begin{{tabularx}}{{\\linewidth}}{{| p{{2.5cm}} | p{{3.5cm}} | p{{5cm}} | X |}}
\\hline
% --- ROW 1 ---
\\textbf{{Start Time}} & \\textbf{{Sim Run ID}} & \\textbf{{Run Date}} & \\textbf{{Notes}} \\\\
\\texttt{{{escape_latex(data['start_time'])}}} & \\texttt{{{escape_latex(timestamp)}}} & \\texttt{{{escape_latex(data['run_date'])}}} & \\\\
\\hline % Changed from cline to hline for a full line
% --- ROW 2 ---
\\textbf{{Finish Time}} & \\multicolumn{{2}}{{l|}}{{\\textbf{{MOP \& OFs}}}} & \\\\ % Merged MOP & OFs header
\\cline{{1-1}} \\cline{{2-4}} % <-- FIX 3: Corrected cline for notes
\\texttt{{{escape_latex(data['finish_time'])}}} & \\multicolumn{{2}}{{p{{8.5cm}}|}}{{{mop_ofs_cell}}} & \\\\ % Merged data cell
{graphics_row}
\\hline
\\end{{tabularx}}
\\vspace{{1cm}}

"""
    return latex_entry

# ... (update_summary_file, compile_latex, and main functions are unchanged) ...
def update_summary_file(latex_entry):
    header = LATEX_PREAMBLE
    footer = "\\end{document}\n"
    body = ""
    if SUMMARY_TEX_FILE.exists():
        with open(SUMMARY_TEX_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            preamble_match = re.match(r"(.*\\begin\{document\})", content, re.DOTALL)
            if preamble_match:
                header = preamble_match.group(1) + "\n"
                body_content = re.split(r"\\begin\{document\}", content, 1)[1]
                body = body_content.rsplit("\\end{document}", 1)[0]
            else:
                print("Warning: Could not find document structure. Starting fresh body.")
    body += latex_entry
    with open(SUMMARY_TEX_FILE, 'w', encoding='utf-8') as f:
        f.write(header + body + footer)
    print(f"Updated summary file at {SUMMARY_TEX_FILE}")

def compile_latex():
    print(f"Compiling {SUMMARY_TEX_FILE} with lualatex...")
    try:
        latexmk_command = ['latexmk', '-lualatex', '-interaction=nonstopmode', f'-output-directory={DATA_DIR}', str(SUMMARY_TEX_FILE)]
        subprocess.run(latexmk_command, capture_output=True, text=True, check=True)
        print("Compilation successful!")
        pdf_path = DATA_DIR / SUMMARY_TEX_FILE.with_suffix('.pdf').name
        print(f"Output saved to {pdf_path}")
    except subprocess.CalledProcessError as e:
        print(f"\n--- LaTeX Compilation Failed ---\n{e.stdout[-1500:]}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path_to_text_file>")
        sys.exit(1)

    input_file = Path(sys.argv[1])
    if not input_file.is_file():
        print(f"Error: Input file not found: {input_file}")
        sys.exit(1)

    match = re.search(r"text_(\d+)\.txt", input_file.name)
    timestamp = match.group(1) if match else "unknown"

    parsed_data = parse_summary_file(input_file)
    print(parsed_data)
#    new_entry = generate_latex_entry(parsed_data, timestamp)
#    update_summary_file(new_entry)
#    compile_latex()

if __name__ == "__main__":
    main()
