import pytest

from biocommons.seqrepo import SeqRepo


@pytest.fixture(scope="session")
def seqrepo(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp('seqrepo'))
    return SeqRepo(dir, writeable=True)


@pytest.fixture(scope="session")
def seqrepo_ro(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp('seqrepo'))
    sr = SeqRepo(dir, writeable=True)
    del sr    # close it
    return SeqRepo(dir)


@pytest.fixture(scope="session")
def seqrepo_keepcase(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp('seqrepo'))
    return SeqRepo(dir, upcase=False, writeable=True)


def test_create(seqrepo):
    assert str(seqrepo).startswith('SeqRepo(root_dir=/')
