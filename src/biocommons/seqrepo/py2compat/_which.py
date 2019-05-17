import os

def which(file):
    """
    >>> which("sh") is not None
    True

    >>> which("bogus-executable-that-doesn't-exist") is None
    True

    """
    for path in os.environ["PATH"].split(os.pathsep):
        if os.path.exists(os.path.join(path, file)):
                return os.path.join(path, file)
    return None
