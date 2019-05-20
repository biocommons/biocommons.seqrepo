def get():
    return {"service": {
        "algorithms": ["md5", "trunc512"],
        "circular_supported" : False,
        "subsequence_limit": None,
        "supported_api_versions": ["1.0"],
    }}
