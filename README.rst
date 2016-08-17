biocommons.fastadir
===================

Python package for writing and reading a non-redundant, journalled,
filesystem-backed collection of biological sequences.


Features/Goals
!!!!!!!!!!!!!!

* Space-efficient storage of sequences within a release and across releases
* Bandwidth-efficient transfer incremental updates
* Fast fetching of sequence slices on chromosome-scale sequences
* Provenance data regarding sequence sources and accessions


Expected deployment cases
!!!!!!!!!!!!!!!!!!!!!!!!!

* Local mirror, replicated with rsync, accessing via Python
* Docker image with REST interface  


Later
@@@@@

* Explicitly model graph segments in sequence storage
* Enable tiered storage, such as local sources first, then remote
* Consistent interface for local and remote sequences
* Scale to tens of millions of sequences (at least)
* Promote hash-based accessions as primary identifiers to facilitate
  the use of graph segments


client:
sr = SeqRepo(...)

sr.fetch_aliases_by_id(id) -> [(o,v,a), ...]
sr.fetch_id_for_alias(o, v, a) -> [(o,v,a), ...]
sr
