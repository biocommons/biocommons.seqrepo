import logging
import os
import sqlite3

import pkg_resources
import yoyo

from ..exceptions import SeqRepoError

logger = logging.getLogger(__name__)

expected_schema_version = 1


min_sqlite_version_info = (3, 8, 0)
if sqlite3.sqlite_version_info < min_sqlite_version_info:
    min_sqlite_version = ".".join(map(str, min_sqlite_version_info))
    msg = "{} requires sqlite3 >= {} but {} is installed".format(
        __package__, min_sqlite_version, sqlite3.sqlite_version)
    logger.critical(msg)
    raise SeqRepoError(msg)


class SeqAliasDB(object):
    """Implements a sqlite database of sequence aliases

    """

    def __init__(self, db_path):
        self._db_path = db_path
        self._db = None

        self._upgrade_db()

        self._db = sqlite3.connect(self._db_path)
        schema_version = self.schema_version()
        self._db.row_factory = sqlite3.Row

        # if we're not at the expected schema version for this code, bail
        if schema_version != expected_schema_version:
            raise RuntimeError("""Upgrade required: Database schema
            version is {} and code expects {}""".format(
                schema_version, expected_schema_version))

    def schema_version(self):
        """return schema version as integer"""
        try:
            return int(
                self._db.execute(
                    "select value from meta where key = 'schema version'").fetchone(
                    )[0])
        except sqlite3.OperationalError:
            return None

    def fetch_aliases(self, seq_id):
        """return list of alias annotation records (dicts) for a given seq_id"""
        return self._db.execute("select * from seqalias where seq_id = ?",
                                [seq_id]).fetchall()

    def store_alias(self, seq_id, namespace, alias):
        """associate a namespaced alias with a sequence

        Alias association with sequences is idempotent: duplicate
        associations are discarded silently.

        """
        log_pfx = "store({q},{n},{a})".format(n=namespace, a=alias, q=seq_id)
        try:
            c = self._db.execute(
                "insert into seqalias (seq_id, namespace, alias) values (?, ?, ?)",
                (seq_id, namespace, alias))
            return c.lastrowid
        except sqlite3.IntegrityError:
            pass

        # IntegrityError fall-through
        logger.debug(log_pfx + ": collision")

        # this record is guaranteed to exist uniquely
        current_rec = self.find_aliases(
            namespace=namespace, alias=alias).fetchone()

        # if seq_id matches current record, it's a duplicate (seq_id, namespace, alias) tuple
        if current_rec["seq_id"] == seq_id:
            logger.debug(log_pfx + ": seq_id match")
            return current_rec["seqalias_id"]

        # otherwise, we're reassigning; deprecate old record, then retry
        logger.debug(log_pfx + ": deprecating {s1}".format(s1=current_rec[
            "seq_id"]))
        self._db.execute(
            "update seqalias set is_current = 0 where seqalias_id = ?",
            [current_rec["seqalias_id"]])
        return self.store_alias(seq_id, namespace, alias)

    def find_aliases(self, namespace=None, alias=None, current_only=True):
        """returns iterator over alias annotation records that match criteria
        
        The optional namespace and alias selectors restrict the
        records that are returned.  If these are not provided, all
        aliases are returned. 

        """
        clauses = []
        params = []

        def eq_or_like(s):
            return "like" if "%" in s else "="

        if namespace is not None:
            clauses += ["namespace {} ?".format(eq_or_like(namespace))]
            params += [namespace]
        if alias is not None:
            clauses += ["alias {} ?".format(eq_or_like(alias))]
            params += [alias]
        if current_only:
            clauses += ["is_current = 1"]
        sql = "select * from seqalias"
        if clauses:
            sql += " where " + " and ".join("(" + c + ")" for c in clauses)
        logger.debug("Executing: " + sql)
        return self._db.execute(sql, params)

    def commit(self):
        self._db.commit()

    # TODO: This should search as ns:a not seq_id
    def __contains__(self, seq_id):
        c = self._db.execute(
            "select exists(select 1 from seqalias where seq_id = ? limit 1) as ex",
            (seq_id, )).fetchone()
        return True if c["ex"] else False

    def _upgrade_db(self):
        """upgrade db using scripts for specified (current) schema version"""
        migration_path = "_data/migrations"
        sqlite3.connect(self._db_path).close()  # ensure that it exists
        db_url = "sqlite:///" + self._db_path
        backend = yoyo.get_backend(db_url)
        migration_dir = pkg_resources.resource_filename(__package__,
                                                        migration_path)
        migrations = yoyo.read_migrations(migration_dir)
        assert len(
            migrations) > 0, "no migration scripts found -- wrong migraion path for " + __package__
        migrations_to_apply = backend.to_apply(migrations)
        backend.apply_migrations(migrations_to_apply)

    def _dump_aliases(self):
        import prettytable
        fields = "seqalias_id seq_id namespace alias added is_current".split()
        pt = prettytable.PrettyTable(field_names=fields)
        for r in self._db.execute("select * from seqalias"):
            pt.add_row([r[f] for f in fields])
        print(pt)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)

    from seqrepo.seqrepo import SeqRepo
    sr = SeqRepo("/tmp")
    sr.store("AAA", [{"namespace": "A", "alias": "B"}])
