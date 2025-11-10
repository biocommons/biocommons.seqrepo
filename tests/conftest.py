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
    sr = SeqRepo(dir, writeable=True)
    yield sr
    sr.close()


@pytest.fixture(scope="session")
def seqrepo_ro(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    with SeqRepo(dir, writeable=True) as sr:
        pass  # closes automatically on exit
    sr_ro = SeqRepo(dir)  # return read-only instance
    yield sr_ro
    sr_ro.close()


@pytest.fixture(scope="session")
def seqrepo_keepcase(tmpdir_factory):
    dir = str(tmpdir_factory.mktemp("seqrepo"))
    sr = SeqRepo(dir, upcase=False, writeable=True)
    yield sr
    sr.close()


def test_create(seqrepo):
    assert str(seqrepo).startswith("SeqRepo(root_dir=/")
