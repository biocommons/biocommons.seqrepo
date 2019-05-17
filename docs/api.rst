API Usage
!!!!!!!!!

::

  $ seqrepo -v -d $SEQREPO_ROOT shell
  
  In [10]: %time sr.fetch("NC_000001.10", start=6000000, end=6000200)
  CPU times: user 4 ms, sys: 0 ns, total: 4 ms
  Wall time: 492 µs
  Out[10]: 'GGACAACAGAGGATGAGGTGGGGCCAGCAGAGGGACAGAGAAGAGC...'


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
    'alias': 'EqjiLeXFeeBT6LIMnbCFQxNqHD8',
    'is_current': 1,
    'namespace': 'seguid',
    'seq_id': '-16o-XuCMVXM-y75LtlLPpmznaDqTn1b',
    'seqalias_id': 144389},
   {'added': '2016-08-18 17:40:49',
    'alias': 'NM_013305.4',
    'is_current': 1,
    'namespace': 'NCBI',
    'seq_id': '-16o-XuCMVXM-y75LtlLPpmznaDqTn1b',
    'seqalias_id': 144390}]
