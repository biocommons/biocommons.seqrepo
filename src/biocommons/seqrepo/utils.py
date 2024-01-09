import os
import re
from typing import Optional

from biocommons.seqrepo.config import SEQREPO_FD_CACHE_SIZE_ENV_NAME

ncbi_defline_re = re.compile(r"(?P<namespace>ref)\|(?P<alias>[^|]+)")
invalid_alias_chars_re = re.compile(r"[^-+./_\w]")


def resolve_fd_cache_size(internal_fd_cache_size: Optional[int]) -> Optional[int]:
    """
    Determines what the fd_cache_size should be set to. If the SEQREPO_FD_CACHE_SIZE env var
    is set, that value takes priority, otherwise whatever passed into the SeqRepo init is used. If
    nothing is set, it'll end up being 0. Setting this value helps performance of reading the
    fasta files, but one must be careful of resource exhaustion.
    Details:
        0 - No cache at all
        None - Unbounded caching
        >=1 - Specific cache size
    """
    env_fd_cache_size = os.environ.get(SEQREPO_FD_CACHE_SIZE_ENV_NAME)
    # If the env var is not set, use what is defined in the code
    if env_fd_cache_size is None:
        return internal_fd_cache_size

    # Else parse out what is in the env var
    if env_fd_cache_size.lower() == "none":
        return None
    try:
        env_fd_cache_size_i = int(env_fd_cache_size)
    except ValueError:
        raise ValueError(
            f"{SEQREPO_FD_CACHE_SIZE_ENV_NAME} must be a valid int, none, or not set, "
            "currently it is " + env_fd_cache_size
        )
    return env_fd_cache_size_i


def parse_defline(defline, namespace):
    """parse fasta defline, returning a list of zero or more dicts
    like [{namespace: , alias: }]

    """

    alias_string = defline.split()[0]  # up to first whitespace
    if alias_string.startswith(">"):
        alias_string = alias_string[1:]

    aliases = [m.groupdict() for m in ncbi_defline_re.finditer(alias_string)]
    if aliases:
        # looks like NCBI pipe-delimited (namespace,accession) pairs
        for a in aliases:
            if a["namespace"] == "ref":
                a["namespace"] = "refseq"
    else:
        aliases = [{"namespace": namespace, "alias": alias_string}]

    return aliases


def validate_aliases(aliases):
    """given a list of {"namespace":, "alias":} dictionaries, validate
    accordinate to rules.  Raise RuntimeError if fails."""

    for alias_rec in aliases:
        namespace, alias = alias_rec["namespace"], alias_rec["alias"]

        if invalid_alias_chars_re.search(alias):
            raise RuntimeError(
                f"alias {alias} contains invalid char (one of {invalid_alias_chars_re})"
            )

        if namespace.startswith("Ensembl"):
            if alias.startswith("ENS") and "." not in alias:
                raise RuntimeError(f"{namespace} alias {alias} is unversioned")
        elif namespace in ("NCBI", "refseq"):
            if "." not in alias:
                raise RuntimeError(f"{namespace} alias {alias} is unversioned")
    return True
