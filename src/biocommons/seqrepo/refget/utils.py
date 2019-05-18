from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import hexlify, unhexlify
import re

from bioutils.accessions import infer_namespaces


def hex_to_base64url(s):
    return urlsafe_b64encode(unhexlify(s)).decode("ascii")

def base64url_to_hex(s):
    return hexlify(urlsafe_b64decode(s)).decode("ascii")

def get_sequence_id(sr, query):
    """determine sequence_ids after guessing form of query

    The query may be:
      * A fully-qualified sequence alias (e.g., VMC:0123 or refseq:NM_01234.5)
      * A digest or digest prefix from VMC, TRUNC512, or MD5
      * A sequence accession (without namespace)
 
    The first match will be returned.
    """

    for ns, a in _generate_nsa_options(query):
        if ns == "refseq":      # TODO: Resolve seqrepo to just one
            ns = "RefSeq"
        aliases = list(sr.aliases.find_aliases(namespace=ns, alias=a))
        if aliases:
            break
    seq_ids = set(a["seq_id"] for a in aliases)
    
    if len(seq_ids) == 0:
        return None
    if len(seq_ids) > 1:
        raise RuntimeError(f"Multiple distinct sequences found for {query}")
    return seq_ids.pop()


############################################################################
# INTERNAL

def _generate_nsa_options(query):
    """
    >>> _generate_nsa_options("NM_000551.3")
    [('refseq', 'NM_000551.3')]

    >>> _generate_nsa_options("ENST00000530893.6")
    [('ensembl', 'ENST00000530893.6')]

    >>> _generate_nsa_options("gi:123456789")
    ['gi', '123456789']

    >>> _generate_nsa_options("01234abcde")
    [('MD5', '01234abcde%'), ('VMC', 'GS_ASNKvN4=%')]

    """

    if ":" in query:
        # interpret as fully-qualified identifier
        nsa_options = [query.split(sep=":", maxsplit=1)]
        return nsa_options

    namespaces = infer_namespaces(query)
    if namespaces:
        nsa_options = [(ns, query) for ns in namespaces]
        return nsa_options
    
    if query.startswith("GS_"):
        nsa_options = [("VMC", query + "%")]
        return nsa_options
    
    # if hex, try md5 and TRUNC512
    if re.match(r"^(?:[0-9A-Fa-f]+)$", query):
        nsa_options = [("MD5", query + "%")]
        # TRUNC512 isn't in seqrepo; synthesize equivalent VMC
        id_b64u = hex_to_base64url(query)
        nsa_options += [("VMC", "GS_" + id_b64u + "%")]
        return nsa_options

    return [(None, query)]
