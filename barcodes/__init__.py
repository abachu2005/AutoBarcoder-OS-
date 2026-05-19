"""AutoBarcoder core analysis package."""
from .analysis import analyze_barcodes
from .clustering import cluster_barcodes, most_common_barcodes
from .processing import (
    process_all_pairs_multiple,
    process_barcodes_for_reads,
    process_single_plate_for_reads,
)
from .reading import allocate_reads_by_plate, read_barcodes_from_merged

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
