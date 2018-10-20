"""classes to read and write block gzip fasta files

A file may not currently be opened for reading and writing at the same time

Files must be named as .fa.bgz to be recognized as blocked gzip compressed

"""

from __future__ import unicode_literals

import io
import logging
import os
import re
import stat
import subprocess

import six

from pysam import FastaFile

line_width = 100
logger = logging.getLogger(__name__)

bgzip_exe = os.environ.get("SEQREPO_BGZIP_PATH", "/usr/bin/bgzip")
min_bgzip_version_info = (1, 2, 1)
min_bgzip_version = ".".join(map(str, min_bgzip_version_info))


def _get_bgzip_version(exe):
    """return bgzip version as string"""
    p = subprocess.Popen([exe, "-h"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    output = p.communicate()
    version_line = output[0].splitlines()[1]
    version = re.match(r"(?:Version:|bgzip \(htslib\))\s+(\d+\.\d+(\.\d+)?)", version_line).group(1)
    return version


def _check_bgzip_version(exe):
    missing_file_exception = OSError if six.PY2 else FileNotFoundError

    try:
        bgzip_version = _get_bgzip_version(exe)
    except AttributeError:
        raise RuntimeError("Didn't find version string when executing {exe}".format(exe=exe))
    except missing_file_exception:
        raise RuntimeError("Error while exceuting {exe}; does it exist?".format(exe=exe))
    except Exception:
        raise RuntimeError("Unknown error while executing {exe}".format(exe=exe))
    bgzip_version_info = tuple(map(int, bgzip_version.split(".")))
    if bgzip_version_info < min_bgzip_version_info:
        raise RuntimeError("bgzip ({exe}) {ev} is too old; >= {rv} is required; please upgrade".format(
            exe=exe, ev=bgzip_version, rv=min_bgzip_version))
    logger.info("Using bgzip {ev} ({exe})".format(ev=bgzip_version, exe=exe))


class FabgzReader(object):
    def __init__(self, filename):
        self._fh = FastaFile(filename)

    def fetch(self, seq_id, start=None, end=None):
        return self._fh.fetch(seq_id.encode("ascii"), start, end)

    def keys(self):
        return self._fh.references

    def __len__(self):
        return self._fh.nreferences

    def __getitem__(self, ac):
        return self.fetch(ac)

    @property
    def filename(self):
        return self._fh.filename


class FabgzWriter(object):
    # TODO: Use temp filename until indexes are built and perms are set, then rename
    def __init__(self, filename):
        super(FabgzWriter, self).__init__()

        _check_bgzip_version(bgzip_exe)

        self.filename = filename
        self._fh = None
        self._basepath, suffix = os.path.splitext(self.filename)
        if suffix != ".bgz":
            raise RuntimeError("Path must end with .bgz")

        files = [self.filename, self.filename + ".fai", self.filename + ".gzi", self._basepath]
        if any(os.path.exists(fn) for fn in files):
            raise RuntimeError("One or more target files already exists ({})".format(", ".join(files)))

        self._fh = io.open(self._basepath, encoding="ascii", mode="w")
        logger.debug("opened " + self.filename + " for writing")
        self._added = set()

    def store(self, seq_id, seq):
        def wrap_lines(seq, line_width):
            for i in range(0, len(seq), line_width):
                yield seq[i:i + line_width]

        if seq_id not in self._added:
            self._fh.write(">" + seq_id + "\n")
            for l in wrap_lines(seq, line_width):
                self._fh.write(l + "\n")
            self._added.add(seq_id)
            logger.debug("added seq_id {i}; length {l}".format(i=seq_id, l=len(seq)))
        return seq_id

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None
            subprocess.check_call([bgzip_exe, "--force", self._basepath])
            os.rename(self._basepath + ".gz", self.filename)

            # open file with FastaFile to create indexes, then make all read-only
            _fh = FastaFile(self.filename)
            _fh.close()
            os.chmod(self.filename, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            os.chmod(self.filename + ".fai", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            os.chmod(self.filename + ".gzi", stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)

            logger.info("{} written; added {} sequences".format(self.filename, len(self._added)))

    def __del__(self):
        if self._fh is not None:
            logger.error("FabgzWriter({}) was not explicitly closed; may result in lost data".format(self.filename))
            self.close()
