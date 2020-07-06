SeqRepo Loading Notes
!!!!!!!!!!!!!!!!!!!!!


Japanese Reference Genome
@@@@@@@@@@@@@@@@@@@@@@@@@

Like this::
  
  wget -nd https://jmorp.megabank.tohoku.ac.jp/dj1/datasets/tommo-jrgv1/files/JRGv{1,2}.zip?download=true
  unzip -p JRGv1.zip\?download\=true JRGv1.fasta | seqrepo -r /tmp load -i master -n JRGv1 -
  unzip -p JRGv2.zip\?download\=true JRGv2.fasta | seqrepo -r /tmp load -i master -n JRGv2 -
  
