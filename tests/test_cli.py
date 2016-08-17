import os
import tempfile

import pytest

from seqrepo.cli import (init, upgrade, load_fasta)


@pytest.fixture
def opts():
    class MockOpts(object):
        pass

    test_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(test_dir, 'data')

    opts = MockOpts()
    opts.dir = os.path.join(
        tempfile.mkdtemp(prefix="seqrepo_pytest_"), "seqrepo")
    opts.fasta_file = [os.path.join(test_data_dir, "sequences.fa.gz")]
    opts.namespace = "test"
    return opts


def test_00_init(opts):
    init(opts)
    assert os.path.exists(opts.dir)


def test_20_load_fasta(opts):
    load_fasta(opts)
