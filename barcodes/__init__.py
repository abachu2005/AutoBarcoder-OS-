"""AutoBarcoder core analysis package."""
from .processing import (
    process_barcodes_for_reads,
    process_single_plate_for_reads,
    process_all_pairs_multiple,
)
from .reading import read_barcodes_from_merged, allocate_reads_by_plate
from .clustering import cluster_barcodes, most_common_barcodes
from .analysis import analyze_barcodes

__all__ = [
    "process_barcodes_for_reads",
    "process_single_plate_for_reads",
    "process_all_pairs_multiple",
    "read_barcodes_from_merged",
    "allocate_reads_by_plate",
    "cluster_barcodes",
    "most_common_barcodes",
    "analyze_barcodes",
]

__version__ = "1.0.0"
