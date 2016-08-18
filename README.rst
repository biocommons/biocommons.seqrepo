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
  

Loading
@@@@@@@

::

  $ seqrepo -d /tmp/sr init
  
  $ seqrepo -v -d /tmp/sr load-fasta -f myfasta.gz -n me
  
  $ seqrepo -v -d /tmp/sr status
  seqrepo 0.1.0
  root directory: /tmp/sr, 0.2 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 3 files, 33080 sequences, 110419437 residues
  aliases: 165481 aliases, 165481 current, 5 namespaces, 33080 sequences


Exporting all sequences
@@@@@@@@@@@@@@@@@@@@@@@

::

  $ seqrepo -v -d /tmp/sr export
  >ncbi:NM_013305.4 seguid:EqjiLe... md5:04e8c3c75... sha512:000a70c470f6... sha1:12a8e22d...
  GTACGCCCCCTCCCCCCGTCCCTATCGGCAGAACCGGAGGCCAACCTTCGCGATCCCTTGCTGCGGGCCCGGAGATCAAACGTGGCCCGCCCCCGGCAGG
  GCACAGCGCGCTGGGCAACCGCGATCCGGCGCCGGACTGGAGGGGTCGATGCGCGGCGCGCTGGGGCGCACAGGGGACGGAGCCCGGGTCTTGCTCCCCA
  ...

API Usage
!!!!!!!!!

::

  $ seqrepo -v -d /tmp/sr shell
  
  # iterate over unique sequences:
  for srec, arec in sr:
      pprint.pprint(srec)
      pprint.pprint(arec)

  # results in records like:
  {'added': '2016-08-18 17:40:49',
   'alpha': 'ACGT',
   'len': 2627,
   'relpath': '2016/08/18/1740/1471542046.008535.fa.bgz',
   'seq': 'GTACGCCC...',
   'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518'}
  
  and

  [{'added': '2016-08-18 17:40:49',
    'alias': '04e8c3c753dad9c19741cdf81ec2b3d5',
    'is_current': 1,
    'namespace': 'md5',
    'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'seqalias_id': 144388},
   {'added': '2016-08-18 17:40:49',
    'alias': 'EqjiLeXFeeBT6LIMnbCFQxNqHD8',
    'is_current': 1,
    'namespace': 'seguid',
    'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'seqalias_id': 144389},
   {'added': '2016-08-18 17:40:49',
    'alias': '12a8e22de5c579e053e8b20c9db08543136a1c3f',
    'is_current': 1,
    'namespace': 'sha1',
    'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'seqalias_id': 144387},
   {'added': '2016-08-18 17:40:49',
    'alias': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'is_current': 1,
    'namespace': 'sha512',
    'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'seqalias_id': 144386},
   {'added': '2016-08-18 17:40:49',
    'alias': 'NM_013305.4',
    'is_current': 1,
    'namespace': 'ncbi',
    'seq_id': '000a70c470f637d6e3a76497aac3eabc4f7816be8fe03d15bdbd3504655fd3f6ddb2609aeef5e0edfbea16ae8ab181b704c4bfb3cd4328c57a895e02fe5ab518',
    'seqalias_id': 144390}]



Fetching existing sequence repositories
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

TO BE WRITTEN

(General idea: Distribute repository with snapshots via rsync server
from public site for manual installation, and use the same source to
seed a docker container.)
