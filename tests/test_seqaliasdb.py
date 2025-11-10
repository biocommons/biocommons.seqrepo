import os
import shutil
import tempfile

import pytest

from biocommons.seqrepo.seqaliasdb import SeqAliasDB


def test_seqinfo():
    # PY2BAGGAGE: Switch to TemporaryDirectory
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")

    db_path = os.path.join(tmpdir, "aliases.sqlite3")

    db = SeqAliasDB(db_path, writeable=True)

    # A:1 -> q1
    aid = db.store_alias("q1", "A", "1")
    assert aid == 1

    # A:1 -> q1 (duplicate)
    aid = db.store_alias("q1", "A", "1")
    assert aid == 1, "created new alias_id for duplicate (nsA, alias1) record"

    # A:2 -> q1 (new alias in same namespace)
    aid = db.store_alias("q1", "A", "2")
    assert aid == 2, "created new alias_id for duplicate (nsA, alias1) record"

    # B:1 -> q1 (new namespace, same alias, same sequence)
    aid = db.store_alias("q1", "B", "1")
    assert aid == 3, "created new alias_id for duplicate (nsA, alias1) record"

    # A:1 -> q2 (reassign)
    aid = db.store_alias("q2", "A", "1")
    assert aid == 4, "should have created a new alias_id on reassignment of new sequence"

    alias_keys = ["seqalias_id", "seq_id", "namespace", "alias", "is_current"]
    aliases = [{k: r[k] for k in alias_keys} for r in db.find_aliases(current_only=False)]
    aliases.sort(
        key=lambda r: (
            r["seqalias_id"],
            r["seq_id"],
            r["namespace"],
            r["alias"],
            r["is_current"],
        )
    )

    assert aliases == [
        {
            "seqalias_id": 1,
            "seq_id": "q1",
            "namespace": "A",
            "alias": "1",
            "is_current": 0,
        },
        {
            "seqalias_id": 2,
            "seq_id": "q1",
            "namespace": "A",
            "alias": "2",
            "is_current": 1,
        },
        {
            "seqalias_id": 3,
            "seq_id": "q1",
            "namespace": "B",
            "alias": "1",
            "is_current": 1,
        },
        {
            "seqalias_id": 4,
            "seq_id": "q2",
            "namespace": "A",
            "alias": "1",
            "is_current": 1,
        },
    ]

    # __contains__
    assert "q1" in db
    assert "q9" not in db

    assert db.stats()["n_sequences"] == 2

    del db  # close
    db = SeqAliasDB(db_path)

    with pytest.raises(RuntimeError):
        db.store_alias("q1", "A", "1")

    shutil.rmtree(tmpdir)


def test_context_manager():
    """Test SeqAliasDB context manager support"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_alias_ctx_")
    db_path = os.path.join(tmpdir, "aliases.sqlite3")

    # Test with statement for resource cleanup
    with SeqAliasDB(db_path, writeable=True) as db:
        db.store_alias("seq1", "test", "alias1")
        db.store_alias("seq2", "test", "alias2")
        db.commit()
        assert "seq1" in db
        assert "seq2" in db

    # After exiting context, database should be closed
    # Verify by reopening
    db_reopened = SeqAliasDB(db_path, writeable=False)
    assert "seq1" in db_reopened
    assert "seq2" in db_reopened
    db_reopened.close()

    shutil.rmtree(tmpdir)


def test_explicit_close_seqaliasdb():
    """Test explicit close() method on SeqAliasDB"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_alias_close_")
    db_path = os.path.join(tmpdir, "aliases.sqlite3")

    db = SeqAliasDB(db_path, writeable=True)
    db.store_alias("seq1", "test", "alias1")
    db.commit()

    # Explicitly close the database
    db.close()

    # Verify we can reopen without issues
    db_reopened = SeqAliasDB(db_path, writeable=False)
    assert "seq1" in db_reopened
    db_reopened.close()

    shutil.rmtree(tmpdir)


def test_close_multiple_times_seqaliasdb():
    """Test that close() is safe to call multiple times on SeqAliasDB"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_alias_multi_")
    db_path = os.path.join(tmpdir, "aliases.sqlite3")

    db = SeqAliasDB(db_path, writeable=True)
    db.store_alias("seq1", "test", "alias1")
    db.commit()

    # Should be safe to call close() multiple times
    db.close()
    db.close()  # Should not raise an exception

    db_reopened = SeqAliasDB(db_path, writeable=False)
    assert "seq1" in db_reopened
    db_reopened.close()

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test_seqinfo()
