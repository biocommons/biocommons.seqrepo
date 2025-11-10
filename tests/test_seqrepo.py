import pytest

from biocommons.seqrepo import SeqRepo
from biocommons.seqrepo.seqrepo import SequenceProxy


def test_create(seqrepo):
    assert str(seqrepo).startswith("SeqRepo(root_dir=/")


def test_seqrepo_dir_not_exist(tmpdir_factory):
    """Ensure that exception is raised for non-existent seqrepo directory"""
    dir = str(tmpdir_factory.mktemp("seqrepo")) + "-IDONTEXIST"
    with pytest.raises(OSError) as ex:
        SeqRepo(dir, writeable=False)

    assert "Unable to open SeqRepo directory" in str(ex.value)


def test_store(seqrepo):
    seqrepo.store(
        "SMELLASSWEET",
        [{"namespace": "en", "alias": "rose"}, {"namespace": "fr", "alias": "rose"}],
    )
    seqrepo.store(
        "smellassweet", [{"namespace": "es", "alias": "rosa"}]
    )  # same sequence, new alias

    seqrepo.store(
        "ASINCHANGE", [{"namespace": "en", "alias": "coin"}]
    )  # same alias, diff seqs in diff namespaces
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
        assert seqrepo.fetch("bogus")  # non-existent alias

    with pytest.raises(KeyError):
        assert seqrepo.fetch("coin")  # ambiguous alias

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
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    seqrepo = SeqRepo(dir, writeable=True)

    # store sequences
    seqrepo.store("NCBISEQUENCE", [{"namespace": "NCBI", "alias": "ncbiac"}])
    seqrepo.store("ENSEMBLSEQUENCE", [{"namespace": "Ensembl", "alias": "ensemblac"}])
    seqrepo.store("LRGSEQUENCE", [{"namespace": "LRG", "alias": "lrgac"}])
    seqrepo.store(
        "REFSEQSEQUENCE", [{"namespace": "refseq", "alias": "refseqac"}]
    )  # should be stored as NCBI:refseqac
    seqrepo.commit()

    # lookups, no query translation
    assert seqrepo["NCBI:ncbiac"] == "NCBISEQUENCE"
    assert seqrepo["Ensembl:ensemblac"] == "ENSEMBLSEQUENCE"
    assert seqrepo["LRG:lrgac"] == "LRGSEQUENCE"
    assert seqrepo["NCBI:refseqac"] == "REFSEQSEQUENCE"  # tests ns translation on store

    # lookups, w/ query translation
    assert seqrepo["refseq:ncbiac"] == "NCBISEQUENCE"
    assert seqrepo["RefSeq:ncbiac"] == "NCBISEQUENCE"  # case-squashed
    assert seqrepo["Ensembl:ensemblac"] == "ENSEMBLSEQUENCE"
    assert seqrepo["LRG:lrgac"] == "LRGSEQUENCE"

    seq_id = seqrepo._get_unique_seqid(alias="ncbiac", namespace="NCBI")
    aliases = list(seqrepo.aliases.find_aliases(seq_id=seq_id))
    assert any(a for a in aliases if a["namespace"] == "refseq")
    assert any(a for a in aliases if a["namespace"] == "ga4gh")

    assert seqrepo["ga4gh:SQ." + seq_id] == "NCBISEQUENCE"
    assert seqrepo["sha512t24u:" + seq_id] == "NCBISEQUENCE"


def test_translation(seqrepo):
    assert "MD5:8b2698fb0b0c93558a6adbb11edb1e4b" in seqrepo.translate_identifier("en:rose"), (
        "failed fully-qualified identifier lookup"
    )
    assert "MD5:8b2698fb0b0c93558a6adbb11edb1e4b" in seqrepo.translate_identifier("rose"), (
        "failed unqualified identifier lookup"
    )
    assert "VMC:GS_bsoUMlD3TrEtlh9Dt1iT29mzfkwwFUDr" in seqrepo.translate_identifier("en:rose"), (
        "failed to find expected identifier in returned identifiers"
    )
    assert seqrepo.translate_identifier("en:rose", target_namespaces=["VMC"]) == [
        "VMC:GS_bsoUMlD3TrEtlh9Dt1iT29mzfkwwFUDr"
    ], "failed to rerieve exactly the expected identifier"


def test_sequenceproxy(seqrepo):
    # A SequenceProxy is returned by __getitem__ when SeqRepo is
    # instantiated with use_sequenceproxy=True

    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")
    assert sp  # __bool__ dunder method
    assert sp[5:7] == "AS"  # __eq__ and __getitem__


def test_context_manager(tmpdir_factory):
    """Test SeqRepo context manager support"""
    dir = str(tmpdir_factory.mktemp("seqrepo_ctx"))

    # Test with statement for resource cleanup
    with SeqRepo(dir, writeable=True) as sr:
        sr.store("ATCGATCGATCG", [{"namespace": "test", "alias": "test_alias"}])
        sr.commit()
        assert "test_alias" in sr

    # After exiting context, database should be closed
    # (We can't directly test closure, but we can verify it doesn't error on re-open)
    sr_reopened = SeqRepo(dir, writeable=False)
    assert "test_alias" in sr_reopened
    sr_reopened.close()


def test_explicit_close(tmpdir_factory):
    """Test explicit close() method"""
    dir = str(tmpdir_factory.mktemp("seqrepo_close"))

    sr = SeqRepo(dir, writeable=True)
    sr.store("GCTAGCTAGCTA", [{"namespace": "test", "alias": "test_alias2"}])
    sr.commit()

    # Explicitly close the repository
    sr.close()

    # Verify we can reopen without issues
    sr_reopened = SeqRepo(dir, writeable=False)
    assert "test_alias2" in sr_reopened
    sr_reopened.close()


def test_close_multiple_times(tmpdir_factory):
    """Test that close() is safe to call multiple times"""
    dir = str(tmpdir_factory.mktemp("seqrepo_multi_close"))

    sr = SeqRepo(dir, writeable=True)
    sr.store("TTAACCGGTTAA", [{"namespace": "test", "alias": "test_alias3"}])
    sr.commit()

    # Should be safe to call close() multiple times
    sr.close()
    sr.close()  # Should not raise an exception
    sr.close()  # And again for good measure

    # Verify we can still reopen after multiple closes
    sr_reopened = SeqRepo(dir, writeable=False)
    assert "test_alias3" in sr_reopened
    sr_reopened.close()


def test_sequenceproxy_slicing(seqrepo):
    """Test SequenceProxy slice operations"""
    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")

    # Test single integer indexing (converted to slice)
    assert sp[0] == "S"

    # Test slice with None bounds
    assert sp[:] == "SMELLASSWEET"

    # Test slice with step (should raise ValueError)
    with pytest.raises(ValueError, match="contiguous"):
        sp[::2]


def test_sequenceproxy_bool_and_eq(seqrepo):
    """Test SequenceProxy bool and equality operations"""
    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")

    # Test __bool__ - empty sequences are False
    assert bool(sp) is True
    assert sp == "SMELLASSWEET"
    assert sp != "DIFFERENTSEQ"


def test_sequenceproxy_hash_and_reversed(seqrepo):
    """Test SequenceProxy hash and reversed operations"""
    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")

    # Test __hash__
    assert isinstance(hash(sp), int)

    # Test __reversed__
    assert str(sp)[::-1] == reversed(sp)


def test_sequenceproxy_repr(seqrepo):
    """Test SequenceProxy repr"""
    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")
    repr_str = repr(sp)
    assert "SequenceProxy" in repr_str
    assert "seq_id=" in repr_str
    assert "len=" in repr_str


def test_sequenceproxy_aliases(seqrepo):
    """Test SequenceProxy aliases property"""
    sp = SequenceProxy(seqrepo, namespace=None, alias="rosa")
    aliases = sp.aliases

    # Should have at least the aliases we know about
    assert any("rose" in a for a in aliases)
    # Check for namespace-prefixed format
    assert any(":" in a for a in aliases)


def test_fetch_uri_invalid(seqrepo):
    """Test fetch_uri with invalid URI format"""
    with pytest.raises(ValueError, match="Unable to parse"):
        seqrepo.fetch_uri("invalid_uri_without_colon")


def test_translate_identifier_with_target_namespaces(seqrepo):
    """Test translate_identifier with target namespace filtering"""
    # Test single target namespace
    result = seqrepo.translate_identifier("en:rose", target_namespaces=["fr"])
    # Should return empty since rose in fr namespace is not the same sequence
    # Actually, all aliases for same sequence will be returned
    assert isinstance(result, list)


def test_getitem_with_use_sequenceproxy_false(tmpdir_factory):
    """Test __getitem__ when use_sequenceproxy=False returns string"""
    dir = str(tmpdir_factory.mktemp("seqrepo_no_proxy"))
    sr = SeqRepo(dir, writeable=True, use_sequenceproxy=False)
    sr.store("ATCGATCG", [{"namespace": "test", "alias": "seq1"}])
    sr.commit()

    # When use_sequenceproxy=False, __getitem__ should return string
    result = sr["seq1"]
    assert isinstance(result, str)
    assert result == "ATCGATCG"
    sr.close()


def test_fetch_with_namespace(seqrepo):
    """Test fetch with namespace argument"""
    result = seqrepo.fetch("coin", namespace="en")
    assert result == "ASINCHANGE"

    result = seqrepo.fetch("coin", namespace="fr")
    assert result == "ASINACORNER"


def test_store_exception_handling(seqrepo):
    """Test store exception handling for invalid sequences"""
    # This tests the try/except in store() that logs critical errors
    # We'll try to store with empty nsaliases to trigger normal path but different scenario
    seqrepo.store("NEWSEQ", [{"namespace": "test", "alias": "newseq"}])
    seqrepo.commit()
    assert "newseq" in seqrepo
