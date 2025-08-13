"""Provide some simple utilities for reading from FASTA files"""

import re

ncbi_defline_re = re.compile(r"(?P<namespace>ref)\|(?P<alias>[^|]+)")
invalid_alias_chars_re = re.compile(r"[^-+./_\w]")


def parse_defline(defline: str, namespace: str) -> list[dict[str, str]]:
    """Parse fasta defline, returning a list of zero or more dicts like [{namespace: , alias: }]"""
    alias_string = defline.split()[0]  # up to first whitespace
    alias_string = alias_string.removeprefix(">")

    aliases = [m.groupdict() for m in ncbi_defline_re.finditer(alias_string)]
    if aliases:
        # looks like NCBI pipe-delimited (namespace,accession) pairs
        for a in aliases:
            if a["namespace"] == "ref":
                a["namespace"] = "refseq"
    else:
        aliases = [{"namespace": namespace, "alias": alias_string}]

    return aliases


def validate_aliases(aliases: list[dict[str, str]]) -> bool:
    """Given a list of {"namespace":, "alias":} dictionaries, validate accordinate to rules.

    :raise RuntimeError: if fails.
    """
    for alias_rec in aliases:
        namespace, alias = alias_rec["namespace"], alias_rec["alias"]

        if invalid_alias_chars_re.search(alias):
            raise RuntimeError(
                f"alias {alias} contains invalid char (one of {invalid_alias_chars_re})"
            )

        if namespace.startswith("Ensembl"):
            if alias.startswith("ENS") and "." not in alias:
                raise RuntimeError(f"{namespace} alias {alias} is unversioned")
        elif (namespace in ("NCBI", "refseq")) and ("." not in alias):
            raise RuntimeError(f"{namespace} alias {alias} is unversioned")
    return True
