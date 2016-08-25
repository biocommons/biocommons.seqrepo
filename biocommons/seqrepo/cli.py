"""command line interface to a local SeqRepo repository

https://github.com/biocommons/biocommons.seqrepo

Typical usage is via the `seqrepo` script::

  $ seqrepo --help 

"""

from __future__ import division, print_function, unicode_literals

import argparse
import io
import itertools
import logging
import os
import pprint
import re
import shutil
import stat
import tempfile

from Bio import SeqIO
import tqdm

from . import __version__, SeqRepo
from .py2compat import gzip_open_encoded, makedirs

logger = logging.getLogger(__name__)


def parse_arguments():
    top_p = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0], formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog="seqrepo " + __version__ +
        ". See https://github.com/biocommons/biocommons.seqrepo for more information")
    top_p.add_argument("--dir", "-d", help="seqrepo data directory; created by init", required=True)
    top_p.add_argument("--verbose", "-v", action="count", default=0, help="be verbose; multiple accepted")
    top_p.add_argument("--version", action="version", version=__version__)

    subparsers = top_p.add_subparsers(title='subcommands')

    # export
    ap = subparsers.add_parser("export", help="export sequences")
    ap.set_defaults(func=export)

    # init
    ap = subparsers.add_parser("init", help="initialize bsa directory")
    ap.set_defaults(func=init)

    # load
    ap = subparsers.add_parser("load", help="load a single fasta file")
    ap.set_defaults(func=load)
    ap.add_argument(
        "fasta_files",
        nargs="+",
        help="fasta files to load (compressed okay)", )
    ap.add_argument(
        "--namespace",
        "-n",
        required=True,
        help="namespace name (e.g., ncbi, ensembl, lrg)", )

    # show-status
    ap = subparsers.add_parser("show-status", help="show seqrepo status")
    ap.set_defaults(func=show_status)

    # snapshot
    ap = subparsers.add_parser("snapshot", help="create a new read-only seqrepo snapshot")
    ap.set_defaults(func=snapshot)
    ap.add_argument(
        "destination_directory",
        help="destination directory name (must not already exist)"
        )

    # start-shell
    ap = subparsers.add_parser("start-shell", help="start interactive shell with initialized seqrepo")
    ap.set_defaults(func=start_shell)

    # upgrade
    ap = subparsers.add_parser("upgrade", help="upgrade bsa database and directory")
    ap.set_defaults(func=upgrade)

    opts = top_p.parse_args()
    return opts


def export(opts):
    def convert_alias_records_to_ns_dict(records):
        """converts a set of alias db records to a dict like {ns: [aliases], ...}
        aliases are lexicographicaly sorted
        """
        records = sorted(records, key = lambda r: (r["namespace"], r["alias"]))
        return {g: [r["alias"] for r in gi]
                for g, gi in itertools.groupby(records, key = lambda r: r["namespace"])}

    def wrap_lines(seq, line_width):
        for i in range(0, len(seq), line_width):
            yield seq[i:i + line_width]

    sr = SeqRepo(opts.dir)
    for srec,arecs in sr:
        nsad = convert_alias_records_to_ns_dict(arecs)
        aliases = ["{ns}:{a}".format(ns=ns, a=a) for ns,aliases in nsad.items() for a in aliases]
        print(">" + " ".join(aliases))
        for l in wrap_lines(srec["seq"], 100):
            print(l)


def init(opts):
    if os.path.exists(opts.dir) and len(os.listdir(opts.dir)) > 0:
        raise IOError("{opts.dir} exists and is not empty".format(opts=opts))
    sr = SeqRepo(opts.dir, writeable=True)  # flake8: noqa


def load(opts):
    defline_re = re.compile("(?P<namespace>gi|ref)\|(?P<alias>[^|]+)")
    disable_bar = opts.verbose > 0  # if > 0, we'll get log messages

    sr = SeqRepo(opts.dir, writeable=True)

    n_seqs_seen = n_seqs_added = n_aliases_added = 0
    fn_bar = tqdm.tqdm(opts.fasta_files, unit="file", disable=disable_bar)
    for fn in fn_bar:
        fn_bar.set_description(os.path.basename(fn))
        if fn.endswith(".gz") or fn.endswith(".bgz"):
            fh = gzip_open_encoded(fn, encoding="ascii")  # PY2BAGGAGE
        else:
            fh = io.open(fn, mode="rt", encoding="ascii")
        logger.info("Opened " + fn)
        seq_bar = tqdm.tqdm(SeqIO.parse(fh, "fasta"),
                            unit=" seqs", disable=disable_bar, leave=False)
        for rec in seq_bar:
            n_seqs_seen += 1
            seq_bar.set_description("seen: {nss} seqs; added: {nsa} seqs, {naa} aliases".format(
                nss = n_seqs_seen, nsa = n_seqs_added, naa = n_aliases_added))
            seq = str(rec.seq)
            if "|" in rec.id:
                aliases = [m.groupdict() for m in defline_re.finditer(rec.id)]
                for a in aliases:
                    if a["namespace"] == "ref":
                        a["namespace"] = "ncbi"
            else:
                aliases = [{"namespace": opts.namespace, "alias": rec.id}]
            n_sa, n_aa = sr.store(seq, aliases)
            n_seqs_added += n_sa
            n_aliases_added += n_aa


def show_status(opts):
    tot_size = sum(os.path.getsize(os.path.join(dirpath,filename))
                       for dirpath, dirnames, filenames in os.walk(opts.dir)
                       for filename in filenames)

    sr = SeqRepo(opts.dir)
    print("seqrepo {version}".format(version=__version__))
    print("root directory: {sr._root_dir}, {ts:.1f} GB".format(sr=sr, ts=tot_size/1e9))
    print("backends: fastadir (schema {fd_v}), seqaliasdb (schema {sa_v}) ".format(
        fd_v=sr.sequences.schema_version(), sa_v=sr.aliases.schema_version()))
    print("sequences: {ss[n_sequences]} sequences, {ss[tot_length]} residues, {ss[n_files]} files".format(
        ss=sr.sequences.stats()))
    print("aliases: {sa[n_aliases]} aliases, {sa[n_current]} current, {sa[n_namespaces]} namespaces, {sa[n_sequences]} sequences".format(
        sa=sr.aliases.stats()))
    return sr


def snapshot(opts):
    """snapshot a seqrepo data directory by hardlinking sequence files,
    copying sqlite databases, and remove write permissions from directories

    """
    src_dir = os.path.realpath(opts.dir)
    dst_dir = opts.destination_directory

    if dst_dir.startswith("/"):
        # use as-is
        pass
    else:
        # interpret dst_dir as relative to parent dir of opts.dir
        dst_dir = os.path.join(src_dir, '..', dst_dir)

    dst_dir = os.path.realpath(dst_dir)

    if os.path.commonpath([src_dir, dst_dir]).startswith(src_dir):
        raise RuntimeError("Cannot nest seqrepo directories "
        "({} is within {})".format(dst_dir, src_dir))

    if os.path.exists(dst_dir):
        raise IOError(dst_dir + ": File exists")

    tmp_dir = tempfile.mkdtemp(prefix=dst_dir + ".")
    
    logger.debug("src_dir = " + src_dir)
    logger.debug("dst_dir = " + dst_dir)
    logger.debug("tmp_dir = " + tmp_dir)
        
    # TODO: cleanup of tmpdir on failure
    makedirs(tmp_dir, exist_ok=True)
    wd = os.getcwd()
    os.chdir(src_dir)

    # make destination directories (walk is top-down)
    for rp in (os.path.join(dirpath, dirname)
               for dirpath, dirnames, _ in os.walk(".")
               for dirname in dirnames):
        dp = os.path.join(tmp_dir, rp)
        os.mkdir(dp)

    # hard link sequence files
    for rp in (os.path.join(dirpath, filename)
               for dirpath, _, filenames in os.walk(".")
               for filename in filenames
               if ".bgz" in filename):
        dp = os.path.join(tmp_dir, rp)
        os.link(rp, dp)

    # copy sqlite databases
    for rp in ["aliases.sqlite3", "sequences/db.sqlite3"]:
        dp = os.path.join(tmp_dir, rp)
        shutil.copyfile(rp, dp)

    # recursively drop write perms on snapshot
    mode_aw = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH
    def _drop_write(p):
        mode = os.lstat(p).st_mode
        new_mode = mode & ~mode_aw
        os.chmod(p, new_mode)
    for dp in (os.path.join(dirpath, dirent)
               for dirpath, dirnames, filenames in os.walk(tmp_dir)
               for dirent in dirnames + filenames):
        _drop_write(dp)
    _drop_write(tmp_dir)
    os.rename(tmp_dir, dst_dir)

    logger.info("snapshot created in " + dst_dir)
    os.chdir(wd)


def start_shell(opts):
    sr = show_status(opts)
    import IPython
    IPython.embed(display_banner=False)


def upgrade(opts):
    sr = SeqRepo(opts.dir, writeable=True)
    print("upgraded to schema version {}".format(sr.seqinfo.schema_version()))


def main():
    opts = parse_arguments()
    verbose_log_level = logging.WARN if opts.verbose == 0 else logging.INFO if opts.verbose == 1 else logging.DEBUG
    logging.basicConfig(level=verbose_log_level)
    opts.func(opts)


if __name__ == "__main__":
    main()
