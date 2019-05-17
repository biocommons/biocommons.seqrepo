Command line usage
!!!!!!!!!!!!!!!!!!

seqrepo includes a command line interface for loading, fetching, and exporting sequences.
  
This documentation assumes that the seqrepo base directory is::

  SEQREPO_ROOT=/usr/local/share/seqrepo

Current convention is to add sequences to `$SEQREPO_ROOT/master`, then
snapshot this to a dated directory like `$SEQREPO_ROOT/2016-08-28`.  (This
convention is conceptually similar to source code development on a
master branch with tags.)


Loading
@@@@@@@

::

  $ seqrepo --root-directory $SEQREPO_ROOT/master init
  
  $ seqrepo --root-directory $SEQREPO_ROOT/master load -n NCBI mirror/ftp.ncbi.nih.gov/refseq/H_sapiens/mRNA_Prot/human.*.gz
  
  $ seqrepo --root-directory $SEQREPO_ROOT/master show-status
  seqrepo 0.1.0
  root directory: /usr/local/share/seqrepo/master, 0.2 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 3 files, 33080 sequences, 110419437 residues
  aliases: 165481 aliases, 165481 current, 5 namespaces, 33080 sequences


Making a snapshot
@@@@@@@@@@@@@@@@@

Snapshots are made with the snapshot command::

  $ seqrepo -v snapshot 2017-07-17
  INFO:biocommons.seqrepo.cli:snapshot created in $SEQREPO_ROOT/2017-07-17

The snapshot command:

  * creates the same directory structure as the source directory
  * hardlinks the sequence files and indexes to the new location
  * copies the sqlite databases
  * removes write permissions from directories and sqlite databases
    (sequence files are made unwritable after creation).




Exporting all sequences
@@@@@@@@@@@@@@@@@@@@@@@

::

  $ seqrepo -v -r $SEQREPO_ROOT export | head
  >NCBI:NM_013305.4 seguid:EqjiLe... MD5:04e8c3c75... SHA512:000a70c470f6... SHA1:12a8e22d...
  GTACGCCCCCTCCCCCCGTCCCTATCGGCAGAACCGGAGGCCAACCTTCGCGATCCCTTGCTGCGGGCCCGGAGATCAAACGTGGCCCGCCCCCGGCAGG
  GCACAGCGCGCTGGGCAACCGCGATCCGGCGCCGGACTGGAGGGGTCGATGCGCGGCGCGCTGGGGCGCACAGGGGACGGAGCCCGGGTCTTGCTCCCCA



Configuration Notes
@@@@@@@@@@@@@@@@@@@

* SEQREPO_BGZIP_PATH may be used to specify an alternative location
  for the bgzip binary. (Default: /usr/bin/bgzip)

