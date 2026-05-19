# processing.py
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

from .clustering import replace_long_sequences, cluster_barcodes, reprint_with_common_barcodes, most_common_barcodes
from .analysis import analyze_barcodes
from .reading import allocate_reads_by_plate
import os
import glob
import pandas as pd

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
                    # ---- Prism-friendly CSV export for specific wells (R1C1 and R5C3) ----
                    well_id = f"R{row_idx + 1}C{col_idx + 1}"
                    if well_id in {"R1C1", "R5C3"}:
                        prism_dir = os.path.join(os.path.dirname(output_pdf_path), "prism_ready")
                        os.makedirs(prism_dir, exist_ok=True)

                        # Ensure we have simple Python lists, even if "labels, percentages" came from zip()
                        lbls = list(labels)
                        vals = [float(v) for v in list(percentages)]

                        # (A) Wide format (recommended for Prism "Column" → Bar graph):
                        #     Each barcode becomes a column; first row holds the percentage.
                        wide_df = pd.DataFrame([vals], columns=[str(x) for x in lbls])
                        wide_csv = os.path.join(prism_dir, f"{well_id}__barplot_wide.csv")
                        wide_df.to_csv(wide_csv, index=False)

                        # (B) Long format (fallback for Prism import wizard as a single Y column):
                        #     Two columns: Barcode, Percentage. You can map "Barcode" to row titles.
                        long_df = pd.DataFrame({"Barcode": [str(x) for x in lbls], "Percentage": vals})
                        long_csv = os.path.join(prism_dir, f"{well_id}__barplot_long.csv")
                        long_df.to_csv(long_csv, index=False)
                    # ----------------------------------------------------------------------

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
