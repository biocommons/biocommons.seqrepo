biocommons.seqrepo
!!!!!!!!!!!!!!!!!!

Python package for writing and reading a local collection of
biological sequences.  The repository is non-redundant, compressed,
and journalled, making it efficient to store and transfer multiple
snapshots.

Released under the Apache License, 2.0.

|ci_rel| |pypi_rel|


Features
!!!!!!!!

* Timestamped snapshots of read-only sequence repository
* Space-efficient storage of sequences within a single snapshot and
  across snapshots
* Bandwidth-efficient transfer incremental updates
* Fast fetching of sequence slices on chromosome-scale sequences
* Precomputed digests that may be used as sequence aliases
* Mappings of external aliases (i.e., accessions or identifiers like
  NM_013305.4) to sequences

The above features are achieved by storing sequences non-redundantly
and compressed, using an add-only journalled filesystem structure
within a single snapshot, and by using hard links across snapshots.
Each sequence is associated with a namespaced alias such as
<seguid,rvvuhY0FxFLNwf10FXFIrSQ7AvQ>, <ncbi,NP_004009.1>,
<gi,5032303>, <ensembl-75ENSP00000354464>,
<ensembl-85,ENSP00000354464.4> (all of which refer to the same
sequence).  Block gzipped format (`BGZF
<https://samtools.github.io/hts-specs/SAMv1.pdf>`__)) enables pysam to
provide fast random access to compressed sequences.

For more information, see `<doc/design.rst>`__.


Anticipated deployments
!!!!!!!!!!!!!!!!!!!!!!!

* Local read-only archive, mirrored from public site, accessed via Python API
* Local read-only archive, mirrored from public site, accessed via REST interface (not yet available)
* Local read-write archive, maintained with command line utility and/or API


Requirements
!!!!!!!!!!!!

Reading a sequence repository requires several packages, all of which
are available from pypi. Installation should be as simple as `pip
install biocommons.seqrepo`.

Writing sequence files also requires `bgzip`, which provided in the
`htslib <https://github.com/samtools/htslib>`__ repo. Ubuntu users
should install the `tabix` package with `sudo apt install tabix`.

Development and deployments are on Ubuntu. Other systems may work but
are not tested.  Patches to get other systems working would be
welcomed.


Quick Start
!!!!!!!!!!!

On Ubuntu 16.04::

  $ sudo apt install -y python3-dev gcc zlib1g-dev tabix
  $ pip install seqrepo
  $ rsync -HRavP rsync.biocommons.org::seqrepo/20160828 /usr/local/share/seqrepo/
  $ seqrepo -d /usr/local/share/seqrepo/20160828 start-shell
  seqrepo 0.2.3.dev2+neeca95d3ae6e.d20160830
  root directory: /opt/seqrepo/20160828, 7.9 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 773511 sequences, 93005806376 residues, 189 files
  aliases: 5572724 aliases, 5473237 current, 9 namespaces, 773511 sequences

  In [1]: sr["NC_000001.11"][780000:780020]
  Out[1]: 'TGGTGGCACGCGCTTGTAGT'


See `Installation <doc/installation.rst>`__ and `Mirroring
<doc/mirroring.rst>`__ for more information.



.. |pypi_rel| image:: https://badge.fury.io/py/biocommons.seqrepo.png
  :target: https://pypi.org/pypi?name=biocommons.seqrepo
  :align: middle

.. |ci_rel| image:: https://travis-ci.org/biocommons/biocommons.seqrepo.svg?branch=master
  :target: https://travis-ci.org/biocommons/biocommons.seqrepo
  :align: middle 

