import shutil
import tempfile

import pytest

from biocommons.seqrepo.fastadir import FastaDir


def test_write_reread():
    # PY2BAGGAGE: Switch to TemporaryDirectory
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")

    fd = FastaDir(tmpdir, writeable=True)

    assert fd.store("1", "seq1") == "1"
    assert fd.store("2", "seq2") == "2"
    fd.commit()
    assert fd.store("3", "seq3") == "3"

    assert fd.fetch("1") == "seq1"
    assert fd.fetch("2") == "seq2"
    assert fd.fetch("3") == "seq3"

    assert "3" in fd

    assert len(fd) == 3

    assert fd["3"] == "seq3", "test __getitem__ lookup"

    with pytest.raises(KeyError):
        fd.fetch("bogus")

    shutil.rmtree(tmpdir)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    test_write_reread()
