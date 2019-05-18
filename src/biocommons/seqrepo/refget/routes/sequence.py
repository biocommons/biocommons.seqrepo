import logging

from connexion import NoContent

from ..globals import get_seqrepo
from ..utils import get_sequence_id


_logger = logging.getLogger(__name__)


def get(id, start=None, end=None):
    sr = get_seqrepo()
    seq_id = get_sequence_id(sr, id)
    _logger.debug(f"{id} -> {seq_id}")
    try:
        return sr.sequences.fetch(seq_id, start, end)
    except KeyError:
        return NoContent, 404
    
