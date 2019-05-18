"""thread global access for refget API"""


import os

from biocommons.seqrepo import SeqRepo
from flask import g


seqrepo_base_dir = "/usr/local/share/seqrepo"
seqrepo_instance_name = "latest"
seqrepo_path = os.path.join(seqrepo_base_dir, seqrepo_instance_name)

def get_seqrepo():
    return _get_or_create(
        "seqrepo",
        lambda: SeqRepo(root_dir=seqrepo_path, translate_ncbi_namespace=True))


def _get_or_create(k, f):
    k = '_' + k
    o = getattr(g, k, None)
    if o is None:
        o = f()
        setattr(g, k, o)
    return o
