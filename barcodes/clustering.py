# clustering.py
from collections import Counter

import Levenshtein as lev
import networkx as nx


def replace_long_sequences(barcodes, length_threshold):
    short_sequences = [barcode for barcode in barcodes if len(barcode) <= length_threshold]
    long_sequences = [barcode for barcode in barcodes if len(barcode) > length_threshold]

    replaced_sequences = []
    for long_seq in long_sequences:
        replaced = False
        for short_seq in short_sequences:
            if short_seq in long_seq:
                replaced_sequences.append(short_seq)
                replaced = True
                break
        if not replaced:
            replaced_sequences.append(long_seq)

    return short_sequences + replaced_sequences

def cluster_barcodes(barcodes, distance_threshold):
    G = nx.Graph()
    for barcode in barcodes:
        G.add_node(barcode)

    for i, barcode1 in enumerate(barcodes):
        for j in range(i + 1, len(barcodes)):
            barcode2 = barcodes[j]
            if lev.distance(barcode1, barcode2) <= distance_threshold:
                G.add_edge(barcode1, barcode2)

    clusters = list(nx.connected_components(G))
    return clusters

def most_common_barcodes(cluster, n=3):
    return Counter(cluster).most_common(n)

def reprint_with_common_barcodes(original_barcodes, clusters):
    barcode_to_cluster = {}
    cluster_list = []

    for cluster in clusters:
        for barcode in cluster:
            barcode_to_cluster[barcode] = cluster

    for original_barcode in original_barcodes:
        if original_barcode in barcode_to_cluster:
            cluster_list.append((barcode_to_cluster[original_barcode], original_barcode))
        else:
            cluster_list.append((set(), original_barcode))

    return cluster_list
