import datetime
import logging
import os
import sqlite3
import time

import pkg_resources
import six
import yoyo

from ..py2compat import lru_cache, makedirs

from .bases import BaseReader, BaseWriter
from .fabgz import FabgzReader, FabgzWriter

logger = logging.getLogger(__name__)

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
    """This class provides simple a simple key-value interface to a
    directory of compressed fasta files.

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

    def __init__(self, root_dir, writeable=False):
        """Creates a new sequence repository if necessary, and then opens it"""

        self._root_dir = root_dir
        self._db_path = os.path.join(self._root_dir, "db.sqlite3")
        self._writing = None
        self._db = None
        self._writeable = writeable

        if self._writeable:
            makedirs(self._root_dir, exist_ok=True)
            self._upgrade_db()

        self._db = sqlite3.connect(self._db_path)
        schema_version = self.schema_version()
        self._db.row_factory = sqlite3.Row

        # if we're not at the expected schema version for this code, bail
        if schema_version != expected_schema_version:
            raise RuntimeError("""Upgrade required: Database schema
            version is {} and code expects {}""".format(schema_version, expected_schema_version))

    # ############################################################################
    # Special methods

    def __contains__(self, seq_id):
        c = self._db.execute("select exists(select 1 from seqinfo where seq_id = ? limit 1) as ex", [seq_id]).fetchone()
        return True if c["ex"] else False

    def __iter__(self):
        sql = "select * from seqinfo order by seq_id"
        for rec in self._db.execute(sql):
            recd = dict(rec)
            recd["seq"] = self.fetch(rec["seq_id"])
            yield recd

    def __len__(self):
        return self.stats()["n_sequences"]

    # ############################################################################
    # Public methods

    def commit(self):
        if self._writing is not None:
            self._writing["fabgz"].close()
            self._db.commit()
            self._writing = None

    def fetch(self, seq_id, start=None, end=None):
        """fetch sequence by seq_id, optionally with start, end bounds

        """
        rec = self._db.execute("""select * from seqinfo where seq_id = ? order by added desc""", [seq_id]).fetchone()

        if rec is None:
            raise KeyError(seq_id)

        if self._writing and self._writing["relpath"] == rec["relpath"]:
            logger.warning("""Fetching from file opened for writing;
            closing first ({})""".format(rec["relpath"]))
            self.commit()

        path = os.path.join(self._root_dir, rec["relpath"])
        fabgz = self._open_for_reading(path)
        return fabgz.fetch(seq_id, start, end)

    def schema_version(self):
        """return schema version as integer"""
        try:
            return int(
                self._db.execute("""select value from meta
            where key = 'schema version'""").fetchone()[0])
        except sqlite3.OperationalError:
            return None

    def stats(self):
        sql = """select count(distinct seq_id) n_sequences, sum(len) tot_length,
              min(added) min_ts, max(added) as max_ts, count(distinct relpath) as
              n_files from seqinfo"""
        return dict(self._db.execute(sql).fetchone())

    def store(self, seq_id, seq):
        """store a sequence with key seq_id.  The sequence itself is stored in
        a fasta file and a reference to it in the sqlite3 database.

        """

        if not self._writeable:
            raise RuntimeError("Cannot write -- opened read-only")

        # open a file for writing if necessary
        # path: <root_dir>/<reldir>/<basename>
        #                  <---- relpath ---->
        #       <------ dir_ ----->
        #       <----------- path ----------->
        if self._writing is None:
            reldir = datetime.datetime.utcnow().strftime("%Y/%m%d/%H%M")
            basename = str(time.time()) + ".fa.bgz"
            relpath = os.path.join(reldir, basename)

            dir_ = os.path.join(self._root_dir, reldir)
            path = os.path.join(self._root_dir, reldir, basename)
            makedirs(dir_, exist_ok=True)
            fabgz = FabgzWriter(path)
            self._writing = {"relpath": relpath, "fabgz": fabgz}
            logger.info("Opened for writing: " + path)

        self._writing["fabgz"].store(seq_id, seq)
        alpha = "".join(sorted(set(seq)))
        self._db.execute("""insert into seqinfo (seq_id, len, alpha, relpath)
                         values (?, ?, ?,?)""", (seq_id, len(seq), alpha, self._writing["relpath"]))
        return seq_id

    # ############################################################################
    # Internal methods

    def _upgrade_db(self):
        """upgrade db using scripts for specified (current) schema version"""
        migration_path = "_data/migrations"
        sqlite3.connect(self._db_path).close()    # ensure that it exists
        db_url = "sqlite:///" + self._db_path
        backend = yoyo.get_backend(db_url)
        migration_dir = pkg_resources.resource_filename(__package__, migration_path)
        migrations = yoyo.read_migrations(migration_dir)
        migrations_to_apply = backend.to_apply(migrations)
        backend.apply_migrations(migrations_to_apply)

    @lru_cache()
    def _open_for_reading(self, path):
        logger.info("Opening for reading: " + path)
        return FabgzReader(path)

    def _dump_aliases(self):
        import prettytable
        fields = "seq_id len alpha added relpath".split()
        pt = prettytable.PrettyTable(field_names=fields)
        for r in self._db.execute("select * from seqinfo"):
            pt.add_row([r[f] for f in fields])
            print(pt)
