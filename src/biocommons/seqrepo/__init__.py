"""biocommons.seqrepo package"""

from importlib.metadata import PackageNotFoundError, version

from .seqrepo import SeqRepo  # noqa: F401

if __package__ is None:
    __version__ = None
else:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:  # pragma: no cover
        # package is not installed
        __version__ = None
