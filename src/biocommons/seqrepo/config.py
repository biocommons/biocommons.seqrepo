import os

try:
    seqrepo_env_var = os.environ.get("SEQREPO_LRU_CACHE_MAXSIZE", "1000000")
    SEQREPO_LRU_CACHE_MAXSIZE = int(seqrepo_env_var)
except ValueError:
    if seqrepo_env_var.lower() == 'none':
        SEQREPO_LRU_CACHE_MAXSIZE = None
    else:
        raise ValueError('SEQREPO_LRU_CACHE_MAXSIZE must be a valid int, none, or not set, '
                         'currently it is ' + seqrepo_env_var)
