Command line usage
!!!!!!!!!!!!!!!!!!

seqrepo includes a command line interface for loading, fetching, and exporting sequences.
  
This documentation assumes that the seqrepo base directory is::

  SEQREPO_ROOT=/usr/local/share/seqrepo

Current convention is to add sequences to `$SEQREPO_ROOT/master`, then
snapshot this to a dated directory like `$SEQREPO_ROOT/20160828`.  (This
convention is conceptually similar to source code development on a
master branch with tags.)


Loading
@@@@@@@

::

  $ seqrepo -d $SEQREPO_ROOT/master init
  
  $ seqrepo -d $SEQREPO_ROOT/master load -n ncbi mirror/ftp.ncbi.nih.gov/refseq/H_sapiens/mRNA_Prot/human.*.gz
  
  $ seqrepo -d $SEQREPO_ROOT/master show-status
  seqrepo 0.1.0
  root directory: /usr/local/share/seqrepo/master, 0.2 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 3 files, 33080 sequences, 110419437 residues
  aliases: 165481 aliases, 165481 current, 5 namespaces, 33080 sequences


Making a snapshot
@@@@@@@@@@@@@@@@@

Snapshots are made with the snapshot command::

  $ seqrepo -v -d $SEQREPO_ROOT/master snapshot 20160231
  INFO:biocommons.seqrepo.cli:snapshot created in $SEQREPO_ROOT/20160231

The snapshot command:

  * creates the same directory structure as the source directory (`-d`)
  * hardlinks the sequence files and indexes to the new location
  * copies the sqlite databases
  * removes write permissions from directories and sqlite databases
    (sequence files are made unwritable after creation).

If the snapshot argument is a full path, that is used as the
destination.  Otherwise, the argument is assumed to be relative to the
parent of the directory specified by `-d`. (A snapshot may not be
nested within the source directory.)




Exporting all sequences
@@@@@@@@@@@@@@@@@@@@@@@

::

  $ seqrepo -v -d $SEQREPO_ROOT/master export | head
  >ncbi:NM_013305.4 seguid:EqjiLe... md5:04e8c3c75... sha512:000a70c470f6... sha1:12a8e22d...
  GTACGCCCCCTCCCCCCGTCCCTATCGGCAGAACCGGAGGCCAACCTTCGCGATCCCTTGCTGCGGGCCCGGAGATCAAACGTGGCCCGCCCCCGGCAGG
  GCACAGCGCGCTGGGCAACCGCGATCCGGCGCCGGACTGGAGGGGTCGATGCGCGGCGCGCTGGGGCGCACAGGGGACGGAGCCCGGGTCTTGCTCCCCA


