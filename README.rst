biocommons.seqrepo
!!!!!!!!!!!!!!!!!!

**Important**: seqrepo 0.4.0 was released on 2018-10-21. 0.4.0
provides a transition path for **breaking changes** that will occur in the
0.5 series. See `0.4.0 Changelog
<https://github.com/biocommons/biocommons.seqrepo/blob/master/doc/changelog/0.4/0.4.0.rst>`__
for details.

----

Python package for writing and reading a local collection of
biological sequences.  The repository is non-redundant, compressed,
and journalled, making it efficient to store and transfer multiple
snapshots.

Released under the Apache License, 2.0.

|ci_rel| | |cov| | |pypi_rel|


Features
!!!!!!!!

* Timestamped, read-only snapshots.
* Space-efficient storage of sequences within a single snapshot and
  across snapshots.
* Bandwidth-efficient transfer incremental updates.
* Fast fetching of sequence slices on chromosome-scale sequences.
* Precomputed digests that may be used as sequence aliases.
* Mappings of external aliases (i.e., accessions or identifiers like
  NM_013305.4) to sequences.


Deployments Scenarios
!!!!!!!!!!!!!!!!!!!!!
* Local read-only archive, mirrored from public site,
  accessed via Python API (see `Mirroring documentation <doc/mirror.rst>`__)
* Local read-write archive, maintained with command
  line utility and/or API (see `Command Line Interface documentation
  <doc/cli.rst>`__).
* Docker-based data-only container that may be linked to application container.
* Planned: Docker image that provides REST interface for local or remote access


Technical Quick Peek
!!!!!!!!!!!!!!!!!!!!

Within a single snapshot, sequences are stored *non-redundantly* and
*compressed* in an add-only journalled filesystem structure.  A
truncated SHA-512 hash is used to assess uniquness and as an
internal id.  (The digest is truncated for space efficiency.)

Sequences are compressed using the Block GZipped Format (`BGZF
<https://samtools.github.io/hts-specs/SAMv1.pdf>`__)), which enables
pysam to provide fast random access to compressed sequences. (Variable
compression typically makes random access impossible.)

Sequence files are immutable, thereby enabling the use of hardlinks
across snapshots and eliminating redundant transfers (e.g., with
rsync).

Each sequence id is associated with a namespaced alias in a sqlite
database.  Such as ``<seguid,rvvuhY0FxFLNwf10FXFIrSQ7AvQ>``,
``<NCBI,NP_004009.1>``, ``<gi,5032303>``,
``<ensembl-75ENSP00000354464>``, ``<ensembl-85,ENSP00000354464.4>``.
The sqlite database is mutable across releases.

For calibration, recent releases that include 3 human genome
assemblies (including patches), and full RefSeq sets (NM, NR, NP, NT,
XM, and XP) consumes approximately 8GB.  The minimum marginal size for
additional snapshots is approximately 2GB (for the sqlite database,
which is not hardlinked).

For more information, see `<doc/design.rst>`__.



Requirements
!!!!!!!!!!!!

Reading a sequence repository requires several Python packages, all of
which are available from pypi. Installation should be as simple as
`pip install biocommons.seqrepo`.

*Writing* sequence files also requires ``bgzip``, which provided in
the `htslib <https://github.com/samtools/htslib>`__ repo. Ubuntu users
should install the ``tabix`` package with ``sudo apt install tabix``.

Development and deployments are on Ubuntu. Other systems may work but
are not tested.  Patches to get other systems working would be
welcomed.

**Mac Developers** If you get "xcrun: error: invalid active developer
path", you need to install XCode. See this `StackOverflow answer
<https://apple.stackexchange.com/questions/254380/why-am-i-getting-an-invalid-active-developer-path-when-attempting-to-use-git-a>`__.


Quick Start
!!!!!!!!!!!

On Ubuntu 16.04::

  $ sudo apt install -y python3-dev gcc zlib1g-dev tabix
  $ pip install seqrepo
  $ sudo mkdir /usr/local/share/seqrepo
  $ sudo chown $USER /usr/local/share/seqrepo
  $ seqrepo pull -i 2018-11-26 
  $ seqrepo show-status -i 2018-11-26 
  seqrepo 0.2.3.post3.dev8+nb8298bd62283
  root directory: /usr/local/share/seqrepo/2018-11-26, 7.9 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 773587 sequences, 93051609959 residues, 192 files
  aliases: 5579572 aliases, 5480085 current, 26 namespaces, 773587 sequences
  
  # Simple Pythonic interface to sequences
  >> from biocommons.seqrepo import SeqRepo
  >> sr = SeqRepo("/usr/local/share/seqrepo/latest")
  >> sr["NC_000001.11"][780000:780020]
  'TGGTGGCACGCGCTTGTAGT'

  # Or, use the seqrepo shell for even easier access
  $ seqrepo start-shell -i 2018-11-26
  In [1]: sr["NC_000001.11"][780000:780020]
  Out[1]: 'TGGTGGCACGCGCTTGTAGT'
  
  # N.B. The following output is edited for simplicity
  $ seqrepo export -i 2018-11-26 | head -n100
  >SHA1:9a2acba3dd7603f... SEGUID:mirLo912A/MppLuS1cUyFMduLUQ Ensembl-85:GENSCAN00000003538 ...
  MDSPLREDDSQTCARLWEAEVKRHSLEGLTVFGTAVQIHNVQRRAIRAKGTQEAQAELLCRGPRLLDRFLEDACILKEGRGTDTGQHCRGDARISSHLEA
  SGTHIQLLALFLVSSSDTPPSLLRFCHALEHDIRYNSSFDSYYPLSPHSRHNDDLQTPSSHLGYIITVPDPTLPLTFASLYLGMAPCTSMGSSSMGIFQS
  QRIHAFMKGKNKWDEYEGRKESWKIRSNSQTGEPTF
  >SHA1:ca996b263102b1... SEGUID:yplrJjECsVqQufeYy0HkDD16z58 NCBI:XR_001733142.1 gi:1034683989
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

.. |cov| image:: https://coveralls.io/repos/github/biocommons/biocommons.seqrepo/badge.svg?branch=
  :target: https://coveralls.io/github/biocommons/biocommons.seqrepo?branch=
