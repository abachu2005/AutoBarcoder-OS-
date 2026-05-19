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
