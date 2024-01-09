import os


def parse_caching_env_var(env_name, env_default):
    seqrepo_env_var = os.environ.get(env_name, env_default)
    if seqrepo_env_var.lower() == "none":
        return None

    try:
        seqrepo_env_var_int = int(seqrepo_env_var)
    except ValueError:
        raise ValueError(
            f"{env_name} must be a valid int, none, or not set, "
            "currently it is " + seqrepo_env_var
        )
    return seqrepo_env_var_int


SEQREPO_LRU_CACHE_MAXSIZE = parse_caching_env_var("SEQREPO_LRU_CACHE_MAXSIZE", "1000000")
# Using a default value here of -1 to differentiate not setting this value and an explicit None (unbounded cache)
SEQREPO_FD_CACHE_MAXSIZE = parse_caching_env_var("SEQREPO_FD_CACHE_MAXSIZE", "-1")
