import os

import pytest

from biocommons.seqrepo.config import SEQREPO_FD_CACHE_SIZE_ENV_NAME
from biocommons.seqrepo.utils import parse_defline, validate_aliases, resolve_fd_cache_size


def test_resolve_fd_cache_size():
    # Preserve any data for this env var before we try different values
    orig_env = os.environ.get(SEQREPO_FD_CACHE_SIZE_ENV_NAME)
    if orig_env:
        del os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME]

    instance_fd_cache_size = 10
    # With no env var set, resolve_fd_cache_size should pass through its input value
    assert resolve_fd_cache_size(instance_fd_cache_size) == instance_fd_cache_size
    # Otherwise any env var will override the instance value
    os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME] = "none"
    assert resolve_fd_cache_size(instance_fd_cache_size) is None
    os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME] = "100"
    assert resolve_fd_cache_size(instance_fd_cache_size) == 100
    os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME] = "0"
    assert resolve_fd_cache_size(instance_fd_cache_size) == 0

    os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME] = "foo"
    with pytest.raises(ValueError):
        assert resolve_fd_cache_size(instance_fd_cache_size)

    # Restore original env var
    if orig_env:
        os.environ[SEQREPO_FD_CACHE_SIZE_ENV_NAME] = orig_env


def test_parse_defline():
    """Sample deflines:
    >NG_007107.2 Homo sapiens methyl-CpG binding protein 2 (MECP2), RefSeqGene on chromosome X
    >XR_928350.3 PREDICTED: Homo sapiens maestro heat like repeat family member 1 (MROH1), transcript variant X23, misc_RNA
    >1 dna:chromosome chromosome:GRCh38:1:1:248956422:1 REF
    >CHR_HSCHR15_4_CTG8 dna:chromosome chromosome:GRCh38:CHR_HSCHR15_4_CTG8:1:102071387:1 HAP
    >ENSP00000451515.1 pep chromosome:GRCh38:14:22439007:22439015:1 gene:ENSG00000237235.2
    >ENST00000410344.1 ncrna:known chromosome:GRCh38:14:96384624:96384815:1 gene:ENSG00000222276.1 gene_biotype:snRNA transcript_biotype:snRNA
    >gi|568815364|ref|NT_077402.3| Homo sapiens chromosome 1 genomic scaffold, GRCh38.p7 Primary Assembly HSCHR1_CTG1
    >ref|NT_005334.17| Homo sapiens chromosome 2 genomic scaffold, GRCh38.p12 Primary Assembly HSCHR2_CTG1
    >LRG_99g (genomic sequence)
    >LRG_99t1 (transcript t1 of LRG_99)
    >LRG_99p1 (protein translated from transcript t1 of LRG_99)

    """

    defline = (
        ">NG_007107.2 Homo sapiens methyl-CpG binding protein 2 (MECP2), RefSeqGene on chromosome X"
    )
    assert parse_defline(defline, "refseq") == [{"namespace": "refseq", "alias": "NG_007107.2"}]

    defline = ">gi|568815364|ref|NT_077402.3| Homo sapiens chromosome 1 genomic scaffold, GRCh38.p7 Primary Assembly HSCHR1_CTG1"
    assert parse_defline(defline, "refseq") == [{"namespace": "refseq", "alias": "NT_077402.3"}]


def test_validate_aliases():
    aliases = [
        {"namespace": "refseq", "alias": "NM_012345.6"},
        {"namespace": "Ensembl", "alias": "ENST012345.6"},
    ]

    assert validate_aliases(aliases)  # okay

    with pytest.raises(RuntimeError):
        validate_aliases([{"namespace": "blah", "alias": "aliases can't have spaces"}])

    with pytest.raises(RuntimeError):
        validate_aliases([{"namespace": "refseq", "alias": "NM_012345"}])

    with pytest.raises(RuntimeError):
        validate_aliases([{"namespace": "Ensembl", "alias": "ENST012345"}])
