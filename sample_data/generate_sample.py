"""Generate a tiny synthetic reads file for the AutoBarcoder demo.

Re-run this script to regenerate ``sample_reads.txt`` deterministically. The
configuration matches ``sample_config.json``.
"""
from __future__ import annotations

import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "sample_config.json").read_text())

ALPHA = "ACGT"
SEED = 42


def random_bc(n, rng):
    return "".join(rng.choice(ALPHA) for _ in range(n))


def mutate(bc, n_edits, rng):
    s = list(bc)
    for _ in range(n_edits):
        i = rng.randrange(len(s))
        s[i] = rng.choice([b for b in ALPHA if b != s[i]])
    return "".join(s)


def main():
    rng = random.Random(SEED)
    start, end = CFG["start_text"], CFG["end_text"]
    bc_len = CFG["expected_len"]
    lines = []

    for r_idx, row in enumerate(CFG["rows"]):
        for c_idx, col in enumerate(CFG["columns"]):
            primary = random_bc(bc_len, rng)
            secondary = random_bc(bc_len, rng) if rng.random() < 0.4 else None

            for _ in range(20):
                bc = mutate(primary, rng.choices([0, 1, 2], weights=[8, 2, 1])[0], rng)
                lines.append(f"NNN{row}NNN{start}{bc}{end}NN{col}NN")
            if secondary:
                for _ in range(5):
                    bc = mutate(secondary, rng.choices([0, 1], weights=[8, 2])[0], rng)
                    lines.append(f"NNN{row}NNN{start}{bc}{end}NN{col}NN")

    rng.shuffle(lines)
    (HERE / "sample_reads.txt").write_text("\n".join(lines) + "\n")
    print(f"Wrote {len(lines)} reads to sample_reads.txt")


if __name__ == "__main__":
    main()
