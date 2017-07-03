# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile

import pytest

from biocommons.seqrepo.cli import (init, load)


@pytest.fixture
def opts():
    class MockOpts(object):
        pass

    test_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(test_dir, 'data')

    opts = MockOpts()
    opts.root_directory = os.path.join(tempfile.mkdtemp(prefix="seqrepo_pytest_"), "seqrepo")
    opts.fasta_files = [os.path.join(test_data_dir, "sequences.fa.gz")]
    opts.namespace = "test"
    opts.instance_name = "test"
    opts.verbose = 0
    return opts


def test_00_init(opts):
    init(opts)
    assert os.path.exists(opts.root_directory)


def test_20_load(opts):
    load(opts)
