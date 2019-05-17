Installation
!!!!!!!!!!!!

seqrepo has been tested only on Ubuntu 14.04 and 16.04.  It requires
separate installation of the tabix package.  It requires sqlite3 >=
3.8.0, which likely precludes early Ubuntu distributions.

On Ubuntu 16.04::

  sudo apt install -y python3-dev gcc zlib1g-dev tabix
  pip install seqrepo
