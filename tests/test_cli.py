# -*- coding: utf-8 -*-
import io
import os
import tempfile
from typing import List, Optional

import pytest

from biocommons.seqrepo.cli import init, load
from biocommons.seqrepo.fastaiter import FastaIter
from biocommons.seqrepo.utils import parse_defline


@pytest.fixture
def opts():
    class MockOpts:
        def __init__(
            self,
            root_directory: Optional[str] = None,
            fasta_files: Optional[List[str]] = None,
            namespace: Optional[str] = None,
            instance_name: Optional[str] = None,
            verbose: int = 0,
        ):
            """
            Mock class for options used in seqrepo tests.

            Args:
                root_directory: The root directory for the seqrepo instance.
                fasta_files: List of FASTA file paths.
                namespace: The namespace.
                instance_name: The instance name.
                verbose: Verbosity level.
            """
            self.root_directory = root_directory
            self.fasta_files = fasta_files
            self.namespace = namespace
            self.instance_name = instance_name
            self.verbose = verbose

    test_dir = os.path.dirname(__file__)
    test_data_dir = os.path.join(test_dir, "data")

    opts = MockOpts(
        root_directory=os.path.join(tempfile.mkdtemp(prefix="seqrepo_pytest_"), "seqrepo"),
        fasta_files=[os.path.join(test_data_dir, "sequences.fa.gz")],
        namespace="test",
        instance_name="test",
        verbose=0,
    )
    return opts


def test_00_init(opts):
    init(opts)
    assert os.path.exists(opts.root_directory)

    with pytest.raises(IOError) as excinfo:
        init(opts)

    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    assert str(excinfo.value) == "{seqrepo_dir} exists and is not empty".format(
        seqrepo_dir=seqrepo_dir
    )


def test_20_load(opts):
    init(opts)
    load(opts)


def test_refseq_fasta(opts):
    def _get_refseq_alias(aliases):
        for al in aliases:
            if al["namespace"] == "refseq":
                return al["alias"]
        return None

    init(opts)
    opts.namespace = "refseq"
    old_fasta = (
        ">gi|295424141|ref|NM_000439.4| Homo sapiens proprotein convertase subtilisin/kexin type 1 "
        + "(PCSK1), transcript variant 1, mRNA\nTTT"
    )
    new_fasta = (
        ">NM_000439.4 Homo sapiens proprotein convertase subtilisin/kexin type 1 (PCSK1), "
        + "transcript variant 1, mRNA\nTTT"
    )

    aliases = parse_defline(old_fasta, opts.namespace)
    nm = _get_refseq_alias(aliases)
    assert nm == "NM_000439.4"

    aliases2 = parse_defline(new_fasta, opts.namespace)
    nm2 = _get_refseq_alias(aliases2)
    assert nm2 == "NM_000439.4"

    data = io.StringIO(new_fasta)

    iterator = FastaIter(data)
    header, seq = next(iterator)
    assert header.startswith(
        "NM_000439.4 Homo sapiens proprotein convertase subtilisin/kexin type 1 (PCSK1)"
    )
    assert seq == "TTT"

    aliases3 = parse_defline(header, opts.namespace)
    nm3 = _get_refseq_alias(aliases3)
    assert nm3 == "NM_000439.4"
