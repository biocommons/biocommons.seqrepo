import os


def makedirs(name, mode=0o777, exist_ok=False):
    if os.path.exists(name):
        if not exist_ok:
            raise IOError("File exists: " + name)
    else:
        os.makedirs(name, mode)
