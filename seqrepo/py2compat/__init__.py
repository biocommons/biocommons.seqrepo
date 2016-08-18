import gzip
import io

import six

if six.PY2:

    from .lru_cache import lru_cache
    from .makedirs import makedirs

    def gzip_open_encoded(file, encoding=None):
        return io.TextIOWrapper(io.BufferedReader(gzip.open(file)), encoding="utf8")

else:

    from os import makedirs
    from functools import lru_cache

    def gzip_open_encoded(file, encoding=None):
        return gzip.open(file, mode="rt", encoding=encoding)
