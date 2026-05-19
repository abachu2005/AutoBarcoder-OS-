"""Unit tests for the clustering primitives."""
from barcodes.clustering import (
    cluster_barcodes,
    most_common_barcodes,
    replace_long_sequences,
    reprint_with_common_barcodes,
)


def test_replace_long_sequences_keeps_short():
    bcs = ["AAAA", "TTTT", "AAAAGGGG", "AAAA"]
    out = replace_long_sequences(bcs, length_threshold=4)
    assert out.count("AAAA") == 3
    assert "AAAAGGGG" not in out


def test_cluster_barcodes_groups_within_edit_distance():
    bcs = ["AAAA", "AAAT", "AAAG", "CCCC", "CCCT"]
    clusters = cluster_barcodes(bcs, distance_threshold=1)
    sizes = sorted(len(c) for c in clusters)
    assert sizes == [2, 3]


def test_most_common_barcodes():
    out = most_common_barcodes(["A", "A", "B", "A", "B", "C"], n=2)
    assert out[0] == ("A", 3)
    assert out[1] == ("B", 2)


def test_reprint_with_common_barcodes_preserves_order():
    clusters = [{"AAAA", "AAAT"}, {"CCCC"}]
    pairs = reprint_with_common_barcodes(["AAAA", "AAAT", "CCCC", "AAAA"], clusters)
    assert [p[1] for p in pairs] == ["AAAA", "AAAT", "CCCC", "AAAA"]
