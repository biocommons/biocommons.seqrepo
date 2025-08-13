"""classes to read and write block gzip fasta files

A file may not currently be opened for reading and writing at the same time

Files must be named as .fa.bgz to be recognized as blocked gzip compressed

"""

import logging
import os
import re
import shutil
import stat
import subprocess
import threading
from types import TracebackType

from pysam import FastaFile
from typing_extensions import Self

_logger = logging.getLogger(__name__)

line_width = 100

min_bgzip_version_info = (1, 2, 1)


def _get_bgzip_version(exe: str) -> str:
    """Return bgzip version as string"""
    p = subprocess.Popen(
        [exe, "-h"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
    )
    output = p.communicate()
    version_line = output[0].splitlines()[1]
    version_match = re.match(r"(?:Version:|bgzip \(htslib\))\s+(\d+\.\d+(\.\d+)?)", version_line)
    if version_match is None:
        raise ValueError(f"Unable to extract bgzip version from {version_line}")
    return version_match.group(1)


def _find_bgzip() -> str:
    """Return path to bgzip if found and meets version requirements, else exception"""
    min_bgzip_version = ".".join(map(str, min_bgzip_version_info))
    exe = os.environ.get("SEQREPO_BGZIP_PATH", shutil.which("bgzip") or "/usr/bin/bgzip")

    try:
        bgzip_version = _get_bgzip_version(exe)
    except AttributeError:
        raise RuntimeError(f"Didn't find version string in bgzip executable ({exe})")
    except FileNotFoundError:
        raise RuntimeError(
            f"{exe} doesn't exist; you need to install htslib and tabix "
            "(See https://github.com/biocommons/biocommons.seqrepo#requirements)"
        )
    except Exception:
        raise RuntimeError(f"Unknown error while executing {exe}")
    bgzip_version_info = tuple(map(int, bgzip_version.split(".")))
    if bgzip_version_info < min_bgzip_version_info:
        raise RuntimeError(
            f"bgzip ({exe}) {bgzip_version} is too old; >= {min_bgzip_version} is required; please upgrade"
        )
    _logger.info(f"Using bgzip {bgzip_version} ({exe})")
    return exe


class FabgzReader:
    """Class that implements ContextManager and wraps a FabgzReader.
    The FabgzReader is returned when acquired in a contextmanager with statement.
    """

    def __init__(self, filename: str) -> None:
        self.lock = threading.Lock()
        self._fh = FastaFile(filename)

    def __del__(self) -> None:
        self._fh.close()

    def __enter__(self) -> Self:
        self.lock.acquire()
        return self

    def __exit__(
        self, exc_type: type[Exception], exc_value: Exception, traceback: TracebackType
    ) -> None:
        self.lock.release()

    def fetch(self, seq_id: str, start: int | None = None, end: int | None = None):
        return self._fh.fetch(seq_id.encode("ascii"), start, end)  # type: ignore

    def keys(self):
        return self._fh.references

    def __len__(self) -> int | None:
        return self._fh.nreferences

    def __getitem__(self, ac: str) -> str:
        return self.fetch(ac)

    @property
    def filename(self) -> str:
        return self._fh.filename


class FabgzWriter:
    # TODO: Use temp filename until indexes are built and perms are set, then rename
    def __init__(self, filename: str) -> None:
        super(FabgzWriter, self).__init__()

        self.filename = filename
        self._fh = None
        self._basepath, suffix = os.path.splitext(self.filename)
        if suffix != ".bgz":
            raise RuntimeError("Path must end with .bgz")

        self._bgzip_exe = _find_bgzip()

        files = [
            self.filename,
            self.filename + ".fai",
            self.filename + ".gzi",
            self._basepath,
        ]
        if any(os.path.exists(fn) for fn in files):
            raise RuntimeError(
                "One or more target files already exists ({})".format(", ".join(files))
            )

        self._fh = open(self._basepath, encoding="ascii", mode="w")
        _logger.debug("opened " + self.filename + " for writing")
        self._added = set()

    def store(self, seq_id: str, seq: str) -> str:
        def wrap_lines(seq, line_width):
            for i in range(0, len(seq), line_width):
                yield seq[i : i + line_width]

        if seq_id not in self._added:
            if self._fh is None:
                raise RuntimeError("Writer has already been closed -- create a new FabgzWriter.")
            self._fh.write(">" + seq_id + "\n")
            for line in wrap_lines(seq, line_width):
                self._fh.write(line + "\n")
            self._added.add(seq_id)
            _logger.debug(f"added seq_id {seq_id}; length {len(seq)}")
        return seq_id

    def close(self) -> None:
        if self._fh:
            self._fh.close()
            self._fh = None
            subprocess.check_call([self._bgzip_exe, "--force", self._basepath])
            os.rename(self._basepath + ".gz", self.filename)

            # open file with FastaFile to create indexes, then make all read-only
            _fh = FastaFile(self.filename)
            _fh.close()
            os.chmod(self.filename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            os.chmod(self.filename + ".fai", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            os.chmod(self.filename + ".gzi", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            _logger.info(f"{self.filename} written; added {len(self._added)} sequences")

    def __del__(self) -> None:
        if self._fh is not None:
            _logger.error(
                f"FabgzWriter({self.filename}) was not explicitly closed; data may be lost"
            )
            self.close()
