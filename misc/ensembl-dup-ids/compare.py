"""Compare before/after sequences for ENST ids whose digest changed.

usage: python3 -I compare.py changed-digests.tsv ftp.ensembl.org > changed-pairs.tsv
"""

import csv
import gzip
import sys
from collections import defaultdict
from itertools import groupby
from pathlib import Path


def read_fasta(path, wanted):
    seqs, id_, buf = {}, None, []
    with gzip.open(path, "rt") as fh:
        for line in fh:
            if line.startswith(">"):
                if id_ in wanted:
                    seqs[id_] = "".join(buf).upper()
                id_, buf = line[1:].split()[0], []
            else:
                buf.append(line.strip())
    if id_ in wanted:
        seqs[id_] = "".join(buf).upper()
    return seqs


def common_prefix(a, b):
    n = 0
    for x, y in zip(a, b, strict=False):
        if x != y:
            break
        n += 1
    return n


def main(digests_path, root):
    with Path(digests_path).open() as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    pairs = []  # (seqtype, id, old_release, new_release)
    for (st, id_), grp in groupby(rows, key=lambda r: (r["seqtype"], r["enst_id"])):
        old, new = sorted(grp, key=lambda r: int(r["rmin"]))
        pairs.append((st, id_, int(old["rmax"]), int(new["rmin"])))

    need = defaultdict(set)  # (seqtype, release) -> ids
    for st, id_, ro, rn in pairs:
        need[st, ro].add(id_)
        need[st, rn].add(id_)
    seqs = {}
    for (st, rel), ids in sorted(need.items()):
        path = (
            f"{root}/pub/release-{rel}/fasta/homo_sapiens/{st}/Homo_sapiens.GRCh38.{st}.all.fa.gz"
        )
        for id_, s in read_fasta(path, ids).items():
            seqs[st, rel, id_] = s

    w = csv.writer(sys.stdout, delimiter="\t", lineterminator="\n")
    w.writerow([
        "seqtype",
        "enst_id",
        "old_rel",
        "new_rel",
        "old_len",
        "new_len",
        "delta",
        "prefix",
        "suffix",
        "old_mid",
        "new_mid",
    ])
    for st, id_, ro, rn in pairs:
        a, b = seqs[st, ro, id_], seqs[st, rn, id_]
        p = common_prefix(a, b)
        s = common_prefix(a[p:][::-1], b[p:][::-1])  # suffix, not overlapping prefix
        # differing middle segments, truncated for display
        am, bm = a[p : len(a) - s], b[p : len(b) - s]
        w.writerow([
            st,
            id_,
            ro,
            rn,
            len(a),
            len(b),
            len(b) - len(a),
            p,
            s,
            am[:40] or "-",
            bm[:40] or "-",
        ])


if __name__ == "__main__":
    main(*sys.argv[1:])
