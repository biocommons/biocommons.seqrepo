import pytest

from biocommons.seqrepo import SeqRepo
from biocommons.seqrepo.seqrepo import SequenceProxy


def test_create(seqrepo):
    assert str(seqrepo).startswith('SeqRepo(root_dir=/')


def test_seqrepo_dir_not_exist(tmpdir_factory):
    """Ensure that exception is raised for non-existent seqrepo directory"""
    dir = str(tmpdir_factory.mktemp('seqrepo')) + "-IDONTEXIST"
    with pytest.raises(OSError) as ex:
        SeqRepo(dir, writeable=False)

    assert "Unable to open SeqRepo directory" in str(ex.value)


def test_store(seqrepo):
    seqrepo.store("SMELLASSWEET", [{"namespace": "en", "alias": "rose"}, {"namespace": "fr", "alias": "rose"}])
    seqrepo.store("smellassweet", [{"namespace": "es", "alias": "rosa"}])    # same sequence, new alias

    seqrepo.store("ASINCHANGE", [{"namespace": "en", "alias": "coin"}])    # same alias, diff seqs in diff namespaces
    seqrepo.store("ASINACORNER", [{"namespace": "fr", "alias": "coin"}])
    seqrepo.commit()


def test_fetch(seqrepo):
    assert seqrepo.fetch("rose") == "SMELLASSWEET"
    assert seqrepo["rose"] == "SMELLASSWEET"
    assert seqrepo.fetch("rosa") == "SMELLASSWEET"
    assert "rosa" in seqrepo

    assert len(list(rec for rec in seqrepo)) == 3

    assert seqrepo.fetch("rosa", start=5, end=7) == "AS"

    with pytest.raises(KeyError):
        assert seqrepo.fetch("bogus")    # non-existent alias

    with pytest.raises(KeyError):
        assert seqrepo.fetch("coin")    # ambiguous alias

    assert seqrepo.fetch("coin", namespace="en") == "ASINCHANGE"
    assert seqrepo.fetch("coin", namespace="fr") == "ASINACORNER"

    assert seqrepo.fetch_uri("en:coin") == "ASINCHANGE"
    assert seqrepo.fetch_uri("fr:coin") == "ASINACORNER"


def test_digests(seqrepo):
    """tests one set of digests"""

    # to get aliases, add "import time; time.sleep(120)" above, then:
    # (3.5) snafu$ SEQREPO_ROOT_DIR=/tmp/pytest-of-reece/pytest-0/seqrepo0 seqrepo export -i .
    assert seqrepo.fetch_uri("fr:coin") == "ASINACORNER"
    assert seqrepo.fetch_uri("MD5:ea81b52627e387fc6edd8b9412cd3a99") == "ASINACORNER"
    assert seqrepo.fetch_uri("SEGUID:aMQF/cdHkAayLkVYs8XV2u+Hy34") == "ASINACORNER"
    assert seqrepo.fetch_uri("SHA1:68c405fdc7479006b22e4558b3c5d5daef87cb7e") == "ASINACORNER"
    assert seqrepo.fetch_uri("VMC:GS_LDz34B6fA_fLxFoc2agLrXQRYuupOGGM") == "ASINACORNER"
    

def test_errors(seqrepo_ro):
    with pytest.raises(RuntimeError):
        seqrepo_ro.store("SHOULDFAIL", [{"namespace": "fr", "alias": "coin"}])


def test_keepcase(seqrepo_keepcase):
    seqrepo_keepcase.store("ifIonlyHADaBRAIN", [{"namespace": "me", "alias": "iiohab"}])
    assert seqrepo_keepcase["iiohab"] == "ifIonlyHADaBRAIN"


def test_refseq_lookup(seqrepo):
    seqrepo.store("NCBISEQUENCE", [{"namespace": "NCBI", "alias": "ncbiac"}])
    # commit not necessary
    assert seqrepo["ncbiac"] == "NCBISEQUENCE"
    assert seqrepo["NCBI:ncbiac"] == "NCBISEQUENCE"
    assert seqrepo["refseq:ncbiac"] == "NCBISEQUENCE"
    

def test_namespace_translation(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp('seqrepo'))
    seqrepo = SeqRepo(dir, writeable=True)

    # store sequences
    seqrepo.store("NCBISEQUENCE",    [{"namespace": "NCBI",    "alias": "ncbiac"   }])
    seqrepo.store("ENSEMBLSEQUENCE", [{"namespace": "Ensembl", "alias": "ensemblac"}])
    seqrepo.store("LRGSEQUENCE",     [{"namespace": "LRG",     "alias": "lrgac"   }])
    seqrepo.store("REFSEQSEQUENCE",  [{"namespace": "refseq",  "alias": "refseqac" }])  # should be stored as NCBI:refseqac
    seqrepo.commit()

    # lookups, no query translation
    assert seqrepo["NCBI:ncbiac"]       == "NCBISEQUENCE"
    assert seqrepo["Ensembl:ensemblac"] == "ENSEMBLSEQUENCE"
    assert seqrepo["LRG:lrgac"]         == "LRGSEQUENCE"
    assert seqrepo["NCBI:refseqac"]     == "REFSEQSEQUENCE"  # tests ns translation on store

    # lookups, w/ query translation
    assert seqrepo["refseq:ncbiac"]     == "NCBISEQUENCE"
    assert seqrepo["RefSeq:ncbiac"]     == "NCBISEQUENCE"  # case-squashed
    assert seqrepo["Ensembl:ensemblac"] == "ENSEMBLSEQUENCE"
    assert seqrepo["LRG:lrgac"]         == "LRGSEQUENCE"

    seq_id = seqrepo._get_unique_seqid(alias="ncbiac", namespace="NCBI")
    aliases = list(seqrepo.aliases.find_aliases(seq_id=seq_id))
    assert any(a for a in aliases if a["namespace"] == "refseq")
    assert any(a for a in aliases if a["namespace"] == "ga4gh")

    assert seqrepo["ga4gh:SQ."+seq_id]   == "NCBISEQUENCE"
    assert seqrepo["sha512t24u:"+seq_id] == "NCBISEQUENCE"
    


def test_translation(seqrepo):
    assert "MD5:8b2698fb0b0c93558a6adbb11edb1e4b" in seqrepo.translate_identifier("en:rose"), "failed fully-qualified identifier lookup"
    assert "MD5:8b2698fb0b0c93558a6adbb11edb1e4b" in seqrepo.translate_identifier("rose"), "failed unqualified identifier lookup"
    assert "VMC:GS_bsoUMlD3TrEtlh9Dt1iT29mzfkwwFUDr" in seqrepo.translate_identifier("en:rose"), "failed to find expected identifier in returned identifiers"
    assert ["VMC:GS_bsoUMlD3TrEtlh9Dt1iT29mzfkwwFUDr"] == seqrepo.translate_identifier("en:rose", target_namespaces=["VMC"]), "failed to rerieve exactly the expected identifier"


def test_sequenceproxy(seqrepo):
    # A SequenceProxy is returned by __getitem__ when SeqRepo is
    # instantiated with use_sequenceproxy=True

    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")
    assert sp                   # __bool__ dunder method
    assert sp[5:7] == "AS"      # __eq__ and __getitem__

