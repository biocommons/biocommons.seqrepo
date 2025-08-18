"""Get and store sequence aliases in a sqlite db."""

import datetime
import logging
import sqlite3
from collections.abc import Iterator
from importlib import resources

import yoyo

from biocommons.seqrepo._internal.translate import translate_alias_records, translate_api2db

_logger = logging.getLogger(__name__)


expected_schema_version = 1

min_sqlite_version_info = (3, 8, 0)
if sqlite3.sqlite_version_info < min_sqlite_version_info:  # pragma: no cover
    min_sqlite_version = ".".join(map(str, min_sqlite_version_info))
    msg = f"{__package__} requires sqlite3 >= {min_sqlite_version} but {sqlite3.sqlite_version} is installed"
    raise ImportError(msg)


sqlite3.register_converter("timestamp", lambda val: datetime.datetime.fromisoformat(val.decode()))


class SeqAliasDB:
    """Implements a sqlite database of sequence aliases"""

    def __init__(
        self,
        db_path: str,
        writeable: bool = False,
        translate_ncbi_namespace: str | None = None,
        check_same_thread: bool = True,
    ) -> None:
        """Initialize SeqAliasDB instance."""
        self._db_path = db_path
        self._writeable = writeable

        if translate_ncbi_namespace is not None:
            _logger.warning(
                "translate_ncbi_namespace is obsolete; translation is now automatic; "
                "this flag will be removed"
            )

        if self._writeable:
            self._upgrade_db()
        self._db = sqlite3.connect(
            self._db_path,
            check_same_thread=check_same_thread,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._db.row_factory = sqlite3.Row
        schema_version = self.schema_version()
        # if we're not at the expected schema version for this code, bail
        if schema_version != expected_schema_version:  # pragma: no cover
            raise RuntimeError(
                f"Upgrade required: Database schema version is {schema_version} and code expects {expected_schema_version}"
            )

    # ############################################################################
    # Special methods

    def __del__(self) -> None:
        self._db.close()

    def __contains__(self, seq_id: str) -> bool:
        cursor = self._db.cursor()
        cursor.execute(
            "select exists(select 1 from seqalias where seq_id = ? limit 1) as ex",
            (seq_id,),
        )
        c = cursor.fetchone()
        return bool(c["ex"])

    # ############################################################################
    # Public methods

    def commit(self) -> None:
        """Commit changes to DB"""
        if self._writeable:
            self._db.commit()

    def fetch_aliases(
        self, seq_id: str, current_only: bool = True, translate_ncbi_namespace: str | None = None
    ) -> list[dict]:
        """Return list of alias annotation records (dicts) for a given seq_id"""
        _logger.warning(
            "SeqAliasDB::fetch_aliases() is deprecated; use find_aliases(seq_id=...) instead"
        )
        if translate_ncbi_namespace is not None:
            _logger.warning(
                "translate_ncbi_namespace is obsolete; translation is now automatic; "
                "this flag will be removed"
            )
        return [dict(r) for r in self.find_aliases(seq_id=seq_id, current_only=current_only)]

    def find_aliases(
        self,
        seq_id: str | None = None,
        namespace: str | None = None,
        alias: str | None = None,
        current_only: bool = True,
        translate_ncbi_namespace: bool | None = None,
    ) -> Iterator[dict]:
        """Return iterator over alias annotation dicts that match criteria

        The arguments, all optional, restrict the records that are
        returned.  Without arguments, all aliases are returned.

        Regardless of arguments, results are ordered by seq_id.

        If arguments contain %, the `like` comparison operator is
        used.  Otherwise arguments must match exactly.

        """
        clauses = []
        params = []

        def eq_or_like(s: str) -> str:
            return "like" if "%" in s else "="

        if translate_ncbi_namespace is not None:
            _logger.warning(
                "translate_ncbi_namespace is obsolete; translation is now automatic; "
                "this flag will be removed"
            )

        if namespace is not None:
            ns_api2db = translate_api2db(namespace, alias)
            if ns_api2db:
                namespace, alias = ns_api2db[0]
            clauses += [f"namespace {eq_or_like(namespace)} ?"]
            params += [namespace]
        if alias is not None:
            clauses += [f"alias {eq_or_like(alias)} ?"]
            params += [alias]
        if seq_id is not None:
            clauses += [f"seq_id {eq_or_like(seq_id)} ?"]
            params += [seq_id]
        if current_only:
            clauses += ["is_current = 1"]

        cols = ["seqalias_id", "seq_id", "alias", "added", "is_current"]
        cols += ["namespace"]
        sql = "select {cols} from seqalias".format(cols=", ".join(cols))  # noqa: S608
        if clauses:
            sql += " where " + " and ".join("(" + c + ")" for c in clauses)
        sql += " order by seq_id, namespace, alias"

        _logger.debug("Executing: %s with params %s", sql, params)
        cursor = self._db.cursor()
        cursor.execute(sql, params)
        return translate_alias_records(dict(r) for r in cursor)

    def schema_version(self) -> int:
        """Return schema version as integer"""
        cursor = self._db.cursor()
        cursor.execute("select value from meta where key = 'schema version'")
        return int(cursor.fetchone()[0])

    def stats(self) -> dict:
        """Get entry stats"""
        sql = """select count(*) as n_aliases, sum(is_current) as n_current,
        count(distinct seq_id) as n_sequences, count(distinct namespace) as
        n_namespaces, min(added) as min_ts, max(added) as max_ts from
        seqalias;"""
        cursor = self._db.cursor()
        cursor.execute(sql)
        return dict(cursor.fetchone())

    def store_alias(self, seq_id: str, namespace: str, alias: str) -> None | str | int:
        """Associate a namespaced alias with a sequence

        Alias association with sequences is idempotent: duplicate
        associations are discarded silently.

        """
        if not self._writeable:
            raise RuntimeError("Cannot write -- opened read-only")

        ns_api2db = translate_api2db(namespace, alias)
        if ns_api2db:
            namespace, new_alias = ns_api2db[0]
            if new_alias is not None:
                alias = new_alias

        log_pfx = f"store({seq_id},{namespace},{alias})"
        cursor = self._db.cursor()
        try:
            cursor.execute(
                "insert into seqalias (seq_id, namespace, alias) values (?, ?, ?)",
                (seq_id, namespace, alias),
            )
            # success => new record
            return cursor.lastrowid  # noqa: TRY300
        except Exception as ex:
            # Every driver has own class for IntegrityError so we have to
            # investigate if the exception class name contains 'IntegrityError'
            # which we can ignore
            if not type(ex).__name__.endswith("IntegrityError"):
                raise
        # IntegrityError fall-through

        # existing record is guaranteed to exist uniquely; fetchone() should always succeed
        current_rec = next(self.find_aliases(namespace=namespace, alias=alias))

        # if seq_id matches current record, it's a duplicate (seq_id, namespace, alias) tuple
        # and we return current record
        if current_rec["seq_id"] == seq_id:
            _logger.debug("%s: duplicate record", log_pfx)
            return current_rec["seqalias_id"]

        # otherwise, we're reassigning; deprecate old record, then retry
        _logger.debug("%s: collision; deprecating %s", log_pfx, current_rec["seq_id"])
        cursor.execute(
            "update seqalias set is_current = 0 where seqalias_id = ?",
            [current_rec["seqalias_id"]],
        )
        return self.store_alias(seq_id, namespace, alias)

    # ############################################################################
    # Internal methods

    def _dump_aliases(self) -> None:  # pragma: no cover
        import prettytable  # noqa: PLC0415

        cursor = self._db.cursor()
        fields = ["seqalias_id", "seq_id", "namespace", "alias", "added", "is_current"]
        pt = prettytable.PrettyTable(field_names=fields)
        cursor.execute("select * from seqalias")
        for r in cursor:
            pt.add_row([r[f] for f in fields])
        print(pt)  # noqa: T201

    def _upgrade_db(self) -> None:
        """Upgrade db using scripts for specified (current) schema version"""
        migration_path = "_data/migrations"
        sqlite3.connect(self._db_path).close()  # ensure that it exists
        db_url = "sqlite:///" + self._db_path
        backend = yoyo.get_backend(db_url)
        if __package__ is None:
            msg = (
                "__package__ is None. This module must be part of a package to "
                "resolve the migration files path."
            )
            raise ImportError(msg)
        migration_dir = str(resources.files(__package__) / migration_path)
        migrations = yoyo.read_migrations(migration_dir)
        if len(migrations) <= 0:
            raise FileNotFoundError(
                f"no migration scripts found -- wrong migration path for {__package__}"
            )
        migrations_to_apply = backend.to_apply(migrations)
        backend.apply_migrations(migrations_to_apply)
