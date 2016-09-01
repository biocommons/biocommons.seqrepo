This document describes the design of the seqrepo package.
It is currently a collection of thoughts during development.
If you find dangling sentences, you should


Goals and design implications
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

This section summarizes goals and their architectural implications.

* Space-efficient within a release/snapshot
  => compress sequences
  => dedupe sequences => use hashes
* Space-efficient across releases
  => use hard links
* Bandwidth-efficient distribution of incremental updates
  => immutable, journaled add-only sequence storage
* Zero or more namespaced aliases associated with a sequence
  => store aliases for hashed sequences
* Fast sequence lookup and slicing (random access)
  => when coupled with compression => blocked gzip

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


Hashing
!!!!!!!

internal PK/FK 

seqhash
sha512 truncated, 21-byte truncated, urlsafe base 64 encode
-16o-XuCMVXM-y75LtlLPpmznaDqTn1b



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




Known reference types: gi, refseq, ensembl, lrg, grc, bic
hashes: sha1, sha1/8, sha256, sha512, md5, seguid

* As github repo? => 100MB file size limit
* Tradeoff: want few files to work around file descriptor limits, but
  will also likely have many files to limit turn on updates.

Resolved
!!!!!!!!
* aliases should have key space
* origins correspond to key spaces for aliases
* store defline with schema


Plan
!!!!
* sha512 is primary hash of canonicalized sequence (speeds: sha1 > md5 ~ sha512 >> sha256)
* file loader reads fasta, yields [ (seq, [(origin,alias)] ]
* client interface, storage interface isa ci, ci connects with URI


Filesystem structure
!!!!!!!!!!!!!!!!!!!!

seqrepo/
  info.json
  db.sqlite
  tx/:tx/(hstree)

where (hstree) refers to a hashed sequence tree like:
  aa/bb/cc/dd.fa.bgz
  aa/bb/cc/dd.fa.bgz
  



Concepts and Terms:
origin & release
source file
alias



Use example:
import seqrepo
sdb = seqrepo.connect(uri)
    seqrepo+file:///local/dir/seqrepo/20160101/
    https://localhost:8000/seqrepo/20160101
    bigtable://...
    
         
seq = sdb.fetch(



* Q: What is the structure of keys?
seqstore interfaces are key-value based: keys are caller-defined
(typically, hashes or accessions), and values are sequences.

seqrepo stores namespaced keys like <namespace>:<alias>

presents a slight wrinkle that keys may have a syntactic
structure that are generally like, but they are
keys nonetheless.

When setting, keys must have a namespace.

When getting, keys may have a namespace. If a namespace is not
specified, a namespace-free search is performed; if that search
returns no results or ambiguous results, KeyError is raised.

