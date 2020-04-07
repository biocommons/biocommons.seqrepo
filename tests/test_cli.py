# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import tempfile

import pytest
from biocommons.seqrepo.cli import (init, load, _get_aliases)
from biocommons.seqrepo.fastaiter import FastaIter
import six
from six import StringIO


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

    with pytest.raises(IOError) as excinfo:
        init(opts)

    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    assert str(excinfo.value) == "{seqrepo_dir} exists and is not empty".format(seqrepo_dir=seqrepo_dir)


def test_20_load(opts):
    init(opts)
    load(opts)


def _get_ncbi_alias(aliases):
    for al in aliases:
        if al['namespace'] == 'NCBI':
            return al['alias']
    return None


def test_ncbi_fasta(opts):
    init(opts)
    opts.namespace = 'NCBI'
    old_fasta = '>gi|295424141|ref|NM_000439.4| Homo sapiens proprotein convertase subtilisin/kexin type 1 ' + \
                         '(PCSK1), transcript variant 1, mRNA\nTTT'
    new_fasta = '>NM_000439.4 Homo sapiens proprotein convertase subtilisin/kexin type 1 (PCSK1), ' + \
                         'transcript variant 1, mRNA\nTTT'

    aliases = _get_aliases(old_fasta, opts)
    nm = _get_ncbi_alias(aliases)
    assert nm == 'NM_000439.4'

    aliases2 = _get_aliases(new_fasta, opts)
    nm2 = _get_ncbi_alias(aliases2)
    assert nm2 == 'NM_000439.4'

    data = StringIO(new_fasta)

    iterator = FastaIter(data)

    header, seq = six.next(iterator)
    assert header.startswith('NM_000439.4 Homo sapiens proprotein convertase subtilisin/kexin type 1 (PCSK1)')
    assert seq == "TTT"

    aliases3 = _get_aliases(header, opts)
    nm3 = _get_ncbi_alias(aliases3)
    assert nm3 == 'NM_000439.4'
