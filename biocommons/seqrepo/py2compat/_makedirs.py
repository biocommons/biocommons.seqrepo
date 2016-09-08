import os

def makedirs(name, mode=511, exist_ok=False):
    """cheapo replacement for py3 makedirs with support for exist_ok

    """
    if os.path.exists(name):
        if not exist_ok:
            # Py3: FileExistsError: [Errno 17] File exists: '/tmp/somedir'
            # but that exception doesn't exist on Py2
            raise OSError("File exists: " + name)
    else:
        os.makedirs(name, mode)
