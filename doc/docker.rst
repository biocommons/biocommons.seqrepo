seqrepo docker instructions
!!!!!!!!!!!!!!!!!!!!!!!!!!!

*Experimental* support for seqrepo as a docker data volume container
is available.  This means that you can use ``docker run`` to pull and
maintain an instance of seqrepo sequences, and share that data across
multiple containers on the same host and with the host itself.


Quick Start
@@@@@@@@@@@

First, create the data container and populate it::
  
  $ docker pull biocommons/seqrepo
  $ docker run --name seqrepo biocommons/seqrepo

Running the container will immediately invoke ``seqrepo pull``, which
will rsync data from ``dl.biocommons.org``.

As run above, data will be stored within ``/var/lib/docker/volumes/``
on the host. This directory may be shared with other docker
containers. (See Tips__ below for sharing seqrepo with the host
system.)

The ``biocommons/seqrepo`` image declares the volume
``/usr/local/share/seqrepo`` as sharable; containers may use
``volumes-from`` to have share seqrepo data like so::

  $ docker run -it --volumes-from seqrepo:ro ubuntu 
  root@1762eab78c3f:/# ls /usr/local/share/seqrepo/
  2016-10-04

  root@1762eab78c3f:/# apt update && apt install -y python3-pip  zlib1g-dev
  ...

  root@1762eab78c3f:/# pip3 install biocommons.seqrepo
  ...

  root@1762eab78c3f:/# ipython
  In [1]: from biocommons.seqrepo import SeqRepo
  In [2]: sr = SeqRepo("/usr/local/share/seqrepo/2016-10-04")
  In [3]: sr["NM_000059.3"][:10]
  Out[3]: 'GTGGCGCGAG'




Tips
@@@@

* docker `volume binding
  <https://docs.docker.com/engine/reference/run/#volume-shared-filesystems>`_
  (`-v`) may be used to share the host's seqrepo repository with that
  in the container, like this::

    mkdir /usr/local/share/seqrepo
    docker run --user $(id -u):$(id -g) -v /usr/local/share/seqrepo:/usr/local/share/seqrepo biocommons/seqrepo

  In this case, the host's ``/usr/local/share/seqrepo`` (before the
  colon) will be made available as the container's
  ``/usr/local/share/seqrepo`` (after the colon).  This effectively
  shares the seqrepo data inside and outside of the container.

  NOTE: The `--user` argument must match the owner of `/usr/local/share/seqrepo`.
