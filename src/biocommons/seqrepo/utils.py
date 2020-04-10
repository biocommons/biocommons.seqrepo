import re


ncbi_defline_re = re.compile(r"(?P<namespace>gi|ref)\|(?P<alias>[^|]+)")


def parse_defline(defline, namespace):
    """parse fasta defline, returning a list of zero or more dicts
    like [{namespace: , alias: }]

    """

    alias_string = defline.split()[0]  # up to first whitespace
    if alias_string.startswith(">"):
        alias_string = alias_string[1:]

    if namespace in ("refseq", "NCBI"):
        aliases = [m.groupdict() for m in ncbi_defline_re.finditer(alias_string)]
        if aliases:
            for a in aliases:
                if a["namespace"] == "ref":
                    a["namespace"] = "refseq"
            return aliases

    aliases = [{"namespace": namespace, "alias": alias_string}]

    return aliases
