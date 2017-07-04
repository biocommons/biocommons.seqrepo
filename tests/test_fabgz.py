import os
import shutil
import tempfile

import pytest
import six

from biocommons.seqrepo.fastadir.fabgz import FabgzReader, FabgzWriter

seed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
sequences = {"l{l}".format(l=l): seed * l for l in (1, 10, 100, 1000, 10000)}


def test_write_reread():
    # PY2BAGGAGE: Switch to TemporaryDirectory
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")

    fabgz_fn = os.path.join(tmpdir, "test.fa.bgz")

    # write sequences
    faw = FabgzWriter(fabgz_fn)
    for seq_id, seq in six.iteritems(sequences):
        faw.store(seq_id, seq)
    # add twice to demonstrate non-redundancy
    for seq_id, seq in six.iteritems(sequences):
        faw.store(seq_id, seq)
    faw.close()

    # now read them back
    far = FabgzReader(fabgz_fn)
    assert far.filename.startswith("/tmp/".encode())
    assert set(far.keys()) == set(sequences.keys())
    assert 5 == len(far), "expected 5 sequences"
    assert "l10" in far.keys()
    assert far["l10"] == seed * 10
    for seq_id in far.keys():
        assert far.fetch(seq_id) == sequences[seq_id]

    shutil.rmtree(tmpdir)


def test_errors():
    with pytest.raises(RuntimeError):
        far = FabgzWriter("/tmp/badsuffix")


if __name__ == "__main__":
    test_write_reread()
