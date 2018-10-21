import itertools
import logging
import sqlite3

import pkg_resources
import yoyo

_logger = logging.getLogger(__name__)

expected_schema_version = 1

min_sqlite_version_info = (3, 8, 0)
if sqlite3.sqlite_version_info < min_sqlite_version_info:    # pragma: no cover
    min_sqlite_version = ".".join(map(str, min_sqlite_version_info))
    msg = "{} requires sqlite3 >= {} but {} is installed".format(__package__, min_sqlite_version,
                                                                 sqlite3.sqlite_version)
    raise ImportError(msg)


class SeqAliasDB(object):
    """Implements a sqlite database of sequence aliases

    """

    def __init__(self, db_path, writeable=False, translate_ncbi_namespace=False):
        self._db_path = db_path
        self._db = None
        self._writeable = writeable
        self.translate_ncbi_namespace = translate_ncbi_namespace

        if self._writeable:
            self._upgrade_db()

        self._db = sqlite3.connect(self._db_path)
        schema_version = self.schema_version()
        self._db.row_factory = sqlite3.Row

        # if we're not at the expected schema version for this code, bail
        if schema_version != expected_schema_version:    # pragma: no cover
            raise RuntimeError("Upgrade required: Database schema"
                               "version is {} and code expects {}".format(schema_version, expected_schema_version))

    # ############################################################################
    # Special methods

    def __contains__(self, seq_id):
        c = self._db.execute("select exists(select 1 from seqalias where seq_id = ? limit 1) as ex",
                             (seq_id, )).fetchone()
        return True if c["ex"] else False

    # ############################################################################
    # Public methods

    def commit(self):
        if self._writeable:
            self._db.commit()

    def fetch_aliases(self, seq_id, current_only=True):
        """return list of alias annotation records (dicts) for a given seq_id"""
        return [dict(r) for r in self.find_aliases(seq_id=seq_id, current_only=current_only)]

    def find_aliases(self, seq_id=None, namespace=None, alias=None, current_only=True, translate_ncbi_namespace=None):
        """returns iterator over alias annotation records that match criteria
        
        The arguments, all optional, restrict the records that are
        returned.  Without arguments, all aliases are returned.

        If arguments contain %, the `like` comparison operator is
        used.  Otherwise arguments must match exactly.

        """
        clauses = []
        params = []

        def eq_or_like(s):
            return "like" if "%" in s else "="

        if translate_ncbi_namespace is None:
            translate_ncbi_namespace = self.translate_ncbi_namespace
        if alias is not None:
            clauses += ["alias {} ?".format(eq_or_like(alias))]
            params += [alias]
        if namespace is not None:
            # Switch to using RefSeq for RefSeq accessions
            # issue #38: translate "RefSeq" to "NCBI" to enable RefSeq lookups
            # issue #31: later breaking change, translate database
            if namespace == "RefSeq":
                namespace = "NCBI"
            clauses += ["namespace {} ?".format(eq_or_like(namespace))]
            params += [namespace]
        if seq_id is not None:
            clauses += ["seq_id {} ?".format(eq_or_like(seq_id))]
            params += [seq_id]
        if current_only:
            clauses += ["is_current = 1"]

        cols = ["seqalias_id", "seq_id", "alias", "added", "is_current"]
        if translate_ncbi_namespace:
            cols += ["case namespace when 'NCBI' then 'RefSeq' else namespace end as namespace"]
        else:
            cols += ["namespace"]
        sql = "select {cols} from seqalias".format(cols=", ".join(cols))
        if clauses:
            sql += " where " + " and ".join("(" + c + ")" for c in clauses)
        sql += " order by seq_id, namespace, alias"

        _logger.debug("Executing: " + sql)
        return self._db.execute(sql, params)

    def schema_version(self):
        """return schema version as integer"""
        return int(self._db.execute("select value from meta where key = 'schema version'").fetchone()[0])

    def stats(self):
        sql = """select count(*) as n_aliases, sum(is_current) as n_current,
        count(distinct seq_id) as n_sequences, count(distinct namespace) as
        n_namespaces, min(added) as min_ts, max(added) as max_ts from
        seqalias;"""
        return dict(self._db.execute(sql).fetchone())

    def store_alias(self, seq_id, namespace, alias):
        """associate a namespaced alias with a sequence

        Alias association with sequences is idempotent: duplicate
        associations are discarded silently.

        """

        if not self._writeable:
            raise RuntimeError("Cannot write -- opened read-only")

        log_pfx = "store({q},{n},{a})".format(n=namespace, a=alias, q=seq_id)
        try:
            c = self._db.execute("insert into seqalias (seq_id, namespace, alias) values (?, ?, ?)", (seq_id, namespace,
                                                                                                      alias))
            # success => new record
            return c.lastrowid
        except sqlite3.IntegrityError:
            pass

        # IntegrityError fall-through

        # existing record is guaranteed to exist uniquely; fetchone() should always succeed
        current_rec = self.find_aliases(namespace=namespace, alias=alias).fetchone()

        # if seq_id matches current record, it's a duplicate (seq_id, namespace, alias) tuple
        # and we return current record
        if current_rec["seq_id"] == seq_id:
            _logger.debug(log_pfx + ": duplicate record")
            return current_rec["seqalias_id"]

        # otherwise, we're reassigning; deprecate old record, then retry
        _logger.debug(log_pfx + ": collision; deprecating {s1}".format(s1=current_rec["seq_id"]))
        self._db.execute("update seqalias set is_current = 0 where seqalias_id = ?", [current_rec["seqalias_id"]])
        return self.store_alias(seq_id, namespace, alias)


    # ############################################################################
    # Internal methods

    def _dump_aliases(self):    # pragma: no cover
        import prettytable
        fields = "seqalias_id seq_id namespace alias added is_current".split()
        pt = prettytable.PrettyTable(field_names=fields)
        for r in self._db.execute("select * from seqalias"):
            pt.add_row([r[f] for f in fields])
        print(pt)

    def _upgrade_db(self):
        """upgrade db using scripts for specified (current) schema version"""
        migration_path = "_data/migrations"
        sqlite3.connect(self._db_path).close()    # ensure that it exists
        db_url = "sqlite:///" + self._db_path
        backend = yoyo.get_backend(db_url)
        migration_dir = pkg_resources.resource_filename(__package__, migration_path)
        migrations = yoyo.read_migrations(migration_dir)
        assert len(migrations) > 0, "no migration scripts found -- wrong migraion path for " + __package__
        migrations_to_apply = backend.to_apply(migrations)
        backend.apply_migrations(migrations_to_apply)
