biocommons.seqrepo
==================

Python package for writing and reading a local collection of
biological sequences.  The repository is non-redundant, compressed,
and journalled, making it efficient to store and transfer incremental
snapshots.


Features
!!!!!!!!

* Space-efficient storage of sequences within a release and across releases
* Bandwidth-efficient transfer incremental updates
* Fast fetching of sequence slices on chromosome-scale sequences
* Provenance data regarding sequence sources and accessions


Expected deployment cases
!!!!!!!!!!!!!!!!!!!!!!!!!

* Local access via Python package
* Docker image with REST interface
