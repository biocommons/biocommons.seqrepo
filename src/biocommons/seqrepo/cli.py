"""command line interface to a local SeqRepo repository

SeqRepo is a non-redundant, compressed, journalled, file-based storage
for biological sequences

https://github.com/biocommons/biocommons.seqrepo

Try::

  $ seqrepo --help

"""

import argparse
import contextlib
import datetime
import gzip
import itertools
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Generator, Iterable, Iterator

import bioutils.assemblies
import bioutils.seqfetcher
import tqdm

from . import SeqRepo, __version__
from .fastaiter import FastaIter
from .utils import parse_defline, validate_aliases

SEQREPO_ROOT_DIR = os.environ.get("SEQREPO_ROOT_DIR", "/usr/local/share/seqrepo")
DEFAULT_INSTANCE_NAME_RW = "master"
DEFAULT_INSTANCE_NAME_RO = "latest"

instance_name_new_re = re.compile(
    r"^20[12]\d-\d\d-\d\d$"
)  # smells like a new datestamp, 2017-01-17
instance_name_old_re = re.compile(r"^20[12]1\d\d\d\d\d$")  # smells like an old datestamp, 20170117
instance_name_re = re.compile(
    r"^20[12]\d-?\d\d-?\d\d$"
)  # smells like a datestamp, 20170117 or 2017-01-17

_logger = logging.getLogger(__name__)


class RsyncExeError(Exception):
    """Raise for issues relating to rsync executable."""


def _check_rsync_binary(opts: argparse.Namespace) -> None:
    """Check for rsync vs openrsync binary issue

    Macs now ship with openrsync, but it's limited in function and not compatible with
    SeqRepo.

    :param opts: CLI args
    :raise RsyncExeError: if provided binary appears to be openrsync not rsync
    """
    result = subprocess.check_output([opts.rsync_exe, "--version"])  # noqa: S603
    if result is not None and ("openrsync" in result.decode()):
        msg = f"Binary located at {opts.rsync_exe} appears to be an `openrsync` instance, but the SeqRepo CLI requires `rsync` (NOT `openrsync`). Please install `rsync` and manually provide its location with the `--rsync-exe` option. See README for more information."
        raise RsyncExeError(msg)


def _get_remote_instances(opts: argparse.Namespace) -> list[str]:
    line_re = re.compile(r"d[-rwx]{9}\s+[\d,]+ \d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} (.+)")
    rsync_cmd = [
        opts.rsync_exe,
        "--no-motd",
        "--copy-dirlinks",
        opts.remote_host + "::seqrepo",
    ]
    _logger.debug("Executing `%s`", " ".join(rsync_cmd))
    result = subprocess.check_output(rsync_cmd)  # noqa: S603
    lines = result.decode().splitlines()[1:]
    dirs = (m.group(1) for m in (line_re.match(line) for line in lines) if m)
    return sorted(filter(instance_name_new_re.match, dirs))


def _get_local_instances(opts: argparse.Namespace) -> list[str]:
    return sorted(filter(instance_name_re.match, os.listdir(opts.root_directory)))


def _latest_instance(opts: argparse.Namespace) -> str | None:
    instances = _get_local_instances(opts)
    return instances[-1] if instances else None


def _latest_instance_path(opts: argparse.Namespace) -> str | None:
    li = _latest_instance(opts)
    return os.path.join(opts.root_directory, li) if li else None


def parse_arguments() -> argparse.Namespace:
    epilog = (
        f"seqrepo {__version__}"
        "See https://github.com/biocommons/biocommons.seqrepo for more information"
    )
    top_p = argparse.ArgumentParser(
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        epilog=epilog,
    )
    top_p.add_argument("--dry-run", "-n", default=False, action="store_true")
    top_p.add_argument("--remote-host", default="dl.biocommons.org", help="rsync server host")
    top_p.add_argument(
        "--root-directory",
        "-r",
        default=SEQREPO_ROOT_DIR,
        help="seqrepo root directory (SEQREPO_ROOT_DIR)",
    )
    top_p.add_argument("--rsync-exe", default="/usr/bin/rsync", help="path to rsync executable")
    top_p.add_argument(
        "--verbose",
        "-v",
        action="count",
        default=0,
        help="be verbose; multiple accepted",
    )
    top_p.add_argument("--version", action="version", version=__version__)

    # dest and required bits are to work around a bug in the Python 3 version of argparse
    # when no subcommands are provided
    # https://stackoverflow.com/questions/22990977/why-does-this-argparse-code-behave-differently-between-python-2-and-3
    # http://bugs.python.org/issue9253#msg186387
    subparsers = top_p.add_subparsers(title="subcommands", dest="_subcommands")
    subparsers.required = True

    # add-assembly-names
    ap = subparsers.add_parser(
        "add-assembly-names",
        help="add assembly aliases (from bioutils.assemblies) to existing sequences",
    )
    ap.set_defaults(func=add_assembly_names)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable (i.e., not a snapshot)",
    )
    ap.add_argument(
        "--partial-load",
        "-p",
        default=False,
        action="store_true",
        help="assign assembly aliases even if some sequences are missing",
    )
    ap.add_argument(
        "--reload-all",
        "-r",
        default=False,
        action="store_true",
        help="reload all assemblies, not just missing ones",
    )

    # export
    ap = subparsers.add_parser("export", help="export sequences")
    ap.set_defaults(func=export)
    ap.add_argument("ALIASES", nargs="*", help="specific aliases to export")
    ap.add_argument("--instance-name", "-i", default=DEFAULT_INSTANCE_NAME_RO, help="instance name")
    ap.add_argument(
        "--namespace",
        "-n",
        help="namespace name (e.g., refseq, NCBI, Ensembl, LRG)",
    )

    # export aliases
    ap = subparsers.add_parser("export-aliases", help="export aliases")
    ap.set_defaults(func=export_aliases)
    ap.add_argument("--instance-name", "-i", default=DEFAULT_INSTANCE_NAME_RO, help="instance name")
    ap.add_argument(
        "--namespace",
        "-n",
        help="namespace name (e.g., refseq, NCBI, Ensembl, LRG)",
    )

    # fetch-load
    ap = subparsers.add_parser(
        "fetch-load",
        help="fetch remote sequences by accession and load them (low-throughput!)",
    )
    ap.set_defaults(func=fetch_load)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable (i.e., not a snapshot)",
    )
    ap.add_argument(
        "accessions",
        nargs="+",
        help="accessions (NCBI or Ensembl)",
    )
    ap.add_argument(
        "--namespace",
        "-n",
        required=True,
        help="namespace name (e.g., NCBI, Ensembl, LRG)",
    )

    # init
    ap = subparsers.add_parser("init", help="initialize seqrepo directory")
    ap.set_defaults(func=init)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable (i.e., not a snapshot)",
    )

    # list-local-instances
    ap = subparsers.add_parser("list-local-instances", help="list local seqrepo instances")
    ap.set_defaults(func=list_local_instances)

    # list-remote-instances
    ap = subparsers.add_parser("list-remote-instances", help="list remote seqrepo instances")
    ap.set_defaults(func=list_remote_instances)

    # load
    ap = subparsers.add_parser("load", help="load a single fasta file")
    ap.set_defaults(func=load)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable (i.e., not a snapshot)",
    )
    ap.add_argument(
        "fasta_files",
        nargs="+",
        help="fasta files to load (compressed okay)",
    )
    ap.add_argument(
        "--namespace",
        "-n",
        required=True,
        help="namespace name (e.g., NCBI, Ensembl, LRG)",
    )

    # pull
    ap = subparsers.add_parser("pull", help="pull incremental update from seqrepo mirror")
    ap.set_defaults(func=pull)
    ap.add_argument("--instance-name", "-i", default=None, help="instance name")
    ap.add_argument(
        "--update-latest",
        "-l",
        default=False,
        action="store_true",
        help="set latest symlink to point to this instance",
    )

    # show-status
    ap = subparsers.add_parser("show-status", help="show seqrepo status")
    ap.set_defaults(func=show_status)
    ap.add_argument("--instance-name", "-i", default=DEFAULT_INSTANCE_NAME_RO, help="instance name")

    # snapshot
    ap = subparsers.add_parser("snapshot", help="create a new read-only seqrepo snapshot")
    ap.set_defaults(func=snapshot)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable",
    )
    ap.add_argument(
        "--destination-name",
        "-d",
        default=datetime.datetime.now(datetime.timezone.utc).strftime("%F"),
        help="destination directory name (must not already exist)",
    )

    # start-shell
    ap = subparsers.add_parser(
        "start-shell", help="start interactive shell with initialized seqrepo"
    )
    ap.set_defaults(func=start_shell)
    ap.add_argument("--instance-name", "-i", default=DEFAULT_INSTANCE_NAME_RO, help="instance name")

    # upgrade
    ap = subparsers.add_parser("upgrade", help="upgrade seqrepo database and directory")
    ap.set_defaults(func=upgrade)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable",
    )

    # update digests
    ap = subparsers.add_parser("update-digests", help="update computed digests in place")
    ap.set_defaults(func=update_digests)
    ap.add_argument(
        "--instance-name",
        "-i",
        default=DEFAULT_INSTANCE_NAME_RW,
        help="instance name; must be writeable",
    )

    # update latest (symlink)
    ap = subparsers.add_parser(
        "update-latest", help="create symlink `latest` to newest seqrepo instance"
    )
    ap.set_defaults(func=update_latest)

    return top_p.parse_args()


############################################################################


def add_assembly_names(opts: argparse.Namespace) -> None:
    """Add assembly names as aliases to existing sequences

    Specifically, associate aliases like GRCh37.p9:1 with existing
    refseq accessions

    ```
    [
        {
            "aliases": ["chr19"],
            "assembly_unit": "Primary Assembly",
            "length": 58617616,
            "name": "19",
            "refseq_ac": "NC_000019.10",
            "relationship": "=",
            "sequence_role": "assembled-molecule",
        }
    ]
    ```

    For the above sample record, this function adds the following aliases:
      * GRCh38:19
      * GRCh38:chr19
    to the sequence referred to by refseq:NC_000019.10.

    """
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir, writeable=True)

    assemblies = bioutils.assemblies.get_assemblies()
    if opts.reload_all:
        assemblies_to_load = sorted(assemblies)
    else:
        namespaces = [
            r["namespace"]
            for r in sr.aliases._db.execute("select distinct namespace from seqalias")  # noqa: SLF001
        ]
        assemblies_to_load = sorted(k for k in assemblies if k not in namespaces)
    _logger.info("%s assemblies to load", len(assemblies_to_load))

    ncbi_alias_map = {
        r["alias"]: r["seq_id"]
        for r in sr.aliases.find_aliases(namespace="NCBI", current_only=False)
    }

    for assy_name in tqdm.tqdm(assemblies_to_load, unit="assembly"):
        _logger.debug("loading %s", assy_name)
        sequences = assemblies[assy_name]["sequences"]
        eq_sequences = [s for s in sequences if s["relationship"] in ("=", "<>")]
        if not eq_sequences:
            _logger.info("No '=' sequences to load for %s; skipping", assy_name)
            continue

        # all assembled-molecules (1..22, X, Y, MT) have ncbi aliases in seqrepo
        not_in_seqrepo = [
            s["refseq_ac"] for s in eq_sequences if s["refseq_ac"] not in ncbi_alias_map
        ]
        if not_in_seqrepo:
            _logger.warning(
                "Assembly %s references %s accessions not in SeqRepo instance %s (e.g., %s)",
                assy_name,
                len(not_in_seqrepo),
                opts,
                ", ".join([*not_in_seqrepo[:5], "..."]),
            )
            if not opts.partial_load:
                _logger.warning("Skipping %s (-p to enable partial loading)", assy_name)
                continue

        eq_sequences = [es for es in eq_sequences if es["refseq_ac"] in ncbi_alias_map]
        _logger.info("Loading %s new accessions for assembly %s", len(eq_sequences), assy_name)

        for s in eq_sequences:
            seq_id = ncbi_alias_map[s["refseq_ac"]]
            aliases = [{"namespace": assy_name, "alias": a} for a in [s["name"]] + s["aliases"]]
            for alias in aliases:
                sr.aliases.store_alias(seq_id=seq_id, **alias)
                _logger.debug(
                    "Added assembly alias %s:%s for %s", alias["namespace"], alias["alias"], seq_id
                )
        sr.commit()


def export(opts: argparse.Namespace) -> None:
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir)

    if opts.ALIASES:

        def alias_generator() -> Generator:
            for alias in set(opts.ALIASES):
                yield from sr.aliases.find_aliases(
                    namespace=opts.namespace,  # None okay
                    alias=alias,
                    translate_ncbi_namespace=True,
                )

        def _rec_iterator_aliases() -> Generator:
            """Yield (srec, [arec]) tuples to export"""
            grouped_alias_iterator = itertools.groupby(
                alias_generator(), key=lambda arec: (arec["seq_id"])
            )
            for seq_id, arecs in grouped_alias_iterator:
                srec = sr.sequences.fetch_seqinfo(seq_id)
                srec["seq"] = sr.sequences.fetch(seq_id)
                yield srec, arecs

        _rec_iterator = _rec_iterator_aliases

    elif opts.namespace:

        def _rec_iterator_namespace() -> Generator:
            """Yield (srec, [arec]) tuples to export"""
            alias_iterator = sr.aliases.find_aliases(
                namespace=opts.namespace, translate_ncbi_namespace=True
            )
            grouped_alias_iterator = itertools.groupby(
                alias_iterator, key=lambda arec: (arec["seq_id"])
            )
            for seq_id, arecs in grouped_alias_iterator:
                srec = sr.sequences.fetch_seqinfo(seq_id)
                srec["seq"] = sr.sequences.fetch(seq_id)
                yield srec, arecs

        _rec_iterator = _rec_iterator_namespace

    else:

        def _rec_iterator_sr() -> Generator:
            yield from sr

        _rec_iterator = _rec_iterator_sr

    for srec, arecs in _rec_iterator():
        nsad = _convert_alias_records_to_ns_dict(arecs)
        aliases = [f"{ns}:{a}" for ns, aliases in sorted(nsad.items()) for a in aliases]
        print(">" + " ".join(aliases))
        for line in _wrap_lines(srec["seq"], 100):
            print(line)


def export_aliases(opts: argparse.Namespace) -> None:
    """Print known aliases to console"""
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir)
    alias_iterator = sr.aliases.find_aliases(translate_ncbi_namespace=True)
    grouped_alias_iterator = itertools.groupby(alias_iterator, key=lambda arec: (arec["seq_id"]))
    for _, arecs in grouped_alias_iterator:
        if opts.namespace and not any(
            arec for arec in arecs if arec["namespace"] == opts.namespace
        ):
            continue
        nsaliases = [f"{a['namespace']}:{a['alias']}" for a in arecs]
        # TODO: Tech debt: These are hacks to work around that GA4GH ids
        # aren't officially in seqrepo yet.
        nsaliases.sort(key=lambda a: (not a.startswith("VMC:"), a))  # VMC first
        nsaliases[0] = nsaliases[0].replace("VMC:GS_", "GA4GH:SQ.")
        print("\t".join(nsaliases))


def fetch_load(opts: argparse.Namespace) -> None:
    disable_bar = _logger.getEffectiveLevel() < logging.WARNING

    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir, writeable=True)

    ac_bar = tqdm.tqdm(opts.accessions, unit="acs", disable=disable_bar)
    for ac in ac_bar:
        ac_bar.set_description(ac)
        aliases_cur = sr.aliases.find_aliases(namespace=opts.namespace, alias=ac)
        if aliases_cur:
            _logger.info("%s already in %s", ac, sr)
            continue
        seq = bioutils.seqfetcher.fetch_seq(ac)
        aliases = [{"namespace": opts.namespace, "alias": ac}]
        n_sa, n_aa = sr.store(seq, aliases)

    sr.commit()


def init(opts: argparse.Namespace) -> None:
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    if os.path.exists(seqrepo_dir) and len(os.listdir(seqrepo_dir)) > 0:
        raise OSError(f"{seqrepo_dir} exists and is not empty")
    _ = SeqRepo(seqrepo_dir, writeable=True)


def list_local_instances(opts: argparse.Namespace) -> None:
    instances = _get_local_instances(opts)
    print(f"Local instances ({opts.root_directory})")
    for i in instances:
        print("  " + i)


def list_remote_instances(opts: argparse.Namespace) -> None:
    instances = _get_remote_instances(opts)
    print(f"Remote instances ({opts.remote_host})")
    for i in instances:
        print("  " + i)


def load(opts: argparse.Namespace) -> None:
    # TODO: drop this test
    if opts.namespace == "-":
        raise RuntimeError("namespace == '-' is no longer supported")

    disable_bar = _logger.getEffectiveLevel() < logging.WARNING

    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    if not os.path.isdir(seqrepo_dir):
        raise RuntimeError(
            f"{seqrepo_dir}: You must manually initialize the repo first (with `seqrepo init`)"
        )
    sr = SeqRepo(seqrepo_dir, writeable=True)

    n_seqs_seen = n_seqs_added = n_aliases_added = 0
    fn_bar = tqdm.tqdm(opts.fasta_files, unit="file", disable=disable_bar)
    for fn in fn_bar:
        fn_bar.set_description(os.path.basename(fn))
        if fn == "-":
            fh = sys.stdin
        elif fn.endswith((".gz", ".bgz")):
            fh = gzip.open(fn, mode="rt", encoding="ascii")  # noqa: SIM115
        else:
            fh = open(fn, encoding="ascii")  # noqa: SIM115
        _logger.info("Opened %s", fn)
        seq_bar = tqdm.tqdm(
            FastaIter(fh),  # type: ignore
            unit=" seqs",
            disable=disable_bar,
            leave=False,
        )
        for defline, seq in seq_bar:  # type: ignore
            n_seqs_seen += 1
            seq_bar.set_description(
                f"sequences: {n_seqs_added}/{n_seqs_seen} added/seen; aliases: {n_aliases_added} added"
            )
            aliases = parse_defline(defline, opts.namespace)
            validate_aliases(aliases)
            n_sa, n_aa = sr.store(seq, aliases)
            n_seqs_added += n_sa
            n_aliases_added += n_aa
    sr.commit()


def pull(opts: argparse.Namespace) -> None:
    remote_instances = _get_remote_instances(opts)
    if opts.instance_name:
        instance_name = opts.instance_name
        if instance_name not in remote_instances:
            raise KeyError(f"{instance_name}: not in list of remote instance names")
    else:
        instance_name = remote_instances[-1]
        _logger.info("most recent seqrepo instance is %s", instance_name)

    local_instances = _get_local_instances(opts)
    if instance_name in local_instances:
        _logger.warning("%s: instance already exists; skipping", instance_name)
        return

    tmp_dir = tempfile.mkdtemp(dir=opts.root_directory, prefix=instance_name + ".")
    os.rmdir(tmp_dir)  # let rsync create it the directory

    cmd = [opts.rsync_exe, "-rtHP", "--no-motd"]
    if local_instances:
        latest_local_instance = local_instances[-1]
        cmd += ["--link-dest=" + os.path.join(opts.root_directory, latest_local_instance) + "/"]
    cmd += [f"{opts.remote_host}::seqrepo/{instance_name}/", tmp_dir]

    _logger.debug("Executing: %s", " ".join(cmd))
    if not opts.dry_run:
        subprocess.check_call(cmd)  # noqa: S603
        dst_dir = os.path.join(opts.root_directory, instance_name)
        os.rename(tmp_dir, dst_dir)
        _logger.info("%s: successfully updated (%s)", instance_name, dst_dir)
        if opts.update_latest:
            update_latest(opts, instance_name)


def show_status(opts: argparse.Namespace) -> SeqRepo:
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    tot_size = sum(
        os.path.getsize(os.path.join(dirpath, filename))
        for dirpath, dirnames, filenames in os.walk(seqrepo_dir)
        for filename in filenames
    )

    sr = SeqRepo(seqrepo_dir)
    print(f"seqrepo {__version__}")
    print(f"instance directory: {sr._root_dir}, {tot_size / 1e9:.1f} GB")  # noqa: SLF001
    print(
        f"backends: fastadir (schema {sr.sequences.schema_version()}), seqaliasdb (schema {sr.aliases.schema_version()}) "
    )
    print(
        "sequences: {ss[n_sequences]} sequences, {ss[tot_length]} residues, "
        "{ss[n_files]} files".format(ss=sr.sequences.stats())
    )
    print(
        "aliases: {sa[n_aliases]} aliases, {sa[n_current]} current, "
        "{sa[n_namespaces]} namespaces, {sa[n_sequences]} sequences".format(sa=sr.aliases.stats())
    )
    return sr


def snapshot(opts: argparse.Namespace) -> None:
    """Snapshot a seqrepo data directory

    * hardlink sequence files
    * copy sqlite databases
    * remove write permissions from directories
    """
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)

    dst_dir = opts.destination_name
    if not dst_dir.startswith("/"):
        # interpret dst_dir as relative to parent dir of seqrepo_dir
        dst_dir = os.path.join(opts.root_directory, dst_dir)

    src_dir = os.path.realpath(seqrepo_dir)
    dst_dir = os.path.realpath(dst_dir)

    if os.path.commonpath([src_dir, dst_dir]).startswith(src_dir):
        raise RuntimeError(f"Cannot nest seqrepo directories ({dst_dir} is within {src_dir})")

    if os.path.exists(dst_dir):
        raise OSError(dst_dir + ": File exists")

    tmp_dir = tempfile.mkdtemp(prefix=dst_dir + ".")

    _logger.debug("src_dir = %s", src_dir)
    _logger.debug("dst_dir = %s", dst_dir)
    _logger.debug("tmp_dir = %s", tmp_dir)

    # TODO: cleanup of tmpdir on failure
    os.makedirs(tmp_dir, exist_ok=True)
    wd = os.getcwd()
    os.chdir(src_dir)

    # make destination directories (walk is top-down)
    for rp in (
        os.path.join(dirpath, dirname)
        for dirpath, dirnames, _ in os.walk(".")
        for dirname in dirnames
    ):
        dp = os.path.join(tmp_dir, rp)
        os.mkdir(dp)

    # hard link sequence files
    for rp in (
        os.path.join(dirpath, filename)
        for dirpath, _, filenames in os.walk(".")
        for filename in filenames
        if ".bgz" in filename
    ):
        dp = os.path.join(tmp_dir, rp)
        os.link(rp, dp)

    # copy sqlite databases
    for rp in ["aliases.sqlite3", "sequences/db.sqlite3"]:
        dp = os.path.join(tmp_dir, rp)
        shutil.copyfile(rp, dp)

    # recursively drop write perms on snapshot
    mode_aw = stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH

    def _drop_write(p: str) -> None:
        mode = os.lstat(p).st_mode
        new_mode = mode & ~mode_aw
        os.chmod(p, new_mode)

    for dp in (
        os.path.join(dirpath, dirent)
        for dirpath, dirnames, filenames in os.walk(tmp_dir)
        for dirent in dirnames + filenames
    ):
        _drop_write(dp)
    _drop_write(tmp_dir)
    os.rename(tmp_dir, dst_dir)

    _logger.info("snapshot created in %s", dst_dir)
    os.chdir(wd)


def start_shell(opts: argparse.Namespace) -> None:
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir)  # noqa: F841
    import IPython  # noqa: PLC0415

    IPython.embed(
        header="\n".join(
            [
                "seqrepo (https://github.com/biocommons/biocommons.seqrepo/)",
                "version: " + __version__,
                "instance path: " + seqrepo_dir,
            ]
        )
    )


def upgrade(opts: argparse.Namespace) -> None:
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir, writeable=False)
    print(f"upgraded to schema version {sr.sequences.schema_version()}")


def update_digests(opts: argparse.Namespace) -> None:
    """Update sequence digests"""
    seqrepo_dir = os.path.join(opts.root_directory, opts.instance_name)
    sr = SeqRepo(seqrepo_dir, writeable=True)
    for srec in tqdm.tqdm(sr.sequences):
        sr._update_digest_aliases(srec["seq_id"], srec["seq"])  # noqa: SLF001


def update_latest(opts: argparse.Namespace, mri: str | None = None) -> None:
    """Update `latest` symlink"""
    if not mri:
        instances = _get_local_instances(opts)
        if not instances:
            _logger.error("No seqrepo instances in %s", opts.root_directory)
            return
        mri = instances[-1]
    dst = os.path.join(opts.root_directory, "latest")
    with contextlib.suppress(OSError):
        os.unlink(dst)
    os.symlink(mri, dst)
    _logger.info("Linked `latest` -> `%s`", mri)


def main() -> None:
    """Run CLI"""
    opts = parse_arguments()
    _check_rsync_binary(opts)

    verbose_log_level = (
        logging.WARNING
        if opts.verbose == 0
        else logging.INFO
        if opts.verbose == 1
        else logging.DEBUG
    )
    logging.basicConfig(level=verbose_log_level)
    opts.func(opts)


############################################################################
# INTERNAL


def _convert_alias_records_to_ns_dict(records: Iterable[dict]) -> dict:
    """Convert a set of alias db records to a dict

    IE like {ns: [aliases], ...}

    aliases are lexicographicaly sorted
    """
    records = sorted(records, key=lambda r: (r["namespace"], r["alias"]))
    return {
        g: [r["alias"] for r in gi]
        for g, gi in itertools.groupby(records, key=lambda r: r["namespace"])
    }


def _wrap_lines(seq: str, line_width: int) -> Iterator[str]:
    for i in range(0, len(seq), line_width):
        yield seq[i : i + line_width]


if __name__ == "__main__":
    main()
