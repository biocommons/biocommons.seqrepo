This document describes the design of the seqrepo package.


Goals
!!!!!

* Space-efficient within a release
* Simple use with multiple releases
* Space-efficient across releases
* Bandwidth-efficient distribution of incremental updates
* Fast sequence lookup and slicing
* Zero or more namespaced aliases associated with a sequence


(A) Solution
!!!!!!!!!!!!

The solution implemented here uses block-gzipped fasta files with
access provided by the pysam.FastaFile module.  This module provides
indexed access to fasta files, with extremely fast slicing into very
large sequences.  A new module, fabgz, was written to provide 



Although FastaFile works very well with large (multigigabyte) files,
the desire for 






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




* Layout 1

seqrepo/
  interface.py
  filesystem.py
seqstore/
  interface.py
  filesystem.py
seqalias/
  interface.py
  sqlite.py
 
* Layout 2

  ::
     seqstore/
       interface.py
       seqfetcher.py
       fabgz.py
       fadir/
       seqrepo/
         cli.py
	 seqrepo.py
	 seqaliasdb.py
       composite.py

   interface::
     fetcher: fetch, __getitem__
     collection (isa fetcher): keys/__dir__, __contains__, __iter__/__next__, __len__
     writer: store, __setitem__


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

