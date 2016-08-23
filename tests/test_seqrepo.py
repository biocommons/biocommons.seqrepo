import pytest

from biocommons.seqrepo import SeqRepo


@pytest.fixture(scope="session")
def seqrepo(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp('seqrepo'))
    return SeqRepo(dir, writeable=True)


def test_create(seqrepo):
    pass


def test_store(seqrepo):
    seqrepo.store("SMELLASSWEET", [{"namespace": "en",
                                    "alias": "rose"}, {"namespace": "fr",
                                                       "alias": "rose"}, {"namespace": "es",
                                                                          "alias": "rosa"}])
    seqrepo.store("ASINCHANGE", [{"namespace": "en", "alias": "coin"}])
    seqrepo.store("ASINACORNER", [{"namespace": "fr", "alias": "coin"}])


def test_fetch(seqrepo):
    assert seqrepo.fetch("rose") == "SMELLASSWEET"
    assert seqrepo.fetch("rosa") == "SMELLASSWEET"

    assert seqrepo.fetch("rosa", start=5, end=7) == "AS"

    with pytest.raises(KeyError):
        assert seqrepo.fetch("coin")    # ambiguous alias

    assert seqrepo.fetch("coin", namespace="en") == "ASINCHANGE"
    assert seqrepo.fetch("coin", namespace="fr") == "ASINACORNER"
