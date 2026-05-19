"""Tkinter desktop GUI for AutoBarcoder.

For most users the web UI (``python -m webapp.backend.main``) is recommended.
This GUI is retained for users who prefer a no-server desktop workflow.
"""
import tkinter as tk
from tkinter import filedialog, messagebox

from barcodes.processing import (
    process_all_pairs_multiple,
    process_single_plate_for_reads,
)


class BarcodeProcessorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AutoBarcoder — 96-Well Plate RNA Barcode Analysis")
        self.geometry("820x680")
        self.configure(bg="black")
        self.use_offset = tk.BooleanVar(value=False)
        self.create_widgets()
        self.center_widgets()

    def create_widgets(self):
        label_style = {"font": ("Helvetica", 12), "bg": "black", "fg": "white"}
        entry_style = {"font": ("Helvetica", 12), "bg": "black", "fg": "white", "insertbackground": "white"}
        text_style = {"font": ("Helvetica", 12), "bg": "black", "fg": "white", "insertbackground": "white"}

        self.labels_and_entries = [
            (tk.Label(self, text="Sequencing Data (.fastq or .txt):", **label_style),
             tk.Entry(self, width=50, **entry_style)),
            (tk.Label(self, text="Row Barcodes:", **label_style),
             tk.Text(self, width=50, height=5, **text_style)),
            (tk.Label(self, text="Column Barcodes:", **label_style),
             tk.Text(self, width=50, height=5, **text_style)),
            (tk.Label(self, text="Flanking Sequence 1 (5'):", **label_style),
             tk.Entry(self, width=20, **entry_style)),
            (tk.Label(self, text="Flanking Sequence 2 (3'):", **label_style),
             tk.Entry(self, width=20, **entry_style)),
            (tk.Label(self, text="Expected RNA Barcode Length:", **label_style),
             tk.Entry(self, width=10, **entry_style)),
            (tk.Label(self, text="Edit Tolerance:", **label_style),
             tk.Entry(self, width=10, **entry_style)),
            (tk.Label(self, text="Raw Data Output File (.txt):", **label_style),
             tk.Entry(self, width=50, **entry_style)),
            (tk.Label(self, text="Graphical Data Output File (.pdf):", **label_style),
             tk.Entry(self, width=50, **entry_style)),
            (tk.Label(self, text="Plate IDs (optional, one per line):", **label_style),
             tk.Text(self, width=50, height=4, **text_style)),
        ]

        for i, (label, entry) in enumerate(self.labels_and_entries):
            label.grid(row=i, column=0, padx=10, pady=6, sticky="e")
            entry.grid(row=i, column=1, padx=10, pady=6, sticky="w")

        self.browse_buttons = [
            tk.Button(self, text="Browse", command=self.browse_file, bg="grey", fg="black", font=("Helvetica", 12)),
            tk.Button(self, text="Browse", command=self.browse_output_txt, bg="grey", fg="black", font=("Helvetica", 12)),
            tk.Button(self, text="Browse", command=self.browse_output_pdf, bg="grey", fg="black", font=("Helvetica", 12)),
        ]
        self.browse_buttons[0].grid(row=0, column=2, padx=10, pady=6, sticky="w")
        self.browse_buttons[1].grid(row=7, column=2, padx=10, pady=6, sticky="w")
        self.browse_buttons[2].grid(row=8, column=2, padx=10, pady=6, sticky="w")

        offset_chk = tk.Checkbutton(
            self,
            text="Use 20-nt left-flank offset (take last N nt between flanks)",
            variable=self.use_offset,
            bg="black", fg="white", selectcolor="black",
            activebackground="black", activeforeground="white",
            font=("Helvetica", 11),
        )
        offset_chk.grid(row=10, column=0, columnspan=3, padx=10, pady=4, sticky="w")

        self.process_button = tk.Button(
            self,
            text="Process Barcodes",
            command=self.process_all_pairs,
            bg="#16a34a",
            fg="white",
            font=("Helvetica", 13, "bold"),
        )
        self.process_button.grid(row=11, column=0, columnspan=3, padx=10, pady=12, sticky="ew")

    def center_widgets(self):
        for i in range(12):
            self.grid_rowconfigure(i, weight=1)
        for c in range(3):
            self.grid_columnconfigure(c, weight=1)

    def browse_file(self):
        p = filedialog.askopenfilename()
        if p:
            self.labels_and_entries[0][1].delete(0, tk.END)
            self.labels_and_entries[0][1].insert(0, p)

    def browse_output_txt(self):
        p = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if p:
            self.labels_and_entries[7][1].delete(0, tk.END)
            self.labels_and_entries[7][1].insert(0, p)

    def browse_output_pdf(self):
        p = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if p:
            self.labels_and_entries[8][1].delete(0, tk.END)
            self.labels_and_entries[8][1].insert(0, p)

    def process_all_pairs(self):
        try:
            file_path = self.labels_and_entries[0][1].get()
            start_text = self.labels_and_entries[3][1].get()
            end_text = self.labels_and_entries[4][1].get()
            expected_len = int(self.labels_and_entries[5][1].get())
            length_threshold = expected_len + 5
            distance_threshold = int(self.labels_and_entries[6][1].get())
            output_summary_path = self.labels_and_entries[7][1].get()
            output_pdf_path = self.labels_and_entries[8][1].get()
            plate_ids_text = self.labels_and_entries[9][1].get("1.0", tk.END).strip()
            rows = [r for r in self.labels_and_entries[1][1].get("1.0", tk.END).strip().split("\n") if r]
            columns = [c for c in self.labels_and_entries[2][1].get("1.0", tk.END).strip().split("\n") if c]
            use_offset = bool(self.use_offset.get())

            if plate_ids_text:
                process_all_pairs_multiple(
                    output_summary_path, output_pdf_path, file_path,
                    start_text, end_text, length_threshold, distance_threshold,
                    [p for p in plate_ids_text.split("\n") if p], rows, columns,
                    use_offset=use_offset, expected_len=expected_len,
                )
            else:
                with open(file_path) as fin:
                    process_single_plate_for_reads(
                        output_summary_path, output_pdf_path, fin.readlines(),
                        start_text, end_text, length_threshold, distance_threshold,
                        rows, columns,
                        use_offset=use_offset, expected_len=expected_len,
                    )

            messagebox.showinfo(
                "Processing Result",
                f"Done. Results saved to:\n  {output_summary_path}\n  {output_pdf_path}",
            )
        except Exception as e:
            messagebox.showerror("Error", str(e))
