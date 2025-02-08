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
