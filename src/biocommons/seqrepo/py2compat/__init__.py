import gzip
import io

import six

try:
    from functools import lru_cache    # Python >= 3.2
except ImportError:
    from ._lru_cache import lru_cache

try:
    from shutil import which    # Python >= 3.3
except ImportError:
    from ._which import which

try:
    from os.path import commonpath    # Python >= 3.5
except ImportError:
    from ._commonpath import commonpath

if six.PY2:    # pragma: no cover

    from ._makedirs import makedirs, FileExistsError

    def gzip_open_encoded(file, encoding=None):
        return io.TextIOWrapper(io.BufferedReader(gzip.open(file)), encoding="utf8")

else:    # pragma: no cover

    from os import makedirs     # flake8: noqa
    FileExistsError = FileExistsError

    def gzip_open_encoded(file, encoding=None):
        return gzip.open(file, mode="rt", encoding=encoding)
