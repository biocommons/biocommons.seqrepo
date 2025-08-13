import shutil
import tempfile
from pathlib import Path

import pytest

from biocommons.seqrepo.fastadir.fabgz import FabgzReader, FabgzWriter

seed = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
sequences = {f"l{b}": seed * b for b in (1, 10, 100, 1000, 10000)}


def test_write_reread():
    # PY2BAGGAGE: Switch to TemporaryDirectory
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")

    fabgz_fn = Path(tmpdir) / "test.fa.bgz"

    # write sequences
    faw = FabgzWriter(str(fabgz_fn))
    for seq_id, seq in sequences.items():
        faw.store(seq_id, seq)
    # add twice to demonstrate non-redundancy
    for seq_id, seq in sequences.items():
        faw.store(seq_id, seq)
    faw.close()

    # now read them back
    far = FabgzReader(fabgz_fn)
    assert far.filename.startswith(tmpdir.encode())
    assert set(far.keys()) == set(sequences.keys())
    assert len(far) == 5, "expected 5 sequences"
    assert "l10" in far.keys()  # noqa: SIM118
    assert far["l10"] == seed * 10
    for seq_id in far.keys():  # noqa: SIM118
        assert far.fetch(seq_id) == sequences[seq_id]

    shutil.rmtree(tmpdir)


def test_errors():
    with pytest.raises(RuntimeError):
        _ = FabgzWriter("/tmp/badsuffix")  # noqa: S108


if __name__ == "__main__":
    test_write_reread()
