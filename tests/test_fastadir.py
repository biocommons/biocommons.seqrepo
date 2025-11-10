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


def test_schema_version():
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")
    orig_schema_version = FastaDir.schema_version

    with pytest.raises(RuntimeError):
        FastaDir.schema_version = lambda self: -1
        fd = FastaDir(tmpdir, writeable=True)

    FastaDir.schema_version = orig_schema_version


def test_writeability():
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_")
    fd = FastaDir(tmpdir, writeable=True)

    with pytest.raises(RuntimeError):
        fd._writeable = False
        fd.store("NC_000001.11", "TGGTGGCACGCGCTTGTAGT")

    fd._writeable = True


def test_context_manager():
    """Test FastaDir context manager support"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_ctx_")

    # Test with statement for resource cleanup
    with FastaDir(tmpdir, writeable=True) as fd:
        fd.store("seq1", "ATCGATCG")
        fd.store("seq2", "GCTAGCTA")
        fd.commit()
        assert fd.fetch("seq1") == "ATCGATCG"

    # After exiting context, database should be closed
    # We can verify by reopening the directory
    fd_reopened = FastaDir(tmpdir, writeable=False)
    assert fd_reopened.fetch("seq1") == "ATCGATCG"
    assert fd_reopened.fetch("seq2") == "GCTAGCTA"
    fd_reopened.close()

    shutil.rmtree(tmpdir)


def test_explicit_close():
    """Test explicit close() method on FastaDir"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_close_")

    fd = FastaDir(tmpdir, writeable=True)
    fd.store("seq1", "ATCGATCG")
    fd.commit()

    # Explicitly close the directory
    fd.close()

    # Verify we can reopen without issues
    fd_reopened = FastaDir(tmpdir, writeable=False)
    assert fd_reopened.fetch("seq1") == "ATCGATCG"
    fd_reopened.close()

    shutil.rmtree(tmpdir)


def test_close_multiple_times():
    """Test that close() is safe to call multiple times on FastaDir"""
    tmpdir = tempfile.mkdtemp(prefix="seqrepo_pytest_multi_")

    fd = FastaDir(tmpdir, writeable=True)
    fd.store("seq1", "ATCGATCG")
    fd.commit()

    # Should be safe to call close() multiple times
    fd.close()
    fd.close()  # Should not raise an exception

    fd_reopened = FastaDir(tmpdir, writeable=False)
    assert fd_reopened.fetch("seq1") == "ATCGATCG"
    fd_reopened.close()

    shutil.rmtree(tmpdir)
