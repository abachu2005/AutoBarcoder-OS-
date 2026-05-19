import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

class DiagnosticsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Barcode Diagnostics")
        self.geometry("800x700")
        self.configure(bg='black')
        self.create_widgets()
        self.grid_columnconfigure(1, weight=1)

    def create_widgets(self):
        label_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white'}
        entry_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white', 'insertbackground': 'white'}
        text_style = {'font': ('Helvetica', 12), 'bg': 'black', 'fg': 'white'}

        # Input file
        tk.Label(self, text="Sequencing Data (.fastq or .txt):", **label_style).grid(row=0, column=0, sticky='e', padx=10, pady=5)
        self.file_entry = tk.Entry(self, **entry_style)
        self.file_entry.grid(row=0, column=1, sticky='ew', padx=10, pady=5)
        tk.Button(self, text="Browse", command=self.browse_file, bg='grey', fg='black').grid(row=0, column=2, padx=10)

        # Row barcodes
        tk.Label(self, text="Row Barcodes (one per line):", **label_style).grid(row=1, column=0, sticky='ne', padx=10, pady=5)
        self.rows_text = tk.Text(self, height=5, **text_style)
        self.rows_text.grid(row=1, column=1, columnspan=2, sticky='ew', padx=10, pady=5)

        # Column barcodes
        tk.Label(self, text="Column Barcodes (one per line):", **label_style).grid(row=2, column=0, sticky='ne', padx=10, pady=5)
        self.cols_text = tk.Text(self, height=5, **text_style)
        self.cols_text.grid(row=2, column=1, columnspan=2, sticky='ew', padx=10, pady=5)

        # Flanks
        tk.Label(self, text="Flanking Sequence 1:", **label_style).grid(row=3, column=0, sticky='e', padx=10, pady=5)
        self.flank1_entry = tk.Entry(self, **entry_style)
        self.flank1_entry.grid(row=3, column=1, sticky='ew', padx=10, pady=5)
        tk.Label(self, text="Flanking Sequence 2:", **label_style).grid(row=4, column=0, sticky='e', padx=10, pady=5)
        self.flank2_entry = tk.Entry(self, **entry_style)
        self.flank2_entry.grid(row=4, column=1, sticky='ew', padx=10, pady=5)

        # Run button
        tk.Button(self, text="Run Diagnostics", command=self.run_diagnostics, bg='green', fg='white', font=('Helvetica', 12)).grid(row=5, column=0, columnspan=3, pady=10)

        # Output area
        tk.Label(self, text="Diagnostics Output:", **label_style).grid(row=6, column=0, sticky='nw', padx=10)
        self.output_area = scrolledtext.ScrolledText(self, height=20, **text_style)
        self.output_area.grid(row=6, column=1, columnspan=2, sticky='nsew', padx=10, pady=5)
        self.grid_rowconfigure(6, weight=1)

    def browse_file(self):
        path = filedialog.askopenfilename(filetypes=[("FASTQ or text files", "*.fastq *.txt"), ("All files","*.*")])
        if path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, path)

    def run_diagnostics(self):
        file_path = self.file_entry.get().strip()
        rows = [r.strip() for r in self.rows_text.get("1.0", tk.END).splitlines() if r.strip()]
        cols = [c.strip() for c in self.cols_text.get("1.0", tk.END).splitlines() if c.strip()]
        flank1 = self.flank1_entry.get().strip()
        flank2 = self.flank2_entry.get().strip()

        if not (file_path and rows and cols and flank1 and flank2):
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        # Initialize counters
        counts = {
            'rows': {r:0 for r in rows},
            'cols': {c:0 for c in cols},
            'flank1':0,
            'flank2':0,
            'both_flanks':0,
            'row_col_any':0,
            'row_col_combo':{(r,c):0 for r in rows for c in cols},
            'row_col_flanks':{(r,c):0 for r in rows for c in cols},
        }

        total_lines = 0
        with open(file_path) as f:
            for line in f:
                total_lines += 1
                has_row = False
                has_col = False
                for r in rows:
                    if r in line:
                        counts['rows'][r] += 1
                        has_row = True
                for c in cols:
                    if c in line:
                        counts['cols'][c] += 1
                        has_col = True
                if flank1 in line:
                    counts['flank1'] += 1
                if flank2 in line:
                    counts['flank2'] += 1
                if flank1 in line and flank2 in line:
                    counts['both_flanks'] += 1
                if has_row and has_col:
                    counts['row_col_any'] += 1
                for r in rows:
                    for c in cols:
                        if r in line and c in line:
                            counts['row_col_combo'][(r,c)] += 1
                            if flank1 in line and flank2 in line:
                                counts['row_col_flanks'][(r,c)] += 1

        # Build report
        report = []
        report.append(f"Total lines processed: {total_lines}\n")
        report.append("Row barcode occurrences:")
        for r, ct in counts['rows'].items(): report.append(f"  {r}: {ct}")
        report.append("\nColumn barcode occurrences:")
        for c, ct in counts['cols'].items(): report.append(f"  {c}: {ct}")
        report.append(f"\nFlank1 ('{flank1}') occurrences: {counts['flank1']}")
        report.append(f"Flank2 ('{flank2}') occurrences: {counts['flank2']}")
        report.append(f"Both flanks in same line: {counts['both_flanks']}\n")
        report.append(f"Lines with any row+column: {counts['row_col_any']}\n")
        report.append("Per-row/column combination:")
        for (r,c), ct in counts['row_col_combo'].items(): report.append(f"  {r} + {c}: {ct}")
        report.append("\nPer-combo with both flanks:")
        for (r,c), ct in counts['row_col_flanks'].items(): report.append(f"  {r} + {c} + both flanks: {ct}")

        self.output_area.delete('1.0', tk.END)
        self.output_area.insert(tk.END, "\n".join(report))

if __name__ == '__main__':
    app = DiagnosticsApp()
    app.mainloop()
