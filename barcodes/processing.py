"""Per-well barcode extraction, clustering, and plate-level report generation."""
from collections import defaultdict
import os
import glob

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd

from .clustering import (
    replace_long_sequences,
    cluster_barcodes,
    reprint_with_common_barcodes,
    most_common_barcodes,
)
from .analysis import analyze_barcodes
from .reading import allocate_reads_by_plate


def _extract_barcode(line, start_text, end_text, expected_len=None, use_offset=False):
    """Pull the substring between ``start_text`` and ``end_text``.

    When ``use_offset`` is True and ``expected_len`` is set, return only the
    *last* ``expected_len`` characters of that interval (skips a filler region
    immediately after the left flank — common in some library designs).
    """
    start_index = line.find(start_text)
    if start_index == -1:
        return None
    start_index += len(start_text)
    end_index = line.find(end_text, start_index)
    if end_index == -1:
        return None
    seq = line[start_index:end_index]
    if use_offset and expected_len and len(seq) >= expected_len:
        return seq[-expected_len:]
    return seq


def process_barcodes_for_reads(
    reads,
    word1,
    word2,
    start_text,
    end_text,
    length_threshold,
    distance_threshold,
    use_offset=False,
    expected_len=None,
):
    barcodes = []
    for line in reads:
        if word1 in line and word2 in line:
            seq = _extract_barcode(line, start_text, end_text, expected_len, use_offset)
            if seq is not None:
                barcodes.append(seq)

    barcodes = replace_long_sequences(barcodes, length_threshold)
    clusters = cluster_barcodes(barcodes, distance_threshold)
    clustered_barcodes = reprint_with_common_barcodes(barcodes, clusters)

    cluster_dict = defaultdict(list)
    for cluster, barcode in clustered_barcodes:
        cluster_dict[frozenset(cluster)].append(barcode)

    all_common_barcodes = []
    for _cluster, barcodes_in_cluster in cluster_dict.items():
        top = most_common_barcodes(barcodes_in_cluster, 1)
        if not top:
            continue
        consensus = top[0][0]
        for _ in barcodes_in_cluster:
            all_common_barcodes.append(f"G{consensus}")

    return analyze_barcodes(all_common_barcodes, top_n=3)


def process_single_plate_for_reads(
    output_summary_path,
    output_pdf_path,
    reads,
    start_text,
    end_text,
    length_threshold,
    distance_threshold,
    rows,
    columns,
    use_offset=False,
    expected_len=None,
    prism_export_wells=None,
    progress_cb=None,
):
    """Process one 96-well plate and write a per-well TXT summary + PDF chart.

    ``prism_export_wells`` (e.g. ``{"R1C1", "R5C3"}``) optionally writes
    GraphPad-Prism-friendly CSVs into ``<output_dir>/prism_ready/``.
    ``progress_cb`` (callable taking ``(done, total)``) lets a UI poll progress.
    """
    array_2d = [[(rows[i], columns[j]) for j in range(len(columns))] for i in range(len(rows))]
    total_wells = sum(len(r) for r in array_2d)
    processed_pairs = 0
    output_lines = []
    well_results = []

    with PdfPages(output_pdf_path) as pdf:
        for row_idx in range(len(array_2d)):
            for col_idx in range(len(array_2d[row_idx])):
                word1, word2 = array_2d[row_idx][col_idx]
                well_id = f"R{row_idx + 1}C{col_idx + 1}"
                pct = process_barcodes_for_reads(
                    reads,
                    word1,
                    word2,
                    start_text,
                    end_text,
                    length_threshold,
                    distance_threshold,
                    use_offset=use_offset,
                    expected_len=expected_len,
                )

                if not pct:
                    output_lines.append(f"{well_id}: CONTAMINATED (no barcodes)")
                    labels = ["Contaminated"]
                    percentages = [0]
                    well_results.append({"well": well_id, "row_bc": word1, "col_bc": word2,
                                         "contaminated": True, "barcodes": []})
                else:
                    summary = ", ".join(f"{l} ({p:.2f}%)" for l, p in pct)
                    output_lines.append(f"{well_id}: {summary}")
                    labels, percentages = zip(*pct)
                    well_results.append({
                        "well": well_id,
                        "row_bc": word1,
                        "col_bc": word2,
                        "contaminated": False,
                        "barcodes": [{"sequence": l, "percentage": float(p)} for l, p in pct],
                    })

                    if prism_export_wells and well_id in prism_export_wells:
                        prism_dir = os.path.join(os.path.dirname(output_pdf_path) or ".", "prism_ready")
                        os.makedirs(prism_dir, exist_ok=True)
                        lbls = list(labels)
                        vals = [float(v) for v in list(percentages)]
                        pd.DataFrame([vals], columns=[str(x) for x in lbls]).to_csv(
                            os.path.join(prism_dir, f"{well_id}__barplot_wide.csv"), index=False
                        )
                        pd.DataFrame({"Barcode": [str(x) for x in lbls], "Percentage": vals}).to_csv(
                            os.path.join(prism_dir, f"{well_id}__barplot_long.csv"), index=False
                        )

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.bar(labels, percentages, color="#3b82f6")
                ax.set_title(f"{well_id}: {word1} - {word2}")
                ax.set_xlabel("Barcode")
                ax.set_ylabel("Percentage")
                ax.set_ylim(0, 100)
                ax.tick_params(axis="x", labelsize=8)
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)

                processed_pairs += 1
                if progress_cb:
                    progress_cb(processed_pairs, total_wells)
                if processed_pairs >= 96:
                    break
            if processed_pairs >= 96:
                break

    with open(output_summary_path, "w") as f:
        f.write("\n".join(output_lines) + "\n")

    return well_results


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
    columns,
    use_offset=False,
    expected_len=None,
    prism_export_wells=None,
    progress_cb=None,
):
    _wc, _tl, reads_dir = allocate_reads_by_plate(
        file_path, plate_ids, os.path.dirname(output_summary_path) or "."
    )

    all_results = {}
    for plate_file in glob.glob(os.path.join(reads_dir, "*_reads.txt")):
        plate_id = os.path.basename(plate_file).split("_reads.txt")[0]
        print(f"Processing plate {plate_id} from {plate_file}…")
        out_txt = f"{output_summary_path}_Plate_{plate_id}.txt"
        out_pdf = f"{output_pdf_path}_Plate_{plate_id}.pdf"
        with open(plate_file) as f:
            results = process_single_plate_for_reads(
                out_txt,
                out_pdf,
                f.readlines(),
                start_text,
                end_text,
                length_threshold,
                distance_threshold,
                rows,
                columns,
                use_offset=use_offset,
                expected_len=expected_len,
                prism_export_wells=prism_export_wells,
                progress_cb=progress_cb,
            )
        all_results[plate_id] = results
        print(f"Finished plate {plate_id}.")

    return all_results
