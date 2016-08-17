"""classes to read and write block gzip fasta files

A file may not currently be opened for reading and writing at the same time

"""

import io
import logging
import os
import subprocess

import six

from pysam import FastaFile

from ..exceptions import SeqRepoError

line_width = 100
logger = logging.getLogger(__name__)


class FabgzReader(object):
    def __init__(self, filename):
        self._fh = FastaFile(filename)

    def fetch(self, seq_id, start=None, end=None):
        return self._fh.fetch(seq_id.encode("utf-8"), start, end)

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
    def __init__(self, filename):
        super(FabgzWriter, self).__init__()
        self.filename = filename
        self._fh = None
        self._basepath, suffix = os.path.splitext(self.filename)
        if suffix != ".bgz":
            raise SeqRepoError("Path must end with .bgz")

        files = [self.filename, self.filename + ".fai", self.filename + ".gzi",
                 self._basepath]
        if any(os.path.exists(fn) for fn in files):
            raise SeqRepoError(
                "One or more target files already exists ({})".format(
                    ", ".join(files)))

        self._fh = io.open(self._basepath, encoding="ascii", mode="w")
        logger.debug("opened " + self.filename + " for writing")
        self._added = set()

    def store(self, seq_id, seq):
        def wrap_lines(seq, line_width):
            for i in range(0, len(seq), line_width):
                yield seq[i:i + line_width]

        if seq_id not in self._added:
            self._fh.write(six.u(">" + seq_id + "\n"))
            # self._fh.writelines(six.u(l+"\n") for l in textwrap.wrap(seq, line_width))
            for l in wrap_lines(seq, line_width):
                self._fh.write(six.u(l) + "\n")
            self._added.add(seq_id)
            logger.debug("added seq_id {i}; length {l}".format(
                i=seq_id, l=len(seq)))
        return seq_id

    def close(self):
        if self._fh:
            self._fh.close()
            self._fh = None
            subprocess.check_call(["bgzip", "--force", self._basepath])
            os.rename(self._basepath + ".gz", self.filename)
            logger.info("{} written; added {} sequences".format(
                self.filename, len(self._added)))

    def __del__(self):
        if self._fh is not None:
            logger.error(
                "FabgzWriter({}) was not explicitly closed; may result in lost data".format(
                    self.filename))
            self.close()
