import logging

from connexion import NoContent

from ..globals import get_seqrepo
from ..utils import get_sequence_id, base64url_to_hex


_logger = logging.getLogger(__name__)


def get(id):
    sr = get_seqrepo()
    seq_id = get_sequence_id(sr, id)

    if not seq_id:
        return NoContent, 404

    seqinfo = sr.sequences.fetch_seqinfo(seq_id)
    aliases = sr.aliases.fetch_aliases(seq_id)

    md5_rec = [a for a in aliases if a["namespace"] == "MD5"]
    md5_id = md5_rec[0]["alias"] if md5_rec else None

    md = {
        "id": seq_id,
        "md5": md5_id,
        "trunc512": base64url_to_hex(seq_id),
        "length": seqinfo["len"],
        "aliases": [
            {"naming_authority": a["namespace"], "alias": a["alias"]}
            for a in aliases
            ]
        }

    return {"metadata": md}, 200
