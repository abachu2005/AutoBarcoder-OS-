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
