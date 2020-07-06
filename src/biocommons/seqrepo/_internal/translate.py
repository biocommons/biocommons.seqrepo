"""translate namespaces

Translates between namespaces exposed in the API and those in the DB.
This is a temporary operation in order to create a smooth transition
for clients.  See biocommons.seqrepo#31 for background.

Use cases:
* Store: translate API namespace to DB namespace. e.g., "refseq" -> "NCBI"
* Find: as with store for query argument, plus translate DB to API for
  returned records.

All translations occur in seqaliasdb.

"""

import copy

translations = [
    # (DB namespace, API namespace)
    ("NCBI", "refseq"),
    ("Ensembl", "ensembl"),
    ("LRG", "lrg"),
    ]


ns_db2api = {db: api for db, api in translations}
ns_api2db = {api: db for db, api in translations}

def translate_alias_records(aliases_itr):
    """given an iterator of find_aliases results, return a stream with
    translated records"""
    
    for a in aliases_itr:
        yield a

        ns = a["namespace"]
        if ns in ns_db2api:
            a2 = copy.copy(a)
            a2["namespace"] = ns_db2api[ns]
            yield a2
