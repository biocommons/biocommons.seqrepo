Example::

  $ seqrepo init
  
  $ seqrepo -v load-fasta -n me fasta1.gz fasta2.gz fasta3.gz
  
  $ seqrepo -v status
  seqrepo 0.1.0
  instance directory: /usr/local/share/seqrepo/master, 0.2 GB
  backends: fastadir (schema 1), seqaliasdb (schema 1) 
  sequences: 3 files, 33080 sequences, 110419437 residues
  aliases: 165481 aliases, 165481 current, 5 namespaces, 33080 sequences

  $ seqrepo -v export | head
  >SEGUID:EqjiLe... MD5:04e8c3c75... SHA512:000a70c470f6... SHA1:12a8e22d...
  GTACGCCCCCTCCCCCCGTCCCTATCGGCAGAACCGGAGGCCAACCTTCGCGATCCCTTGCTGCGGGCCCGGAGATCAAACGTGGCCCGCCCCCGGCAGG
  GCACAGCGCGCTGGGCAACCGCGATCCGGCGCCGGACTGGAGGGGTCGATGCGCGGCGCGCTGGGGCGCACAGGGGACGGAGCCCGGGTCTTGCTCCCCA


In [10]: %time sr.fetch("NC_000001.10", start=6000000, end=6000200)
CPU times: user 4 ms, sys: 0 ns, total: 4 ms
Wall time: 492 µs
Out[10]: 'GGACAACAGAGGATGAGGTGGGGCCAGCAGAGGGACAGAGAAGAGCTGCCTGCCCTGGAACAGGCAGAAAGCATCCCACGTGCAAGAAAAAGTAGGCCAGCTAGACTTAAAATCAGAACTACCGCTCATCAAAAGATAGTGTAACATTTGGGGTGCTATAATTTTAACATGTCCCCCAAAAGGCATGTGTTGGAAATTTA'



Sequences are stored non-redundantly in compressed, timestamped files::

  $ tree $SEQREPO_ROOT
  /usr/local/share/seqrepo/master
  ├── aliases.sqlite3
  └── sequences
      ├── 2016
      │   └── 08
      │       └── 18
      │           └── 1740
      │               ├── 1471542021.2968519.fa.bgz
      │               ├── 1471542021.2968519.fa.bgz.fai
      │               ├── 1471542021.2968519.fa.bgz.gzi
      │               ├── 1471542033.2398305.fa.bgz
      │               ├── 1471542033.2398305.fa.bgz.fai
      │               ├── 1471542033.2398305.fa.bgz.gzi
      │               ├── 1471542046.008535.fa.bgz
      │               ├── 1471542046.008535.fa.bgz.fai
      │               └── 1471542046.008535.fa.bgz.gzi
      └── db.sqlite3
