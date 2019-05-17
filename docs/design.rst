This document describes the design of the seqrepo package.
It is currently a collection of thoughts during development.
If you find dangling sentences, you should


Goals and design implications
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This section summarizes goals and their architectural implications.

* Space-efficient within a release/snapshot
  ⇒ compress sequences
  ⇒ dedupe sequences ⇒ use hashes
* Space-efficient across releases
  ⇒ use hard links
* Bandwidth-efficient distribution of incremental updates
  ⇒ immutable, journaled add-only sequence storage
* Zero or more namespaced aliases associated with a sequence
  ⇒ store aliases for hashed sequences
* Fast sequence lookup and slicing (random access)
  ⇒ when coupled with compression ⇒ blocked gzip

Space-efficient storage usually means compression.  Conventional
compression precludes random access to files, which, for example,
would necessitate reading an entire chromosome in order to access an
arbitrary region.

Fortunately, the blocked gzip format (`bgzf
<https://samtools.github.io/hts-specs/SAMv1.pdf>`__) enables random
access on compressed files.  The solution implemented here uses
block-gzipped fasta files with access provided by the pysam.FastaFile
module.  Taken together, bgzf and pysam enable compression and fast
random access.

Space efficiency across snapshots is well-served by using hardlinks
across snapshots for sequence files. (Sqlite databases are not
hardlinked.)


Components
!!!!!!!!!!

The biocommons.seqrepo package provides five classes:


FabgzReader, FabgzWriter
@@@@@@@@@@@@@@@@@@@@@@@@

* Provides fast random access to to sequences using block gzipped format (BGZF) 
* On commit, FabgzWriter closes file and creates indicies
* FabgzReader is a thin wrapper around PySAM FastaFile (which provides bgzf reading)


FastaDir
@@@@@@@@

* Key-value store for sequences using immutable and journaled files
* Sqlite db tracks metadata and file location of key values (sequences)

SeqAliasDb
@@@@@@@@@@

* Associates sequence key with "namespaced aliases" (e.g., ensembl-75, ENST00000012432)

SeqRepo
@@@@@@@

* Uses [custom sqeuence hash
  method](https://github.com/biocommons/bioutils/blob/master/bioutils/digests.py#L50)
  to link between sequences in FastaDir and sequence aliases in
  SeqAliasDB

* Parses fasta files for aliases and generates computed hashes

Known reference types: gi, refseq, Ensembl, LRG, GRC, BIC
hashes: SHA1, SHA1/8, SHA256, SHA512, MD5, SEGUID



Filesystem Layout
!!!!!!!!!!!!!!!!!

FS Layout::

  /opt/seqrepo/
  ├── master
  │   ├── aliases.sqlite3
  │   └── sequences
  │       ├── 2016
  │       │   ├── 0824
  │       │   │   ├── 045923
  │       │   │   │   ├── 1472014763.7728612.fa.bgz
  │       │   │   │   ├── 1472014763.7728612.fa.bgz.fai
  │       │   │   │   └── 1472014763.7728612.fa.bgz.gzi
  │       │   │   ├── 045927
  │       │   │   │   ├── 1472014767.3542793.fa.bgz
  ├── 2016-08-27
  │   ├── aliases.sqlite3
  │   └── sequences
  │       ├── 2016 ...
  ├
  └── 2016-08-28
      ├── aliases.sqlite3
      └── sequences
          │   ├── 0824...
          │   └── 0828
          │       ├── 000003
          │       │   ├── 1472342403.26.fa.bgz
          │       │   ├── 1472342403.26.fa.bgz.fai
          │       │   └── 1472342403.26.fa.bgz.gzi
          │           └── 1472357923.36.fa
          └── db.sqlite3


