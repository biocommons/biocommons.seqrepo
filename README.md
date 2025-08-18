# biocommons.seqrepo

SeqRepo is a Python package for storing and reading a local collection of
biological sequences. The repository is non-redundant, compressed, and
journalled, making it efficient to store and transfer multiple snapshots.

## Introduction

Specific, named biological sequences provide the reference and coordinate
system for communicating variation and consequential phenotypic changes.
Several databases of sequences exist, with significant overlap, all using
distinct names. Furthermore, these systems are often difficult to install
locally.

SeqRepo provides an efficient, non-redundant and indexed storage system for
biological sequences. Clients refer to sequences and metadata using familiar
identifiers, such as NM_000551.3 or GRCh38:1, or any of several hash-based
identifiers. The interface supports fast slicing of arbitrary regions of large
sequences.

A "fully-qualified" identifier includes a namespace to disambiguate accessions
from different origins or sequence sets (e.g., "1" in GRCh37 and GRCh38). If the
namespace is provided, seqrepo uses it as-is; if the namespace is not provided
and the unqualified identifier refers to a unique sequence, it is returned;
otherwise, the use of ambiguous identifiers raise an error.

SeqRepo favors namespaces from [identifiers.org](https://identifiers.org)
whenever available. Examples include
[refseq](<https://registry.identifiers.org/registry/refseq>) and
[ensembl](<https://registry.identifiers.org/registry/ensembl>).

[seqrepo-rest-service](https://github.com/biocommons/seqrepo-rest-service) provides a REST interface
and docker image.

Released under the Apache License, 2.0.

[![ci_rel](https://travis-ci.org/biocommons/biocommons.seqrepo.svg?branch=master)](https://travis-ci.org/biocommons/biocommons.seqrepo)
\|
[![cov](https://coveralls.io/repos/github/biocommons/biocommons.seqrepo/badge.svg?branch=)](https://coveralls.io/github/biocommons/biocommons.seqrepo?branch=)
\|
[![pypi_rel](https://badge.fury.io/py/biocommons.seqrepo.png)](https://pypi.org/pypi?name=biocommons.seqrepo)
\| [ChangeLog](https://github.com/biocommons/biocommons.seqrepo/tree/master/docs/changelog/0.5)

## Citation

Hart RK, Prlić A (2020). **SeqRepo: A system for managing local collections of
biological sequences.** PLoS ONE 15(12): e0239883.
<https://doi.org/10.1371/journal.pone.0239883>

## Features

- Timestamped, read-only snapshots.
- Space-efficient storage of sequences within a single snapshot and across snapshots.
- Bandwidth-efficient transfer incremental updates.
- Fast fetching of sequence slices on chromosome-scale sequences.
- Precomputed digests that may be used as sequence aliases.
- Mappings of external aliases (i.e., accessions or identifiers like
  `NM_013305.4`) to sequences.

## Deployments Scenarios

- Local read-only archive, mirrored from public site, accessed via Python API
  (see [Mirroring documentation](docs/mirror.rst))
- Local read-write archive, maintained with command line utility and/or API (see
  [Command Line Interface documentation](docs/cli.rst)).
- Docker data-only container that may be linked to application container.
- SeqRepo and refget REST API for local or remote access (see
    [seqrepo-rest-service](https://github.com/biocommons/seqrepo-rest-service))

## Technical Quick Peek

Within a single snapshot, sequences are stored *non-redundantly* and
*compressed* in an add-only journalled filesystem structure. A truncated SHA-512
hash is used to assess uniquness and as an internal id. (The digest is truncated
for space efficiency.)

Sequences are compressed using the Block GZipped Format
([BGZF](https://samtools.github.io/hts-specs/SAMv1.pdf))), which enables pysam
to provide fast random access to compressed sequences. (Variable compression
typically makes random access impossible.)

Sequence files are immutable, thereby enabling the use of hardlinks across
snapshots and eliminating redundant transfers (e.g., with `rsync`).

Each sequence id is associated with a namespaced alias in a sqlite database.
Such as `<seguid,rvvuhY0FxFLNwf10FXFIrSQ7AvQ>`, `<NCBI,NP_004009.1>`,
`<gi,5032303>`, `<ensembl-75ENSP00000354464>`, `<ensembl-85,ENSP00000354464.4>`.
The sqlite database is mutable across releases.

For calibration, recent releases that include 3 human genome assemblies
(including patches), and full RefSeq sets (NM, NR, NP, NT, XM, and XP) consumes
approximately 8GB. The minimum marginal size for additional snapshots is
approximately 2GB (for the sqlite database, which is not hardlinked).

For more information, see [docs/design.rst](docs/design.rst).

## Requirements

Reading a sequence repository requires several Python packages, all of which are
available from pypi. Installation should be as simple as `pip install
biocommons.seqrepo`.

Acquiring SeqRepo snapshots using the CLI requires an [rsync](https://github.com/RsyncProject/rsync) binary. Note that [openrsync](https://www.openrsync.org/), which now ships with new MacOS installs, does not support all required functions. Mac users should install rsync from [HomeBrew](https://formulae.brew.sh/formula/rsync) and use the `--rsync-exe` option to declare its exact location.

*Writing* sequence files also requires `bgzip`, which provided in the
[htslib](https://github.com/samtools/htslib) repo. Ubuntu users should install
the `tabix` package with `sudo apt install tabix`.

Development and deployments are on Ubuntu. Other systems may work but are not
tested. Patches to get other systems working would be welcomed.

## Quick Start

### OS X

    $ brew install python htslib

### Ubuntu

    $ sudo apt install -y python3-dev gcc zlib1g-dev tabix

### All platforms

    $ python -m venv venv
    $ source venv/bin/activate
    $ pip install seqrepo
    $ sudo mkdir -p /usr/local/share/seqrepo
    $ sudo chown $USER /usr/local/share/seqrepo
    $ seqrepo pull -i 2024-12-20
    $ seqrepo show-status -i 2024-12-20
    seqrepo 0.6.12.dev7+gd311e3e.d20250730
    instance directory: /usr/local/share/seqrepo/2024-12-20, 13.5 GB
    backends: fastadir (schema 1), seqaliasdb (schema 1)
    sequences: 1144093 sequences, 128795051613 residues, 435 files
    aliases: 5865328 aliases, 5865328 current, 35 namespaces, 1144093 sequences

    # Simple Pythonic interface to sequences
    >> from biocommons.seqrepo import SeqRepo
    >> sr = SeqRepo("/usr/local/share/seqrepo/2024-12-20")
    >> sr["NC_000001.11"][780000:780020]
    'TGGTGGCACGCGCTTGTAGT'

    # Or, use the seqrepo shell for even easier access
    $ seqrepo start-shell -i 2024-12-20
    In [1]: sr["NC_000001.11"][780000:780020]
    Out[1]: 'TGGTGGCACGCGCTTGTAGT'

    # N.B. The following output is edited for simplicity
    $ seqrepo export -i 2024-12-20 | head -n100
    >MD5:611ff0945aa9eeaaf9ef908d0e744cd0 SEGUID:mirLo912A/MppLuS1cUyFMduLUQ SHA1:9a2acba3dd7603f329a4bb92d5c53214c76e2d44 VMC:GS_---7nAwbv5Fs2Ml2-k3X6Zvj-6ZcjeD3 ga4gh:SQ.---7nAwbv5Fs2Ml2-k3X6Zvj-6ZcjeD3 sha512t24u:---7nAwbv5Fs2Ml2-k3X6Zvj-6ZcjeD3
    MDSPLREDDSQTCARLWEAEVKRHSLEGLTVFGTAVQIHNVQRRAIRAKGTQEAQAELLCRGPRLLDRFLEDACILKEGRGTDTGQHCRGDARISSHLEA
    SGTHIQLLALFLVSSSDTPPSLLRFCHALEHDIRYNSSFDSYYPLSPHSRHNDDLQTPSSHLGYIITVPDPTLPLTFASLYLGMAPCTSMGSSSMGIFQS
    QRIHAFMKGKNKWDEYEGRKESWKIRSNSQTGEPTF
    >MD5:8ca1247fe64b17b9d40c2112a8bfc3a2 NCBI:XM_017008743.2 SEGUID:8cijSTmR/FOL+Gtq9gf6JlbRcvY SHA1:f1c8a3493991fc538bf86b6af607fa2656d172f6 VMC:GS_---BUlBwgZN_r5wSII-WCNDd9nn1Owj4 ga4gh:SQ.---BUlBwgZN_r5wSII-WCNDd9nn1Owj4 refseq:XM_017008743.2 sha512t24u:---BUlBwgZN_r5wSII-WCNDd9nn1Owj4
    ACTTATGGAAAACAGTGTGGCATATTCTGCTGAGCTTCGCCCTGGAAGAAGCCTCTTTTATACATCTCTTCAGGGAAGAGAGAAGCAATGGGCATGTTAG
    TATACAATGATCACAGCCACGCAGGCCTGCAAGCTGCCTTTTGGACAGGCTGTTGACTGCCGTTCCAATTAGCTGATTGGAGAATGTGGAATGCAGAGTG
    ATAATGCTGCATATCTGCTATCAGGCAGCAGCAAAGGTTTTTGTCTTGGGAAGGCAAGCTTTCCCTGCAATATTATCTCAGCAGCTCCCTAGCTGCTTAC

See [Installation](docs/installation.rst) and
[Mirroring](docs/mirror.rst) for more information.

## Environment Variables

SEQREPO_LRU_CACHE_MAXSIZE sets the lru_cache maxsize for the sqlite query
response caching. It defaults to 1 million but can also be set to "none" to be
unlimited.

SEQREPO_FD_CACHE_MAXSIZE sets the lru_cache size for file handler caching during
FASTA sequence retrievals. It defaults to 0 to disable any caching, but can be
set to a specific value or "none" to be unlimited. Using a moderate value (>10)
will greatly increase performance of sequence retrieval.

## Developing

### Developing on OS X

    brew install python htslib

If you get "xcrun: error: invalid active developer path", you need to install
XCode. See this [StackOverflow answer](https://apple.stackexchange.com/questions/254380/why-am-i-getting-an-invalid-active-developer-path-when-attempting-to-use-git-a).

### Developing on Ubuntu

    sudo apt install -y python3-dev gcc zlib1g-dev tabix

Here's how to get started developing:

    make devready
    source venv/bin/activate
    seqrepo --version

Code reformatting:

    make reformat

Install pre-commit hook:

    # included in `make devready`, not necessary for new installations
    pre-commit install

## Building a docker image

Docker images are available at https://hub.docker.com/r/biocommons/seqrepo.
Tags correspond to the version of data, not the version of seqrepo, because the
intent is to make it easy to depend on a local version of seqrepo *files*.  Each
docker image is an installation of seqrepo that downloads the corresponding
version of seqrepo data.  When used in conjunction with docker volumes for
persistence, this provides an easy way to incorporate seqrepo data into a docker
stack.

### Building

    cd misc/docker
    make 2021-01-29.log  # builds and pushes to hub.docker.com (i.e., you need creds)
