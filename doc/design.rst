This document describes the design of the seqrepo package.


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

Space efficiency across snapshots is well-served by using hardlinks on 



Although FastaFile works very well with large (multigigabyte) files,
the desire for 


A new module, fabgz, was written to provide




* distinguish internal ids from namespaced aliases (even for sha512)



Filesystem Layout
!!!!!!!!!!!!!!!!!

/opt/seqrepo/data/
└── master
    ├── aliases.sqlite3
    ├── aliases.sqlite3-journal
    └── sequences
        ├── 2016
        │   └── 0701
     ///////
        │   └── 0713
     ///////
        │   └── 0819
        │       ├── 230638
        │       │   └── 1471647998.6470723.fa.bgz
        │       ├── 230647
        │       │   └── 1471648007.2638052.fa.bgz
     ///////
        ├── db.sqlite3
        └── db.sqlite3-journal




Managing SeqRepo snapshots
!!!!!!!!!!!!!!!!!!!!!!!!!!






Details
!!!!!!!


Known reference types: gi, refseq, ensembl, lrg, grc, bic
hashes: sha1, sha1/8, sha256, sha512, md5, seguid

Questions
!!!!!!!!!
* Okay to case-squash sequences?
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

