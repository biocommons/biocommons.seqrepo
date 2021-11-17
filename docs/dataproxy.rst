How to use the Data Proxy for data access
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

seqrepo includes a proxy class that allows to easily switch between either a local
or remote installations of seqrepo. In the case of a remote installation,
this approach expects that an instance of [seqrepo-rest-service](https://github.com/biocommons/seqrepo-rest-service)
is available somewhere.


::

>>> from biocommons.seqrepo import dataproxy
>>> dp1 = dataproxy.create_dataproxy("seqrepo+http://localhost:5000/seqrepo")
>>> dp2 = dataproxy.create_dataproxy("seqrepo+file:///usr/local/share/seqrepo/latest")
>>> ir = "refseq:NM_000551.3"
>>> print(f"dp1 = {dp1}")
``dp1 = <biocommons.seqrepo.dataproxy.SeqRepoRESTDataProxy object at 0x10ef1d9d0>``

>>> print(f"dp2 = {dp2}")
``dp2 = <biocommons.seqrepo.dataproxy.SeqRepoDataProxy object at 0x10d853970>``

>>> assert dp1.get_metadata(ir) == dp2.get_metadata(ir)
>>> assert dp1.get_sequence(ir) == dp2.get_sequence(ir)
>>> dp1.get_metadata(ir)
``{'added': '2016-08-24T05:03:11Z', 'aliases': ['MD5:215137b1973c1a5afcf86be7d999574a', 'NCBI:NM_000551.3', 'refseq:NM_000551.3', 'SEGUID:T12L0p2X5E8DbnL0+SwI4Wc1S6g', 'SHA1:4f5d8bd29d97e44f036e72f4f92c08e167354ba8', 'VMC:GS_v_QTc1p-MUYdgrRv4LMT6ByXIOsdw3C_', 'sha512t24u:v_QTc1p-MUYdgrRv4LMT6ByXIOsdw3C_', 'ga4gh:SQ.v_QTc1p-MUYdgrRv4LMT6ByXIOsdw3C_'], 'alphabet': 'ACGT', 'length': 4560}``


It is also possible to configure the location that should get used via an environemnt variable:

  export SEQREPO_DATAPROXY_URI='seqrepo+http://localhost:5000/seqrepo'

::

>>> from biocommons.seqrepo import dataproxy
>>> dp1 = dataproxy.create_dataproxy()


This dataproxy will automatically connect to the URI provided in the environment variable.
