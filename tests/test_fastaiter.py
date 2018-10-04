import six
from six.moves import StringIO

import pytest

from biocommons.seqrepo.fastaiter import FastaIter


def test_empty():
    data = StringIO("")

    iterator = FastaIter(data)

    # should return an empty generator
    with pytest.raises(StopIteration):
        six.next(iterator)


def test_noheader():
    data = StringIO("ACGT\n")

    iterator = FastaIter(data)

    # should return an empty generator
    with pytest.raises(StopIteration):
        six.next(iterator)


def test_single():
    data = StringIO(">seq1\nACGT\n")

    iterator = FastaIter(data)

    header, seq = six.next(iterator)
    assert header == "seq1"
    assert seq == "ACGT"

    # should be empty now
    with pytest.raises(StopIteration):
        six.next(iterator)


def test_multiple():
    data = StringIO(">seq1\nACGT\n>seq2\nTGCA\n\n>seq3\nTTTT")

    iterator = FastaIter(data)

    header, seq = six.next(iterator)
    assert header == "seq1"
    assert seq == "ACGT"

    header, seq = six.next(iterator)
    assert header == "seq2"
    assert seq == "TGCA"

    header, seq = six.next(iterator)
    assert header == "seq3"
    assert seq == "TTTT"

    # should be empty now
    with pytest.raises(StopIteration):
        six.next(iterator)


def test_multiline():
    data = StringIO(">seq1\nACGT\nTGCA")

    iterator = FastaIter(data)

    header, seq = six.next(iterator)
    assert header == "seq1"
    assert seq == "ACGTTGCA"

    # should be empty now
    with pytest.raises(StopIteration):
        six.next(iterator)

