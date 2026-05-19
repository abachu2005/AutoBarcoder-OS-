"""End-to-end test against the bundled sample dataset."""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def sample():
    cfg = json.loads((ROOT / "sample_data" / "sample_config.json").read_text())
    reads = (ROOT / "sample_data" / "sample_reads.txt").read_text().splitlines(keepends=True)
    return cfg, reads


def test_extract_barcode_basic():
    from barcodes.processing import _extract_barcode
    line = "NNNROWNNNCAGCTGAATGTTTAGGATCCNNCOLNN"
    seq = _extract_barcode(line, "CAGCTG", "GGATCC")
    assert seq == "AATGTTTA"


def test_extract_barcode_offset_returns_last_n():
    from barcodes.processing import _extract_barcode
    line = "...CAGCTGXXXXXXXXXXXXXXXXXXXXAATGTTTAGGATCC..."
    seq = _extract_barcode(line, "CAGCTG", "GGATCC", expected_len=8, use_offset=True)
    assert seq == "AATGTTTA"


def test_sample_dataset_end_to_end(sample, tmp_path):
    from barcodes.processing import process_single_plate_for_reads
    cfg, reads = sample
    results = process_single_plate_for_reads(
        str(tmp_path / "summary.txt"),
        str(tmp_path / "results.pdf"),
        reads,
        cfg["start_text"], cfg["end_text"],
        cfg["expected_len"] + 5, cfg["distance_threshold"],
        cfg["rows"], cfg["columns"],
        expected_len=cfg["expected_len"],
    )
    assert len(results) == 16
    assert sum(1 for w in results if not w["contaminated"]) >= 15
    assert (tmp_path / "summary.txt").exists()
    assert (tmp_path / "results.pdf").stat().st_size > 1000
