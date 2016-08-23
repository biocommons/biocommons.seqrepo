import os
import shutil
import tempfile

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
    faw.close()

    # now read them back
    far = FabgzReader(fabgz_fn)
    assert set(far.keys()) == set(sequences.keys())

    for seq_id in far.keys():
        assert far.fetch(seq_id) == sequences[seq_id]

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    test_write_reread()
