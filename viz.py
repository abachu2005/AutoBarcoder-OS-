# viz_prism.py — 5 clusters, tight center layout, bigger nodes,
# intra-cluster edges visible, no-overlap, and crisp labels on top.

from collections import Counter, defaultdict
from typing import List, Dict, Tuple

import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.lines as mlines
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from matplotlib import patheffects as pe

import networkx as nx
import numpy as np

# ============================== Prism Style (bigger/clearer) ==============================

PRISM_FONT_FAMILY   = "Arial"
PRISM_BASE_FONTSIZE = 12
PRISM_TITLE_SIZE    = 22
PRISM_LABEL_SIZE    = 12
PRISM_NODE_TEXT_MAX = 15
PRISM_NODE_TEXT_MIN = 6

PRISM_BLACK         = "#000000"
PRISM_GRAY_MED      = "#666666"  # darker so intra-cluster edges are clearly visible
PRISM_GRAY_LIGHT    = "#b8b8b8"
PRISM_WHITE         = "#FFFFFF"

PRISM_BOX_LW        = 2.8
PRISM_NODE_EDGE_LW  = 2.2
PRISM_META_LINE_LW  = 1.8
PRISM_INTRA_EDGE_LW = 2.0

mpl.rcParams.update({
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "font.family": PRISM_FONT_FAMILY,
    "font.sans-serif": [PRISM_FONT_FAMILY, "Helvetica", "Liberation Sans", "DejaVu Sans", "sans-serif"],
    "font.size": PRISM_BASE_FONTSIZE,
    "font.weight": "bold",
    "text.color": PRISM_BLACK,
    "figure.facecolor": PRISM_WHITE,
    "axes.facecolor": PRISM_WHITE,
    "axes.edgecolor": PRISM_BLACK,
})

GRAPH_PAD_GREYS = [
    "#f2f2f2", "#eaeaea", "#e2e2e2", "#dadada",
    "#d2d2d2", "#cacaca", "#c2c2c2", "#bababa",
    "#b2b2b2", "#aaaaaa", "#a2a2a2", "#9a9a9a",
]

_FP = FontProperties(family=PRISM_FONT_FAMILY, weight="bold")

# ===================== Edit distance =====================

try:
    import Levenshtein as lev
    def edit_distance(a, b): return lev.distance(a, b)
except Exception:
    def edit_distance(a: str, b: str) -> int:
        la, lb = len(a), len(b)
        dp = list(range(lb + 1))
        for i in range(1, la + 1):
            prev, dp[0] = dp[0], i
            ai = a[i-1]
            for j in range(1, lb + 1):
                cur = dp[j]
                cost = 0 if ai == b[j-1] else 1
                dp[j] = min(dp[j] + 1, dp[j-1] + 1, prev + cost)
                prev = cur
        return dp[-1]

# ========================= Crafted dataset (5 clusters; clear dominant + variants) =========================

def _sub(s: str, pos: int, ch: str) -> str:
    i = pos - 1
    if s[i] == ch: return s
    return s[:i] + ch + s[i+1:]

SEEDS_ORDERED = ["ACGTACGT", "TGCATGCA", "AACCGGTT", "TTCCAAGG", "CGATCGAT"]

CLUSTERS5_SPEC = {
    "ACGTACGT": {"base_count": 10, "variants": [(2,"A",2),(4,"C",2),(7,"A",2),(8,"A",2)]},      # ~18
    "TGCATGCA": {"base_count": 9,  "variants": [(3,"T",2),(5,"C",2),(1,"A",2),(8,"T",1)]},      # ~16
    "AACCGGTT": {"base_count": 11, "variants": [(1,"G",2),(3,"A",2),(8,"A",2),(5,"T",1)]},      # ~18
    "TTCCAAGG": {"base_count": 8,  "variants": [(2,"A",3),(5,"G",3),(7,"C",3),(1,"C",1)]},      # ~18
    "CGATCGAT": {"base_count": 9,  "variants": [(2,"T",3),(4,"A",3),(1,"A",1),(8,"C",1)]},      # ~17
}

def build_dataset_5() -> List[str]:
    data: List[str] = []
    for base in SEEDS_ORDERED:
        spec = CLUSTERS5_SPEC[base]
        data.extend([base] * spec["base_count"])
        for pos, ch, n in spec["variants"]:
            data.extend([_sub(base, pos, ch)] * n)
    return data

# ========================= Graph (each node = one occurrence) =========================

def build_graph_with_occurrences(barcodes: List[str], distance_threshold: int):
    per_label_idx = defaultdict(int)
    nodes: List[Tuple[str, int]] = []
    for bc in barcodes:
        per_label_idx[bc] += 1
        nodes.append((bc, per_label_idx[bc]))

    G = nx.Graph()
    for node in nodes:
        seq, _ = node
        G.add_node(node, seq=seq)

    for i in range(len(nodes)):
        si = G.nodes[nodes[i]]["seq"]
        for j in range(i + 1, len(nodes)):
            sj = G.nodes[nodes[j]]["seq"]
            d = edit_distance(si, sj)
            if d <= distance_threshold:
                G.add_edge(nodes[i], nodes[j], weight=1.0/(1 + d))
    clusters = list(nx.connected_components(G))
    return G, clusters

# ========================= Core + ring layout (dominant mini-cluster) =========================

def _circle_positions(n: int, radius: float, theta0: float = 0.0) -> List[Tuple[float,float]]:
    if n == 1:
        return [(0.0, 0.0)]
    return [(radius*np.cos(theta0 + 2*np.pi*k/n),
             radius*np.sin(theta0 + 2*np.pi*k/n)) for k in range(n)]

def min_pairwise_dist(coords: np.ndarray) -> float:
    n = len(coords)
    if n <= 1: return np.inf
    md = np.inf
    for i in range(n):
        for j in range(i+1, n):
            d = np.hypot(coords[i,0]-coords[j,0], coords[i,1]-coords[j,1])
            if d < md: md = d
    return md

def _enforce_min_sep(pos: Dict, min_sep: float) -> Dict:
    """Scale positions radially around their centroid until min pairwise distance >= min_sep."""
    keys = list(pos.keys())
    pts = np.array([pos[k] for k in keys], dtype=float)
    ctr = pts.mean(axis=0)
    pts -= ctr
    for _ in range(80):
        cur = min_pairwise_dist(pts)
        if not np.isfinite(cur) or cur >= min_sep:
            break
        scale = (min_sep / max(cur, 1e-9)) * 1.08
        pts *= scale
    pts += ctr
    return {k: (float(pts[i,0]), float(pts[i,1])) for i, k in enumerate(keys)}

def layout_core_and_rings(H: nx.Graph,
                          dominant_label: str,
                          sep_core: float = 0.80,     # spacing inside dominant mini-cluster
                          sep_ring: float = 1.05,     # spacing among ring nodes
                          gap_core_to_ring: float = 1.10,
                          min_sep_units: float = 1.20  # strict no-overlap guard
                          ) -> Dict:
    nodes = list(H.nodes())
    seqs = {n: H.nodes[n]["seq"] for n in nodes}
    core_nodes = [n for n in nodes if seqs[n] == dominant_label]
    ring_nodes = [n for n in nodes if seqs[n] != dominant_label]

    n_core = len(core_nodes)
    R_core = 0.0 if n_core <= 1 else max(0.42, (n_core * sep_core) / (2*np.pi))
    core_xy = _circle_positions(n_core, R_core, theta0=np.pi/12)

    n_ring = len(ring_nodes)
    pos = {}

    R1_min = R_core + gap_core_to_ring
    if n_ring <= 0:
        for n, (x,y) in zip(core_nodes, core_xy):
            pos[n] = (x, y)
        return _enforce_min_sep(pos, min_sep_units)

    R1 = max(R1_min, (n_ring * sep_ring) / (2*np.pi))
    if n_ring <= 14:
        ring1_xy = _circle_positions(n_ring, R1, theta0=-np.pi/18)
        for n, (x,y) in zip(core_nodes, core_xy): pos[n] = (x, y)
        for n, (x,y) in zip(ring_nodes, ring1_xy): pos[n] = (x, y)
        return _enforce_min_sep(pos, min_sep_units)

    # Two rings if many variants
    n1 = int(np.ceil(n_ring/2))
    n2 = n_ring - n1
    R2 = R1 + 1.00
    ring1_xy = _circle_positions(n1, R1, theta0=-np.pi/18)
    ring2_xy = _circle_positions(n2, R2, theta0=np.pi/18)

    for n, (x,y) in zip(core_nodes, core_xy): pos[n] = (x, y)
    for n, (x,y) in zip(ring_nodes[:n1], ring1_xy): pos[n] = (x, y)
    for n, (x,y) in zip(ring_nodes[n1:], ring2_xy): pos[n] = (x, y)

    return _enforce_min_sep(pos, min_sep_units)

# ========================= Text sizing & drawing (labels on top) =========================

def _measure_text_multiline(lines: List[str], fs: int) -> Tuple[float, float]:
    widths = []; heights = []
    for s in lines:
        tp = TextPath((0, 0), s, size=fs, prop=_FP)
        bb = tp.get_extents()
        widths.append(bb.width); heights.append(bb.height)
    line_gap = 0.15 * fs
    total_height = sum(heights) + line_gap * (len(lines) - 1 if len(lines) > 1 else 0)
    max_width = max(widths) if widths else 0.0
    return max_width, total_height

def fit_fontsize_in_circle_multiline(text: str, radius_pt: float,
                                     max_pt: int = PRISM_NODE_TEXT_MAX,
                                     min_pt: int = PRISM_NODE_TEXT_MIN,
                                     pad_pt: float = 3.6):  # extra padding so text never touches border
    usable = max(1.0, radius_pt - pad_pt)
    lines = text.split("\n")
    for fs in range(max_pt, min_pt - 1, -1):
        w, h = _measure_text_multiline(lines, fs)
        if (w <= 2 * usable) and (h <= 2 * usable):
            return fs
    return min_pt

def draw_labels_inside_nodes(ax, positions: Dict, node_size: float,
                             labels: Dict, text_colors: Dict = None, z: int = 6):
    # node_size in NetworkX is points^2 → convert to radius in points
    radius_pt = (float(node_size) / np.pi) ** 0.5
    for n, (x, y) in positions.items():
        text = labels.get(n, str(n))
        fs = fit_fontsize_in_circle_multiline(text, radius_pt, pad_pt=3.6)
        color = (text_colors or {}).get(n, PRISM_BLACK)
        txt = ax.text(
            x, y, text,
            ha="center", va="center",
            fontsize=fs, fontweight="bold",
            fontproperties=_FP, color=color,
            linespacing=1.0, zorder=z
        )
        # Subtle white halo to keep labels readable on any grey
        txt.set_path_effects([pe.withStroke(linewidth=0.8, foreground=PRISM_WHITE)])

# ========================= Rendering (tight center; bigger nodes; edges drawn) =========================

def _dynamic_node_size(n_nodes: int) -> int:
    # bigger nodes, still scale with count
    size = int(4000 - 30 * n_nodes)     # e.g., 18 -> ~3460
    return max(2400, min(size, 4200))   # clamp

def make_cluster_web(
    barcodes: List[str],
    distance_threshold: int = 2,
    layout_seed: int = 7,
    out_png: str = "barcode_clustering_web.png",
    out_jpg: str = "barcode_clustering_web.jpg",
    out_pdf: str = "barcode_clustering_web.pdf",
    dpi_export: int = 900,
):
    G, comps = build_graph_with_occurrences(barcodes, distance_threshold)

    # Stable cluster ordering by seed
    def comp_key(comp: set) -> int:
        labels = {G.nodes[n]["seq"] for n in comp}
        for idx, s in enumerate(SEEDS_ORDERED):
            if s in labels:
                return idx
        return 10_000
    comps.sort(key=comp_key)

    consensus: List[str] = []
    sizes: List[int] = []
    cluster_subgraphs = []
    cluster_pos_rel = []
    cluster_bboxes = []
    node_sizes = []

    for comp in comps:
        nodes = list(comp)
        H = G.subgraph(nodes).copy()

        labels = [H.nodes[n]["seq"] for n in H.nodes()]
        dom = Counter(labels).most_common(1)[0][0]
        consensus.append(dom)
        sizes.append(len(nodes))
        cluster_subgraphs.append(H)

        # Explicit core+ring layout with enforced min separation (no overlaps)
        rel = layout_core_and_rings(H, dom,
                                    sep_core=0.80,
                                    sep_ring=1.05,
                                    gap_core_to_ring=1.10,
                                    min_sep_units=1.20)
        pts = np.array([rel[n] for n in H.nodes()])
        xs, ys = pts[:,0], pts[:,1]
        pad_x, pad_y = 0.60, 0.60   # generous interior padding so clusters look roomy
        hw = (xs.max() - xs.min())/2 + pad_x
        hh = (ys.max() - ys.min())/2 + pad_y
        cluster_pos_rel.append(rel)
        cluster_bboxes.append((hw, hh))

        node_sizes.append(_dynamic_node_size(len(nodes)))

    # Meta: bring clusters toward center (short lines)
    m = len(consensus)
    D = np.zeros((m, m), dtype=int)
    for i in range(m):
        for j in range(i+1, m):
            D[i,j] = D[j,i] = edit_distance(consensus[i], consensus[j])

    M = nx.Graph(); M.add_nodes_from(range(m))
    for i in range(m):
        order = np.argsort(D[i])
        for j in [k for k in order if k != i][:2]:
            a, b = sorted((i, j))
            M.add_edge(a, b, weight=1.0/(1 + D[a,b]))

    meta_pos = nx.spring_layout(M, seed=layout_seed, k=0.6, iterations=450, weight='weight')
    meta_pts = np.array(list(meta_pos.values()))
    meta_pts -= meta_pts.mean(axis=0)
    meta_pts /= (np.abs(meta_pts).max() + 1e-9)
    meta_pts *= 2.6   # tight center, short inter-cluster lines

    centers = {i: np.array((float(meta_pts[i,0]), float(meta_pts[i,1])), dtype=float)
               for i in range(m)}

    # Light de-overlap for boxes (still close)
    for _ in range(200):
        moved = False
        for i in range(m):
            for j in range(i+1, m):
                ci, cj = centers[i], centers[j]
                hw_i, hh_i = cluster_bboxes[i]
                hw_j, hh_j = cluster_bboxes[j]
                dx, dy = cj - ci
                if dx == dy == 0: dx = 1e-3; dy = 0
                req_x = (hw_i + hw_j) + 0.25
                req_y = (hh_i + hh_j) + 0.25
                overlap_x = req_x - abs(dx)
                overlap_y = req_y - abs(dy)
                if overlap_x > 0 and overlap_y > 0:
                    push = np.array([np.sign(dx) * overlap_x * 0.5, np.sign(dy) * overlap_y * 0.5])
                    centers[i] -= push * 0.045
                    centers[j] += push * 0.045
                    moved = True
        if not moved:
            break

    # --- Figure ---
    fig, ax = plt.subplots(figsize=(26, 16), dpi=220)
    fig.set_facecolor(PRISM_WHITE); ax.set_facecolor(PRISM_WHITE)

    # Short, light meta lines (between cluster centers)
    pairs = set()
    for i in range(m):
        order = np.argsort(D[i])
        for j in [k for k in order if k != i][:2]:
            a, b = sorted((i, j))
            pairs.add((a, b))

    centers_tup = {i: (float(centers[i][0]), float(centers[i][1])) for i in range(m)}
    for (i, j) in pairs:
        (x1, y1), (x2, y2) = centers_tup[i], centers_tup[j]
        ax.add_artist(mlines.Line2D([x1, x2], [y1, y2],
                                    color=PRISM_GRAY_LIGHT, linewidth=PRISM_META_LINE_LW,
                                    alpha=1.0, solid_capstyle="butt", zorder=1))

    grey_cycle: List[str] = GRAPH_PAD_GREYS

    # Draw clusters
    for idx, H in enumerate(cluster_subgraphs):
        cx, cy = centers_tup[idx]
        hw, hh = cluster_bboxes[idx]
        rel = cluster_pos_rel[idx]
        node_size = node_sizes[idx]
        fill_hex = grey_cycle[idx % len(grey_cycle)]

        # Cluster box (zorder=2, so edges can be drawn above it)
        rect = patches.FancyBboxPatch(
            (cx - hw, cy - hh), 2*hw, 2*hh,
            boxstyle="round,pad=0.10,rounding_size=0.14",
            linewidth=PRISM_BOX_LW, edgecolor=PRISM_BLACK, facecolor=PRISM_WHITE, zorder=2
        )
        ax.add_patch(rect)

        # Header (explicitly on top)
        title = f"Consensus: {consensus[idx]}   |   n={sizes[idx]}"
        ax.text(cx, cy + hh + 0.60, title, ha="center", va="bottom",
                fontsize=PRISM_LABEL_SIZE, fontweight="bold", color=PRISM_BLACK,
                bbox=dict(boxstyle="round,pad=0.34", facecolor=PRISM_WHITE,
                          edgecolor=PRISM_BLACK, linewidth=1.6), zorder=5)

        # Absolute positions
        pos_shift = {n: (rel[n][0] + cx, rel[n][1] + cy) for n in H.nodes()}

        # ---- Intra-cluster edges (drawn ABOVE the white box; BELOW nodes) ----
        edge_art = nx.draw_networkx_edges(
            H, pos=pos_shift, ax=ax, alpha=1.0,
            width=PRISM_INTRA_EDGE_LW, edge_color=PRISM_GRAY_MED,
        )
        # Ensure zorder=3 even if NetworkX ignores the kwarg
        try:
            arts = edge_art if isinstance(edge_art, (list, tuple)) else [edge_art]
            for a in arts:
                if hasattr(a, "set_zorder"):
                    a.set_zorder(3)
        except Exception:
            pass

        # Nodes (bigger) — drawn atop edges
        node_art = nx.draw_networkx_nodes(
            H, pos_shift,
            nodelist=list(H.nodes()),
            node_size=node_size,
            node_color=fill_hex,
            edgecolors=PRISM_BLACK,
            linewidths=PRISM_NODE_EDGE_LW,
            ax=ax,
        )
        try: node_art.set_zorder(4)
        except Exception: pass

        # Labels on top with halo and padding
        label_map = {n: H.nodes[n]["seq"] for n in H.nodes()}
        draw_labels_inside_nodes(ax, pos_shift, node_size, labels=label_map,
                                 text_colors={n: PRISM_BLACK for n in H.nodes()},
                                 z=6)

    ax.axis("off")
    ax.margins(0.06)
    ax.set_title(
        f"Barcode Clustering (Levenshtein ≤ {distance_threshold}) — each node = one occurrence",
        fontsize=PRISM_TITLE_SIZE, fontweight="bold", pad=18, color=PRISM_BLACK
    )

    fig.tight_layout()
    if out_png:
        fig.savefig(out_png, bbox_inches="tight", dpi=dpi_export, facecolor=PRISM_WHITE)
        print(f"Saved {out_png}")
    if out_jpg:
        fig.savefig(out_jpg, bbox_inches="tight", dpi=dpi_export, facecolor=PRISM_WHITE)
        print(f"Saved {out_jpg}")
    if out_pdf:
        fig.savefig(out_pdf, bbox_inches="tight", facecolor=PRISM_WHITE)  # vector export (crisp)
        print(f"Saved {out_pdf}")

    return fig, ax

# ========================= Run =========================

def build_and_render_default():
    dataset = build_dataset_5()
    make_cluster_web(
        dataset,
        distance_threshold=2,
        layout_seed=7,
        out_png="/Users/abhinavbachu/Downloads/barcode_clustering_web.png",
        out_jpg="/Users/abhinavbachu/Downloads/barcode_clustering_web.jpg",
        out_pdf="barcode_clustering_web.pdf",
        dpi_export=900,
    )

if __name__ == "__main__":
    build_and_render_default()
