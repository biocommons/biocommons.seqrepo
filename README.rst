biocommons.seqrepo
==================

Python package for writing and reading a local collection of
biological sequences.  The repository is non-redundant, compressed,
and journalled, making it efficient to store and transfer multiple
snapshots.

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


Expected deployments and use modes
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

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

Fetching existing sequence repositories
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

A public instance of seqrepo with dated snapshots is available at on
seqrepo.biocommons.org.

You can list available snapshots like so::



ip-10-30-1-22$ rsync rsync.biocommons.org::
This is the rsync service for tools and data from biocommons.org
This service is hosted by Invitae (https://invitae.com/).

seqrepo         Sequence Repository snapshots; see instructions at https://github.com/biocommons/biocommons.seqrepo
uta             Universal Transcript Archive; see instructions at https://bitbucket.org/biocommons/uta
ip-10-30-1-22$ rsync rsync.biocommons.org::seqrepo                                                                                                                                                                                            
This is the rsync service for tools and data from biocommons.org
This service is hosted by Invitae (https://invitae.com/).

drwxr-xr-x          4,096 2016/08/31 01:25:54 .
dr-xr-xr-x          4,096 2016/08/28 03:25:40 20160827
dr-xr-xr-x          4,096 2016/08/28 15:52:54 20160828
ip-10-30-1-22$ rsync -HRavP rsync.biocommons.org::seqrepo/20160828 /usr/local/share/seqrepo/                                                                                                                                                  
This is the rsync service for tools and data from biocommons.org
This service is hosted by Invitae (https://invitae.com/).

receiving incremental file list
20160828/
20160828/aliases.sqlite3
    277,676,032  15%   88.33MB/s    0:00:16  ^C
rsync error: received SIGINT, SIGTERM, or SIGHUP (code 20) at rsync.c(632) [generator=3.1.1]
rsync error: received SIGUSR1 (code 19) at main.c(1434) [receiver=3.1.1]
ip-10-30-1-22$ ll /usr/local/share/seqrepo/
total 4.0K
drwxr-xr-x 3 reece reece 4.0K Aug 31 01:46 20160828/








.. |pypi_rel| image:: https://badge.fury.io/py/biocommons.seqrepo.png
  :target: https://pypi.org/pypi?name=biocommons.seqrepo
  :align: middle

.. |ci_rel| image:: https://travis-ci.org/biocommons/biocommons.seqrepo.svg?branch=master
  :target: https://travis-ci.org/biocommons/biocommons.seqrepo
  :align: middle 







	  
