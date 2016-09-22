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
``<seguid,rvvuhY0FxFLNwf10FXFIrSQ7AvQ>``, ``<ncbi,NP_004009.1>``,
``<gi,5032303>``, ``<ensembl-75ENSP00000354464>``,
``<ensembl-85,ENSP00000354464.4>`` (all of which refer to the same
sequence).  Block gzipped format (`BGZF
<https://samtools.github.io/hts-specs/SAMv1.pdf>`__)) enables pysam to
provide fast random access to compressed sequences.

For more information, see `<doc/design.rst>`__.


Deployments Scenarios
!!!!!!!!!!!!!!!!!!!!!
* Available now: Local read-only archive, mirrored from public site,
  accessed via Python API (see `Mirroring documentation <doc/mirror.rst>`__)
* Available now: Local read-write archive, maintained with command
  line utility and/or API (see `Command Line Interface documentation
  <doc/cli.rst>`__).
* Planned: Docker-based data-only container that may be linked to application container
* Planned: Docker image that provides REST interface for local or remote access


Requirements
!!!!!!!!!!!!

Reading a sequence repository requires several packages, all of which
are available from pypi. Installation should be as simple as `pip
install biocommons.seqrepo`.

Writing sequence files also requires ``bgzip``, which provided in the
`htslib <https://github.com/samtools/htslib>`__ repo. Ubuntu users
should install the ``tabix`` package with ``sudo apt install tabix``.

Development and deployments are on Ubuntu. Other systems may work but
are not tested.  Patches to get other systems working would be
welcomed.


Quick Start
!!!!!!!!!!!

On Ubuntu 16.04::

  $ sudo apt install -y python3-dev gcc zlib1g-dev tabix
  $ pip install seqrepo
  $ seqrepo pull -i 20160906 
  $ seqrepo show-status -i 20160906 
  seqrepo 0.2.3.post3.dev8+nb8298bd62283
  root directory: /usr/local/share/seqrepo/20160906, 7.9 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 773587 sequences, 93051609959 residues, 192 files
  aliases: 5579572 aliases, 5480085 current, 26 namespaces, 773587 sequences
  
  $ seqrepo start-shell -i 20160906
  In [1]: sr["NC_000001.11"][780000:780020]
  Out[1]: 'TGGTGGCACGCGCTTGTAGT'
  
  # N.B. The following output is edited
  $ seqrepo export -i 20160906 | head -n100
  >sha1:9a2acba3dd7603f... seguid:mirLo912A/MppLuS1cUyFMduLUQ ensembl-85:GENSCAN00000003538 sh:---7nAwbv5Fs2Ml2-k3X6Zvj-6ZcjeD3 ...
  MDSPLREDDSQTCARLWEAEVKRHSLEGLTVFGTAVQIHNVQRRAIRAKGTQEAQAELLCRGPRLLDRFLEDACILKEGRGTDTGQHCRGDARISSHLEA
  SGTHIQLLALFLVSSSDTPPSLLRFCHALEHDIRYNSSFDSYYPLSPHSRHNDDLQTPSSHLGYIITVPDPTLPLTFASLYLGMAPCTSMGSSSMGIFQS
  QRIHAFMKGKNKWDEYEGRKESWKIRSNSQTGEPTF
  >sha1:ca996b263102b1... seguid:yplrJjECsVqQufeYy0HkDD16z58 ncbi:XR_001733142.1 sh:---WkVUs3IT3_ZZM-ReDjypLo6d_vJx6 gi:1034683989
  TTTACGTCTTTCTGGGAATTTATACTGGAAGTATACTTACCTCTGTGCAAAATTGCAAATATATAAGGTAATTCATTCCAGCATTGCTTATATTAGGTTG
  AACTATGTAACATTGACATTGATGTGAATCAAAAATGGTTGAAGGCTGGCAGTTTCATATGATTCAGCCTATAATAGCAAAAGATTGAAAAAATCCATTA
  ATACAGTGTGGTTCAAAAAAATTTGTTGTATCAAGGTAAAATAATAGCCTGAATATAATTAAGATAGTCTGTGTATACATCGATGAAAACATTGCCAATA



See `Installation <doc/installation.rst>`__ and `Mirroring
<doc/mirror.rst>`__ for more information.



.. |pypi_rel| image:: https://badge.fury.io/py/biocommons.seqrepo.png
  :target: https://pypi.org/pypi?name=biocommons.seqrepo
  :align: middle

.. |ci_rel| image:: https://travis-ci.org/biocommons/biocommons.seqrepo.svg?branch=master
  :target: https://travis-ci.org/biocommons/biocommons.seqrepo
  :align: middle 

