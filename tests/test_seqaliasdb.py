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

    alias_keys = "seqalias_id seq_id namespace alias is_current".split()
    aliases = [{k: r[k] for k in alias_keys} for r in db.find_aliases(current_only=False)]
    aliases.sort(key=lambda r: (r["seqalias_id"], r["seq_id"], r["namespace"], r["alias"], r["is_current"]))

    assert aliases == [{
        'seqalias_id': 1,
        'seq_id': 'q1',
        'namespace': 'A',
        'alias': '1',
        'is_current': 0
    }, {
        'seqalias_id': 2,
        'seq_id': 'q1',
        'namespace': 'A',
        'alias': '2',
        'is_current': 1
    }, {
        'seqalias_id': 3,
        'seq_id': 'q1',
        'namespace': 'B',
        'alias': '1',
        'is_current': 1
    }, {
        'seqalias_id': 4,
        'seq_id': 'q2',
        'namespace': 'A',
        'alias': '1',
        'is_current': 1
    }]

    # __contains__
    assert "q1" in db
    assert "q9" not in db

    assert db.stats()["n_sequences"] == 2

    del db    # close
    db = SeqAliasDB(db_path)

    with pytest.raises(RuntimeError):
        db.store_alias("q1", "A", "1")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test_seqinfo()
