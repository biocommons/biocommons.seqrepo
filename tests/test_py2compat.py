import os

import pytest
import six

from biocommons.seqrepo.py2compat import makedirs, FileExistsError


def test_makedirs(tmpdir_factory):
    tmpdir = str(tmpdir_factory.mktemp('p2compat'))
    dn = os.path.join(tmpdir, "test")

    assert not os.path.isdir(dn)

    makedirs(dn)

    assert os.path.isdir(dn)

    with pytest.raises(FileExistsError):
        makedirs(dn)

    makedirs(dn, exist_ok=True)
