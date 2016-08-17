import sqlite3
import pytest

min_sqlite_version_info = (3, 8, 0)
min_sqlite_version = ".".join(map(str, min_sqlite_version_info))
require_min_sqlite_version = pytest.mark.skipif(
    sqlite3.sqlite_version_info < min_sqlite_version_info,
    reason="requires sqlite3 >= " + min_sqlite_version + " (https://github.com/biocommons/seqrepo/issues/1)")
