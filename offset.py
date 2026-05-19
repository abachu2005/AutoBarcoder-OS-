# barcode_app_with_offset.py
# Single-file launcher that embeds your original modules unchanged and adds an optional
# "left flank 20-nt upstream" offset mode via a runtime toggle.

import sys, types

# -----------------------------
# Create "barcodes" and "gui" packages
# -----------------------------
barcodes_pkg = types.ModuleType("barcodes")
barcodes_pkg.__path__ = []  # mark as a package
sys.modules["barcodes"] = barcodes_pkg

gui_pkg = types.ModuleType("gui")
gui_pkg.__path__ = []
sys.modules["gui"] = gui_pkg

def _exec_module(modname: str, code: str, package: str | None):
    mod = types.ModuleType(modname)
    mod.__package__ = package
    mod.__dict__["__name__"] = modname
    mod.__dict__["__package__"] = package
    sys.modules[modname] = mod
    exec(code, mod.__dict__)
    return mod

# -----------------------------
# === Your ORIGINAL code (unchanged) ===
# -----------------------------

analysis_py = r'''
# analysis.py
from collections import Counter


def analyze_barcodes(barcodes, top_n=3):
   line_counts = Counter(barcodes)
   most_common_lines = line_counts.most_common(top_n)
   total_lines = len(barcodes)
   most_common_percentages = [
       (line, (count / total_lines) * 100) for line, count in most_common_lines
   ]
   return most_common_percentages
'''

clustering_py = r'''
# clustering.py
import Levenshtein as lev
import networkx as nx
from collections import Counter


def replace_long_sequences(barcodes, length_threshold):
   short_sequences = [barcode for barcode in barcodes if len(barcode) <= length_threshold]
   long_sequences = [barcode for barcode in barcodes if len(barcode) > length_threshold]


   replaced_sequences = []
   for long_seq in long_sequences:
       replaced = False
       for short_seq in short_sequences:
           if short_seq in long_seq:
               replaced_sequences.append(short_seq)
               replaced = True
               break
       if not replaced:
           replaced_sequences.append(long_seq)


   return short_sequences + replaced_sequences


def cluster_barcodes(barcodes, distance_threshold):
   G = nx.Graph()
   for barcode in barcodes:
       G.add_node(barcode)


   for i, barcode1 in enumerate(barcodes):
       for j in range(i + 1, len(barcodes)):
           barcode2 = barcodes[j]
           if lev.distance(barcode1, barcode2) <= distance_threshold:
               G.add_edge(barcode1, barcode2)


   clusters = list(nx.connected_components(G))
   return clusters


def most_common_barcodes(cluster, n=3):
   return Counter(cluster).most_common(n)


def reprint_with_common_barcodes(original_barcodes, clusters):
   barcode_to_cluster = {}
   cluster_list = []


   for cluster in clusters:
       for barcode in cluster:
           barcode_to_cluster[barcode] = cluster


   for original_barcode in original_barcodes:
       if original_barcode in barcode_to_cluster:
           cluster_list.append((barcode_to_cluster[original_barcode], original_barcode))
       else:
           cluster_list.append((set(), original_barcode))


   return cluster_list
'''

processing_py = r'''
# processing.py
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


from .clustering import replace_long_sequences, cluster_barcodes, reprint_with_common_barcodes, most_common_barcodes
from .analysis import analyze_barcodes
from .reading import allocate_reads_by_plate
import os
import glob


def process_barcodes_for_reads(reads, word1, word2, start_text, end_text, length_threshold, distance_threshold):
   barcodes = []
   for line in reads:
       if word1 in line and word2 in line:
           start_index = line.find(start_text) + len(start_text)
           end_index = line.find(end_text, start_index)
           if start_index != -1 and end_index != -1:
               word3 = line[start_index:end_index]
               barcodes.append(word3)


   barcodes = replace_long_sequences(barcodes, length_threshold)
   clusters = cluster_barcodes(barcodes, distance_threshold)
   clustered_barcodes = reprint_with_common_barcodes(barcodes, clusters)


   cluster_dict = defaultdict(list)
   for cluster, barcode in clustered_barcodes:
       cluster_dict[frozenset(cluster)].append(barcode)


   all_common_barcodes = []
   for cluster, barcodes_in_cluster in cluster_dict.items():
       most_common_barcodes_list = most_common_barcodes(barcodes_in_cluster, 1)
       most_common = most_common_barcodes_list[0][0]
       for _ in barcodes_in_cluster:
           modified_barcode = f"G{most_common}"
           all_common_barcodes.append(modified_barcode)


   most_common_percentages_after = analyze_barcodes(all_common_barcodes, top_n=3)
   return most_common_percentages_after


def process_single_plate_for_reads(
   output_summary_path,
   output_pdf_path,
   reads,
   start_text,
   end_text,
   length_threshold,
   distance_threshold,
   rows,
   columns
):
   array_2d = [
       [(rows[i], columns[j]) for j in range(len(columns))]
       for i in range(len(rows))
   ]
   processed_pairs = 0
   output = ""


   with PdfPages(output_pdf_path) as pdf:
       for row_idx in range(len(array_2d)):
           for col_idx in range(len(array_2d[row_idx])):
               word1, word2 = array_2d[row_idx][col_idx]
               most_common_percentages_after = process_barcodes_for_reads(
                   reads, word1, word2,
                   start_text, end_text,
                   length_threshold, distance_threshold
               )


               # if no barcodes found → mark as contaminated
               if not most_common_percentages_after:
                   output += f"R{row_idx + 1}C{col_idx + 1}: CONTAMINATED (no barcodes)\n"
                   labels = ["Contaminated"]
                   percentages = [0]
               else:
                   output += (
                       f"R{row_idx + 1}C{col_idx + 1}: "
                       f"{', '.join(f'{line} ({pct:.2f}%)' for line, pct in most_common_percentages_after)}\n"
                   )
                   labels, percentages = zip(*most_common_percentages_after)


               # generate plot (even for contaminated we draw a 0% bar)
               fig, ax = plt.subplots(figsize=(10, 6))
               ax.bar(labels, percentages, color='blue')
               ax.set_title(f'R{row_idx + 1}C{col_idx + 1}: {word1} - {word2}')
               ax.set_xlabel('Barcode')
               ax.set_ylabel('Percentage')
               ax.set_ylim(0, 100)
               ax.tick_params(axis='x', labelsize=8)


               pdf.savefig(fig)
               plt.close(fig)


               processed_pairs += 1
               if processed_pairs >= 96:
                   break
           if processed_pairs >= 96:
               break


   with open(output_summary_path, 'w') as summary_file:
       summary_file.write(output)




def process_all_pairs_multiple(
   output_summary_path,
   output_pdf_path,
   file_path,
   start_text,
   end_text,
   length_threshold,
   distance_threshold,
   plate_ids,
   rows,
   columns
):
   # Allocate reads by plate IDs and create separate text files for each plate in the 'reads' directory
   word_count, total_lines, reads_dir = allocate_reads_by_plate(file_path, plate_ids, os.path.dirname(output_summary_path))


   # Process each generated text file separately as a single plate
   for plate_file in glob.glob(os.path.join(reads_dir, "*_reads.txt")):
       plate_id = os.path.basename(plate_file).split("_reads.txt")[0]
       print(f"Processing Plate {plate_id} with reads from {plate_file}...")


       output_summary_plate = f"{output_summary_path}_Plate_{plate_id}.txt"
       output_pdf_plate = f"{output_pdf_path}_Plate_{plate_id}.pdf"


       # Process and analyze the reads for this plate
       with open(plate_file, 'r') as reads:
           process_single_plate_for_reads(
               output_summary_plate,
               output_pdf_plate,
               reads.readlines(),
               start_text,
               end_text,
               length_threshold,
               distance_threshold,
               rows,
               columns
           )


       print(f"Finished processing Plate {plate_id}.")
'''

reading_py = r'''
# reading.py
import os
import glob
from collections import defaultdict


def read_barcodes_from_merged(file_path, word1, word2, start_text, end_text):
   barcodes = []
   with open(file_path, 'r') as merged:
       for line in merged:
           if word1 in line and word2 in line:
               start_index = line.find(start_text) + len(start_text)
               end_index = line.find(end_text, start_index)
               if start_index != -1 and end_index != -1:
                   word3 = line[start_index:end_index]
                   barcodes.append(word3)
   return barcodes


def allocate_reads_by_plate(file_path, plate_ids, output_dir):
   """
   Run through the input file for each plate ID and write lines to respective files in a 'reads' directory.
   """
   # Create a 'reads' directory within the output directory to store the reads files
   reads_dir = os.path.join(output_dir, 'reads')
   if not os.path.exists(reads_dir):
       os.makedirs(reads_dir)


   # Initialize a dictionary to store counts for each plate ID
   word_count = {plate_id: 0 for plate_id in plate_ids}
   total_lines = 0


   # Process each plate ID individually
   for plate_id in plate_ids:
       output_file_path = os.path.join(reads_dir, f"{plate_id}_reads.txt")
       with open(output_file_path, 'w') as output_file:
           with open(file_path, 'r') as file:
               for line in file:
                   total_lines += 1
                   if plate_id in line:
                       word_count[plate_id] += 1
                       output_file.write(line)


       print(f"Plate {plate_id} allocated {word_count[plate_id]} reads out of {total_lines} lines.")


   return word_count, total_lines, reads_dir
'''

app_py = r'''
# app.py
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk


from barcodes.processing import (
   process_all_pairs_multiple,
   process_single_plate_for_reads
)


class BarcodeProcessorApp(tk.Tk):
   def __init__(self):
       super().__init__()
       self.title("96 Well Plate RNA Barcode Analysis")
       self.geometry("800x600")
       self.configure(bg='black')
       self.create_widgets()
       self.center_widgets()


   def create_widgets(self):
       # Styles for labels, entries, and text widgets
       label_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white'}
       entry_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white', 'insertbackground': 'white'}
       text_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white', 'insertbackground': 'white'}


       self.labels_and_entries = [
           (tk.Label(self, text="Sequencing Data (.fastq or .txt):", **label_style),
            tk.Entry(self, width=50, **entry_style)),
           (tk.Label(self, text="Row Barcodes:", **label_style),
            tk.Text(self, width=50, height=5, **text_style)),
           (tk.Label(self, text="Column Barcodes:", **label_style),
            tk.Text(self, width=50, height=5, **text_style)),
           (tk.Label(self, text="Flanking Sequence 1:", **label_style),
            tk.Entry(self, width=20, **entry_style)),
           (tk.Label(self, text="Flanking Sequence 2:", **label_style),
            tk.Entry(self, width=20, **entry_style)),
           (tk.Label(self, text="Expected RNA Barcode Length:", **label_style),
            tk.Entry(self, width=10, **entry_style)),
           (tk.Label(self, text="Edit Tolerance:", **label_style),
            tk.Entry(self, width=10, **entry_style)),
           (tk.Label(self, text="Raw Data Output File (.txt):", **label_style),
            tk.Entry(self, width=50, **entry_style)),
           (tk.Label(self, text="Graphical Data Output File (.pdf):", **label_style),
            tk.Entry(self, width=50, **entry_style)),
           (tk.Label(self, text="Plate IDs (for multiple analysis):", **label_style),
            tk.Text(self, width=50, height=5, **text_style))
       ]


       for i, (label, entry) in enumerate(self.labels_and_entries):
           label.grid(row=i, column=0, padx=10, pady=10, sticky="e")
           entry.grid(row=i, column=1, padx=10, pady=10, sticky="w")


       # Buttons for file browsing
       self.browse_buttons = [
           tk.Button(self, text="Browse", command=self.browse_file, bg='grey', fg='black', font=('Helvetica', 12)),
           tk.Button(self, text="Browse", command=self.browse_output_txt, bg='grey', fg='black', font=('Helvetica', 12)),
           tk.Button(self, text="Browse", command=self.browse_output_pdf, bg='grey', fg='black', font=('Helvetica', 12))
       ]


       self.browse_buttons[0].grid(row=0, column=2, padx=10, pady=10, sticky="w")
       self.browse_buttons[1].grid(row=7, column=2, padx=10, pady=10, sticky="w")
       self.browse_buttons[2].grid(row=8, column=2, padx=10, pady=10, sticky="w")


       # Button to start processing
       self.process_button = tk.Button(
           self,
           text="Process Barcodes",
           command=self.process_all_pairs,
           bg='green',
           fg='white',
           font=('Helvetica', 12)
       )
       self.process_button.grid(row=11, column=0, columnspan=3, padx=10, pady=10, sticky="ew")


   def center_widgets(self):
       for i in range(12):
           self.grid_rowconfigure(i, weight=1)
       self.grid_columnconfigure(0, weight=1)
       self.grid_columnconfigure(1, weight=1)
       self.grid_columnconfigure(2, weight=1)


   def browse_file(self):
       file_path = filedialog.askopenfilename()
       if file_path:
           self.labels_and_entries[0][1].insert(0, file_path)


   def browse_output_txt(self):
       output_path = filedialog.asksaveasfilename(
           defaultextension=".txt",
           filetypes=[("Text files", "*.txt")]
       )
       if output_path:
           self.labels_and_entries[7][1].insert(0, output_path)


   def browse_output_pdf(self):
       output_path = filedialog.asksaveasfilename(
           defaultextension=".pdf",
           filetypes=[("PDF files", "*.pdf")]
       )
       if output_path:
           self.labels_and_entries[8][1].insert(0, output_path)


   def process_all_pairs(self):
       # Extracting input parameters
       file_path = self.labels_and_entries[0][1].get()
       start_text = self.labels_and_entries[3][1].get()
       end_text = self.labels_and_entries[4][1].get()
       length_threshold = int(self.labels_and_entries[5][1].get()) + 5
       distance_threshold = int(self.labels_and_entries[6][1].get())
       output_summary_path = self.labels_and_entries[7][1].get()
       output_pdf_path = self.labels_and_entries[8][1].get()
       plate_ids_text = self.labels_and_entries[9][1].get("1.0", tk.END).strip()


       # Reading row and column barcode lists
       rows = self.labels_and_entries[1][1].get("1.0", tk.END).strip().split('\n')
       columns = self.labels_and_entries[2][1].get("1.0", tk.END).strip().split('\n')


       # If plate IDs are provided, run multi-plate processing; otherwise, single-plate
       if plate_ids_text:
           plate_ids = plate_ids_text.split('\n')
           process_all_pairs_multiple(
               output_summary_path,
               output_pdf_path,
               file_path,
               start_text,
               end_text,
               length_threshold,
               distance_threshold,
               plate_ids,
               rows,
               columns
           )
       else:
           with open(file_path, 'r') as file_in:
               process_single_plate_for_reads(
                   output_summary_path,
                   output_pdf_path,
                   file_in.readlines(),
                   start_text,
                   end_text,
                   length_threshold,
                   distance_threshold,
                   rows,
                   columns
               )


       messagebox.showinfo(
           "Processing Result",
           f"Processing complete. Results saved to {output_summary_path} and {output_pdf_path}."
       )
'''

main_py = r'''
# main.py
from gui.app import BarcodeProcessorApp


def main():
   app = BarcodeProcessorApp()
   app.mainloop()


if __name__ == "__main__":
   main()
'''

# -----------------------------
# Install original modules into sys.modules (unchanged)
# -----------------------------
_exec_module("barcodes.analysis", analysis_py, package="barcodes")
_exec_module("barcodes.clustering", clustering_py, package="barcodes")
_exec_module("barcodes.reading", reading_py, package="barcodes")
_exec_module("barcodes.processing", processing_py, package="barcodes")
_exec_module("gui.app", app_py, package="gui")
_exec_module("main", main_py, package=None)  # present for completeness; we won't call main.main()

# -----------------------------
# === Offset enhancement (new, additive) ===
# -----------------------------
# This variant extracts the **last expected_len nt** between the two flanks,
# which correctly drops a 20-nt filler immediately after the left flank.

def _extract_barcode_with_offset(line: str, start_text: str, end_text: str, expected_len: int):
    s = line.find(start_text)
    if s == -1:
        return None
    s += len(start_text)
    e = line.find(end_text, s)
    if e == -1:
        return None
    window = line[s:e]
    if len(window) < expected_len:
        return None
    # keep LAST expected_len (handles filler-before-barcode)
    return window[-expected_len:]

def _process_barcodes_for_reads_offset(reads, word1, word2, start_text, end_text, length_threshold, distance_threshold):
    # defer to original modules for downstream steps; only extraction changes
    from barcodes.clustering import replace_long_sequences, cluster_barcodes, reprint_with_common_barcodes, most_common_barcodes
    from barcodes.analysis import analyze_barcodes
    from collections import defaultdict

    expected_len = max(1, length_threshold - 5)  # your GUI sets threshold = expected_len + 5

    barcodes = []
    for line in reads:
        if word1 in line and word2 in line:
            bc = _extract_barcode_with_offset(line, start_text, end_text, expected_len)
            if bc is not None:
                barcodes.append(bc)

    barcodes = replace_long_sequences(barcodes, length_threshold)
    clusters = cluster_barcodes(barcodes, distance_threshold)
    clustered_barcodes = reprint_with_common_barcodes(barcodes, clusters)

    cluster_dict = defaultdict(list)
    for cluster, barcode in clustered_barcodes:
        cluster_dict[frozenset(cluster)].append(barcode)

    all_common_barcodes = []
    for cluster, barcodes_in_cluster in cluster_dict.items():
        most_common_barcodes_list = most_common_barcodes(barcodes_in_cluster, 1)
        most_common = most_common_barcodes_list[0][0]
        for _ in barcodes_in_cluster:
            modified_barcode = f"G{most_common}"
            all_common_barcodes.append(modified_barcode)

    most_common_percentages_after = analyze_barcodes(all_common_barcodes, top_n=3)
    return most_common_percentages_after

# -----------------------------
# Launch the GUI and inject a toggle without modifying original code
# -----------------------------
def launch_gui_with_offset_toggle():
    import tkinter as tk
    from gui.app import BarcodeProcessorApp
    import barcodes.processing as bp

    app = BarcodeProcessorApp()

    # Add a checkbox (row 10 is free in the original layout)
    app.use_offset_var = tk.BooleanVar(value=False)
    app.offset_check = tk.Checkbutton(
        app,
        text="Use 20-nt left-flank offset (skip 20 filler)",
        variable=app.use_offset_var,
        bg='black', fg='white', selectcolor='black',
        font=('Helvetica', 12), anchor='w'
    )
    app.offset_check.grid(row=10, column=0, columnspan=3, padx=10, pady=4, sticky='w')

    # Save original handler; wrap it to temporarily monkey-patch the processing func
    original_handler = app.process_all_pairs

    def wrapped_handler():
        if app.use_offset_var.get():
            # swap in our offset extractor just for this run
            orig_func = bp.process_barcodes_for_reads
            try:
                bp.process_barcodes_for_reads = _process_barcodes_for_reads_offset
                original_handler()
            finally:
                bp.process_barcodes_for_reads = orig_func
        else:
            original_handler()

    # Rebind the button to our wrapped handler
    app.process_button.configure(command=wrapped_handler)

    app.mainloop()

if __name__ == "__main__":
    launch_gui_with_offset_toggle()
