"""command line interface to a local SeqRepo repository

https://github.com/biocommons/seqrepo

Typical usage is via the `seqrepo` script::

  $ seqrepo --help 

"""

from __future__ import division, print_function, unicode_literals

import argparse
import datetime
import gzip
import io
import logging
import os
import re

from Bio import SeqIO

import seqrepo
from .py2compat import gzip_open_encoded

logger = logging.getLogger(__name__)


def parse_arguments():
    top_p = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog='See https://github.com/biocommons/seqrepo for more information', )
    top_p.add_argument(
        "--dir",
        "-d",
        help="seqrepo data directory; created by init",
        required=True)
    top_p.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="be verbose; multiple accepted")
    top_p.add_argument(
        "--version",
        action="version",
        default=seqrepo.__version__,
        version=seqrepo.__version__)

    subparsers = top_p.add_subparsers(title='subcommands')

    # init
    ap = subparsers.add_parser("init", help="initialize bsa directory")
    ap.set_defaults(func=init)

    # load-fasta
    ap = subparsers.add_parser("load-fasta", help="load a single fasta file")
    ap.set_defaults(func=load_fasta)
    ap.add_argument(
        "--fasta-file",
        "-f",
        action="append",
        default=[],
        help="fasta file to load (compressed okay)", )
    ap.add_argument(
        "--namespace",
        "-n",
        required=True,
        help="namespace name (e.g., ncbi, ensembl, lrg)", )

    # log
    ap = subparsers.add_parser("log", help="show seqrepo database log")
    ap.set_defaults(func=log)

    # status
    ap = subparsers.add_parser("status", help="show seqrep status")
    ap.set_defaults(func=status)

    # upgrade
    ap = subparsers.add_parser(
        "upgrade", help="upgrade bsa database and directory")
    ap.set_defaults(func=upgrade)

    opts = top_p.parse_args()
    return opts


def init(opts):
    if os.path.exists(opts.dir):
        raise seqrepo.SeqRepoError("{opts.dir} exists and is not empty".format(
            opts=opts))
    sr = seqrepo.SeqRepo(opts.dir)


def load_fasta(opts):
    defline_re = re.compile("(?P<namespace>gi|ref)\|(?P<alias>[^|]+)")
    sr = seqrepo.SeqRepo(opts.dir)
    for fn in opts.fasta_file:
        if fn.endswith(".gz") or fn.endswith(".bgz"):
            fh = gzip_open_encoded(fn, encoding="ascii")
        else:
            fh = io.open(fn, mode="rt", encoding="ascii")
        logger.info("Opened " + fn)
        for rec in SeqIO.parse(fh, "fasta"):
            seq = str(rec.seq)
            if "|" in rec.id:
                aliases = [m.groupdict() for m in defline_re.finditer(rec.id)]
                for a in aliases:
                    if a["namespace"] == "ref":
                        a["namespace"] = "ncbi"
            else:
                aliases = [{"namespace": opts.namespace, "alias": rec.id}]
            sr.store(seq, aliases)


def log(opts):
    sr = seqrepo.SeqRepo(opts.dir)
    c = sr.seqinfo._db.cursor()
    c.execute("select * from log order by ts")
    for r in c:
        print(r)


def status(opts):
    sr = seqrepo.SeqRepo(opts.dir)
    print("path = " + sr._path)
    print("schema version = " + sr.seqinfo.schema_version())


def upgrade(opts):
    sr = seqrepo.SeqRepo(opts.dir)
    print("upgraded to schema version {}".format(sr.seqinfo.schema_version()))


def main():
    opts = parse_arguments()
    verbose_log_level = logging.WARN if opts.verbose == 0 else logging.INFO if opts.verbose == 1 else logging.DEBUG
    logging.basicConfig(level=verbose_log_level)
    opts.func(opts)


if __name__ == "__main__":
    main()
