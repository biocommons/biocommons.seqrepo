# ensembl-dup-ids

## Summary

While building [SeqRepo](https://github.com/biocommons/seqrepo), a database of
sequences used as reference sequences for variant representation, it was noted
that some *versioned* ENST ids referred to distinct sequences. If widespread,
this would make it impossible to rely on versioned ENST ids as stable sequence
identifiers.

This repo investigates the extent of this degeneracy by checking human GRCh38
cds and cdna FASTA from Ensembl releases 83–116. Earlier releases are
excluded because their FASTA deflines have only unversioned ids.

Three origins of degeneracy are observed:

- In Ensembl's FASTA files, the cdna and cds files for a release use the same
  identifier for both sequence types.

- Across releases, 1 ENST id (of 655,076 cdna sequence ids) referred to more
  than one sequence. (This id is also among the 252 cds ids below.)

- Across releases, 252 ENST ids (of 561,410 cds sequence ids) referred to more
  than one sequence.

On one hand, the observed ambiguity is unlikely to create real-world problems in
variant interpretation. On the other hand, it does mean that tools like SeqRepo
need to account for the fact that the mapping is not unique, which in turn has
implications for the design of database constraints.

## Results

- **Within a release:** no id maps to more than one sequence of a given type.
  (cds and cdna share ids by design.)
- **Across releases:** 252 of 561,410 cds ids and 1 of 655,076 cdna ids map
  to two distinct sequences; none maps to more than two. Changes cluster in
  releases 85/88 and 106–109.
- **Nature of the changes:** for 251 of the 252 cds ids, the cdna sequence is
  unchanged — the CDS was re-annotated without a corresponding version bump
  in the cdna. Most changes are at the 5′ end (start-codon moves, nearly all
  in frame); others replace the CDS wholesale or add/remove a 3′ stop codon.
- **Reversion:** one id, `ENST00000635818.1` (cds), switches A→B→A
  (B in releases 88–91: stop codon dropped, then restored).

Digests are truncated to 15 base64url characters (90 bits); collision risk at
this scale is negligible.

## Method

1. Download cds and cdna FASTA for each release.
2. Compute `ga4gh:SQ` (sha512t24u) digests per record with
   `fasta-sequence-digest`, which normalizes like `bioutils` (strip
   whitespace and `*`, uppercase).
3. Load `(release, seqtype, enst_id, digest)` into DuckDB and query.
4. For ids with more than one digest, extract the sequences on either side of
   the change (`compare.py`) and classify the difference by shared prefix and
   suffix length.

## Requirements

- `wget`, `zsh`, GNU make
- `duckdb` CLI (tested with 1.5 and 2.0)
- `fasta-sequence-digest` (Rust; `~/projects/reece/fasta-sequence-digest`,
  install with `cargo install --path .`)
- Python 3 (stdlib only)
- ~4 GB disk

## Usage

```sh
make -j6 dl && make -j8 vrsids && make uniqueness classify
```

| target | does |
|---|---|
| `dl` | download FASTA for all releases |
| `vrsids` | compute per-file `.vrsids` (digest, id) |
| `default`, `enst.duckdb` | load all `.vrsids` into `enst.duckdb` |
| `uniqueness` | run uniqueness queries |
| `changed-digests.tsv` | digests and release ranges for ids with >1 digest |
| `changed-pairs.tsv` | before/after sequence comparison per changed id |
| `classify` | summarize changes by kind (5′ end, 3′ end, both ends) |
| `clean` | remove `enst.duckdb` and `changed-*.tsv` |
| `cleanest` | also remove per-file `.vrsids` |

## Files

- `Makefile` — pipeline
- `compare.py` — extract and diff before/after sequences for changed ids
- `sql/load.sql` — build the `enst` table
- `sql/uniqueness.sql` — uniqueness, reversion, and gap queries
- `sql/changed-digests.sql` — export changed ids for `compare.py`
- `sql/classify.sql` — classify changes

## Open questions

- 13 cds and 98 cdna ids are absent from one or more intermediate releases
  and then reappear; not yet examined.
- Why changes cluster in releases 85/88 and 106–109 is unknown.
