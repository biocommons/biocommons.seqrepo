seqrepo
=======

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
* Precomputed digests that may be used as sequence aliases

For more information, see `<design.rst>`__.


Expected deployment cases
!!!!!!!!!!!!!!!!!!!!!!!!!

* Local access via Python package, using a repo rsync'd from a remote source or loaded locally
* Docker image with REST interface


Installation
!!!!!!!!!!!!

seqrepo has been tested only on Ubuntu 14.04 and 16.04.  It requires
separate installation of the tabix package.  It requires sqlite3 >=
3.8.0, which likely precludes early Ubuntu distributions.

On Ubuntu 16.04::

  sudo apt install tabix
  pip install seqrepo


Command line usage
!!!!!!!!!!!!!!!!!!

seqrepo includes a command line interface for loading, fetching, and exporting sequences.

loading
@@@@@@@


fetching one sequence
@@@@@@@@@@@@@@@@@@@@@


exporting all sequences
@@@@@@@@@@@@@@@@@@@@@@@



API Usage
!!!!!!!!!


Fetching existing sequence repositories
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

