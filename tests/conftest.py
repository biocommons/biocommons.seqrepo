import os

import pytest

from biocommons.seqrepo import SeqRepo
from biocommons.seqrepo.dataproxy import SeqRepoDataProxy, SeqRepoRESTDataProxy


@pytest.fixture(scope="session")
def dataproxy():
    sr = SeqRepo(root_dir=os.environ.get("SEQREPO_ROOT_DIR", "/usr/local/share/seqrepo/latest"))
    return SeqRepoDataProxy(sr)


@pytest.fixture(scope="session")
def rest_dataproxy():
    url = os.environ.get("SEQREPO_REST_URL", "http://localhost:5000/seqrepo")
    return SeqRepoRESTDataProxy(base_url=url)


@pytest.fixture(scope="session")
def seqrepo(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    return SeqRepo(dir, writeable=True)


@pytest.fixture(scope="session")
def seqrepo_ro(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    sr = SeqRepo(dir, writeable=True)
    del sr  # close it
    return SeqRepo(dir)


@pytest.fixture(scope="session")
def seqrepo_keepcase(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    return SeqRepo(dir, upcase=False, writeable=True)


def test_create(seqrepo):
    assert str(seqrepo).startswith("SeqRepo(root_dir=/")
