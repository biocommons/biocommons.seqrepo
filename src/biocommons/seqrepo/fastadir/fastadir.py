"""Provide quick access a directory of block-gzipped FASTA files"""

import datetime
import functools
import importlib.resources
import logging
import os
import sqlite3
import time
from collections.abc import Iterator
from typing import Any

import yoyo

from biocommons.seqrepo.config import SEQREPO_LRU_CACHE_MAXSIZE
from biocommons.seqrepo.fastadir.bases import BaseReader, BaseWriter
from biocommons.seqrepo.fastadir.fabgz import FabgzReader, FabgzWriter

_logger = logging.getLogger(__name__)

# expected_schema_version must match (exactly) the schema version
# stored in the associated database. If newer code introduces schema
# changes, a database upgrade will be attempted automatically. If
# older code tries to open a database with a newer schema, the code
# will fail.

# This has two important implications: 1) system wide installations
# will be on one version, and all users must update code to match; 2)
# opening two repositories with different versions is not possible.

expected_schema_version = 1


class FastaDir(BaseReader, BaseWriter):
    """Provide a simple key-value interface to a directory of compressed fasta files.

    Sequences are stored in dated fasta files. Dating the files
    enables compact storage with multiple releases (using hard links)
    and efficient incremental updates and transfers (e.g., via rsync).
    The fasta files are compressed with block gzip, enabling fast
    random access to arbitrary regions of even large (chromosome-size)
    sequences (thanks to pysam.FastaFile).

    When the key is a hash based on sequence (e.g., SHA512), the
    combination provides a convenient non-redundant storage of
    sequences, with fast access to sequences and sequence slices,
    compact storage and easy replication.

    The two primary methods are:

        * seq_id <- store(seq, seq_id): store a sequence
        * seq <- fetch(seq_id, [s, e]): return sequence (slice)

    """

    def __init__(
        self,
        root_dir: str,
        writeable: bool = False,
        check_same_thread: bool = True,
        fd_cache_size: int | None = 0,
    ) -> None:
        """Create a new sequence repository if necessary, and then open it"""
        self._root_dir = root_dir
        self._db_path = os.path.join(self._root_dir, "db.sqlite3")
        self._writing = None
        self._writeable = writeable

        if self._writeable:
            os.makedirs(self._root_dir, exist_ok=True)
            self._upgrade_db()

        self._db = sqlite3.connect(
            self._db_path,
            check_same_thread=check_same_thread,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        schema_version = self.schema_version()
        self._db.row_factory = sqlite3.Row

        # if we're not at the expected schema version for this code, bail
        if schema_version != expected_schema_version:
            raise RuntimeError(
                f"""Upgrade required: Database schema
            version is {schema_version} and code expects {expected_schema_version}"""
            )

        if fd_cache_size == 0:
            _logger.info("File descriptor caching disabled")
        else:
            _logger.warning("File descriptor caching enabled (size=%s)", fd_cache_size)

        @functools.lru_cache(maxsize=fd_cache_size)
        def _open_for_reading(path: str) -> FabgzReader:
            if fd_cache_size == 0:
                _logger.debug("Opening for reading uncached: %s", path)
            return FabgzReader(path)

        self._open_for_reading = _open_for_reading

    def __del__(self) -> None:
        self._db.close()

    # ############################################################################
    # Special methods

    def __contains__(self, seq_id: str) -> bool:
        c = self._fetch_one(
            "select exists(select 1 from seqinfo where seq_id = ? limit 1) as ex",
            (seq_id,),
        )

        return bool(c["ex"])

    def __iter__(self) -> Iterator[dict]:
        sql = "select * from seqinfo order by seq_id"
        cursor = self._db.cursor()
        cursor.execute(sql)
        for rec in cursor:
            recd = dict(rec)
            recd["seq"] = self.fetch(rec["seq_id"])
            yield recd
        cursor.close()

    def __len__(self) -> int:
        return self.stats()["n_sequences"]

    # ############################################################################
    # Public methods

    def commit(self) -> None:
        """Commit changes to DB"""
        if self._writing is not None:
            self._writing["fabgz"].close()
            self._db.commit()
            self._writing = None

    def fetch(self, seq_id: str, start: int | None = None, end: int | None = None) -> str:
        """Fetch sequence by seq_id, optionally with start, end bounds"""
        rec = self.fetch_seqinfo(seq_id)

        if self._writing and self._writing["relpath"] == rec["relpath"]:
            _logger.warning(
                "Fetching from file opened for writing; closing first (%s)", (rec["relpath"])
            )
            self.commit()

        path = os.path.join(self._root_dir, rec["relpath"])

        with self._open_for_reading(path) as fabgz:
            return fabgz.fetch(seq_id, start, end)

    @functools.lru_cache(maxsize=SEQREPO_LRU_CACHE_MAXSIZE)
    def fetch_seqinfo(self, seq_id: str) -> dict:
        """Fetch sequence info by seq_id"""
        rec = self._fetch_one(
            """select * from seqinfo where seq_id = ? order by added desc""", (seq_id,)
        )

        if rec is None:
            raise KeyError(seq_id)
        return dict(rec)

    def schema_version(self) -> int | None:
        """Return schema version as integer"""
        try:
            rec = self._fetch_one("select value from meta where key = 'schema version'")
            return int(rec[0])
        except sqlite3.OperationalError:
            return None

    def stats(self) -> dict:
        """Get stats for stored sequences"""
        sql = """select count(distinct seq_id) n_sequences, sum(len) tot_length,
              min(added) min_ts, max(added) as max_ts, count(distinct relpath) as
              n_files from seqinfo"""
        return dict(self._fetch_one(sql))

    def store(self, seq_id: str, seq: str) -> str:
        """Store a sequence with key seq_id.

        The sequence itself is stored in a fasta file and a reference to it in the sqlite3 database.
        """
        if not self._writeable:
            raise RuntimeError("Cannot write -- opened read-only")

        # open a file for writing if necessary
        # path: <root_dir>/<reldir>/<basename>
        #                  <---- relpath ---->
        #       <------ dir_ ----->
        #       <----------- path ----------->
        if self._writing is None:
            reldir = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m%d/%H%M")
            basename = str(time.time()) + ".fa.bgz"
            relpath = os.path.join(reldir, basename)

            dir_ = os.path.join(self._root_dir, reldir)
            path = os.path.join(self._root_dir, reldir, basename)
            os.makedirs(dir_, exist_ok=True)
            fabgz = FabgzWriter(path)
            self._writing = {"relpath": relpath, "fabgz": fabgz}
            _logger.debug("Opened for writing: %s", path)

        self._writing["fabgz"].store(seq_id, seq)
        alpha = "".join(sorted(set(seq)))
        cursor = self._db.cursor()
        cursor.execute(
            """insert into seqinfo (seq_id, len, alpha, relpath)
                         values (?, ?, ?,?)""",
            (seq_id, len(seq), alpha, self._writing["relpath"]),
        )
        cursor.close()
        return seq_id

    # ############################################################################
    # Internal methods

    def _fetch_one(self, sql: str, params: tuple[str, ...] = ()) -> Any:  # noqa: ANN401
        cursor = self._db.cursor()
        cursor.execute(sql, params)
        val = cursor.fetchone()
        cursor.close()
        return val

    def _upgrade_db(self) -> None:
        """Upgrade db using scripts for specified (current) schema version"""
        migration_path = "_data/migrations"
        sqlite3.connect(self._db_path).close()  # ensure that it exists
        db_url = "sqlite:///" + self._db_path
        backend = yoyo.get_backend(db_url)
        if __package__ is None:
            raise ValueError("__package__ must be accessible to retrieve migration files")
        migration_dir = importlib.resources.files(__package__) / migration_path
        migrations = yoyo.read_migrations(str(migration_dir))
        migrations_to_apply = backend.to_apply(migrations)
        backend.apply_migrations(migrations_to_apply)

    def _dump_aliases(self) -> None:
        import prettytable  # noqa: PLC0415

        fields = ["seq_id", "len", "alpha", "added", "relpath"]
        pt = prettytable.PrettyTable(field_names=fields)
        cursor = self._db.cursor()
        cursor.execute("select * from seqinfo")
        for r in cursor:
            pt.add_row([r[f] for f in fields])
            print(pt)  # noqa: T201
        cursor.close()
