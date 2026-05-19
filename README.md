# AutoBarcoder

> Demultiplex and cluster RNA barcodes from 96-well-plate sequencing reads — in your browser or terminal.

AutoBarcoder takes a pile of sequencing reads, sorts them back into 96 wells using your row/column barcodes, clusters the variable RNA barcode between two flanking sequences, and produces a per-well summary (TXT + PDF) of the top barcode variants. It handles single plates and multi-plate runs.

![status: ready](https://img.shields.io/badge/status-ready-brightgreen) ![python: 3.9+](https://img.shields.io/badge/python-3.9%2B-blue) ![license: MIT](https://img.shields.io/badge/license-MIT-lightgrey) [![DOI](https://zenodo.org/badge/929581836.svg)](https://zenodo.org/badge/latestdoi/929581836) [![CI](https://github.com/abachu2005/AutoBarcoder-OS-/actions/workflows/ci.yml/badge.svg)](https://github.com/abachu2005/AutoBarcoder-OS-/actions/workflows/ci.yml)

---

## What it does

```
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│ Sequencing reads │ → │  Row+Column tag  │ → │  Extract between │ → │  Per-well TXT +  │
│  (FASTQ / TXT)   │   │   demultiplex    │   │  flanks; cluster │   │   PDF + JSON     │
└──────────────────┘   └──────────────────┘   │   by Levenshtein │   └──────────────────┘
                                              └──────────────────┘
```

Inputs you provide:

- Sequencing data (FASTQ or plain-text — every line containing both row & column tags is scanned).
- Row barcodes + column barcodes (one per line).
- 5′ and 3′ flanking sequences that bracket the variable RNA barcode.
- Expected barcode length and a Levenshtein edit-distance tolerance for clustering.

Outputs you get:

- `summary.txt` — per-well top-3 barcodes and percentages.
- `results.pdf` — one bar chart per well.
- JSON results via the web API (programmatic access).
- Optional GraphPad-Prism-friendly CSVs for selected wells.

---

## Quick start (web UI — recommended)

The fastest way to try AutoBarcoder is the new browser UI.

```bash
git clone https://github.com/abachu2005/AutoBarcoder-OS-.git
cd AutoBarcoder-OS-
python3 bin/autobarcoder-setup       # interactive wizard: venv + deps + smoke test
bash webapp/run.sh                   # serve at http://127.0.0.1:8000
```

Then open <http://127.0.0.1:8000> and click **“Try with sample data”** to see a working analysis on a synthetic 4×4 plate.

## Quick start (desktop GUI)

```bash
pip install -r requirements.txt
python main.py
```

The Tkinter app provides the same controls as the web UI in a single window, useful when you can't run a local server.

## Quick start (Python API)

```python
from barcodes.processing import process_single_plate_for_reads

with open("reads.fastq") as f:
    results = process_single_plate_for_reads(
        "summary.txt", "results.pdf", f.readlines(),
        start_text="CAGCTG", end_text="GGATCC",
        length_threshold=25, distance_threshold=2,
        rows=["AAACGT", "AATTGG"], columns=["CCGTAA", "CCGGTT"],
        expected_len=20,
    )
```

---

## Repository layout

```
.
├── barcodes/             # core analysis library (reading, clustering, analysis, processing)
├── gui/                  # Tkinter desktop GUI
├── webapp/               # FastAPI + HTML/JS web UI
│   ├── backend/main.py
│   └── frontend/index.html
├── bin/autobarcoder-setup# interactive setup wizard
├── sample_data/          # tiny synthetic dataset for the demo button
├── viz.py                # publication-style clustering web renderer (standalone)
├── diagnostics.py        # diagnostic motif-counting GUI
├── main.py               # Tkinter launcher
└── requirements.txt
```

## Configuration reference

| Field | Meaning |
|---|---|
| **Sequencing data** | FASTQ or text file. Every line is scanned independently. |
| **Row / Column barcodes** | One per line. A read must contain *both* a row and a column tag to be assigned to a well. |
| **5′ / 3′ flank** | The constant sequences bracketing the variable barcode. |
| **Expected barcode length** | Used internally as `length+5` to allow short insertions during clustering. |
| **Edit tolerance** | Levenshtein distance threshold for grouping similar barcodes into one cluster. |
| **20-nt offset** | If your library has filler between the 5′ flank and the real barcode, enable this to take the *last* N nt between the flanks. |
| **Plate IDs** | Multi-plate mode. Each provided string is treated as a plate-identifier substring; reads are split per plate. |

## Output catalogue

- `summary.txt` — one line per well: `R{row}C{col}: G<seq> (xx.xx%), G<seq> (xx.xx%), …` or `CONTAMINATED (no barcodes)`.
- `results.pdf` — bar chart per well, top 3 clusters.
- `prism_ready/` (if `prism_export_wells` is set in the API) — Wide- and long-format CSVs.
- Web jobs additionally expose JSON at `/api/jobs/{id}/results` and downloadable artifacts.

## License

MIT — see [`LICENSE`](LICENSE).
