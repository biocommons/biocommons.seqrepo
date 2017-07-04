import os

import six


class FileExistsError(OSError):
    pass


def makedirs(name, mode=0o777, exist_ok=False):
    """cheapo replacement for py3 makedirs with support for exist_ok

    """

    if os.path.exists(name):
        if not exist_ok:
            raise FileExistsError("File exists: " + name)
    else:
        os.makedirs(name, mode)
