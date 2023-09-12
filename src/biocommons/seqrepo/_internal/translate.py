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
import datetime


def translate_db2api(namespace, alias):
    """
    >>> translate_db2api("VMC", "GS_1234")
    [('sha512t24u', '1234'), ('ga4gh', 'SQ.1234')]

    """

    if namespace == "NCBI":
        return [("refseq", alias)]
    if namespace == "Ensembl":
        return [("ensembl", alias)]
    if namespace == "LRG":
        return [("lrg", alias)]
    if namespace == "VMC":
        return [
            ("sha512t24u", alias[3:] if alias else None),
            ("ga4gh", "SQ." + alias[3:] if alias else None),
        ]
    return []


def translate_api2db(namespace, alias):
    """
    >>> translate_api2db("ga4gh", "SQ.1234")
    [('VMC', 'GS_1234')]

    """

    if namespace.lower() == "refseq":
        return [("NCBI", alias)]
    if namespace == "ensembl":
        return [("Ensembl", alias)]
    if namespace == "lrg":
        return [("LRG", alias)]
    if namespace == "sha512t24u":
        return [
            ("VMC", "GS_" + alias if alias else None),
        ]
    if namespace == "ga4gh":
        return [
            ("VMC", "GS_" + alias[3:]),
        ]
    return []


def translate_alias_records(aliases_itr):
    """given an iterator of find_aliases results, return a stream with
    translated records"""

    for arec in aliases_itr:
        yield arec

        for ns, a in translate_db2api(arec["namespace"], arec["alias"]):
            arec2 = copy.copy(arec)
            arec2["namespace"] = ns
            arec2["alias"] = a
            yield arec2


if __name__ == "__main__":
    aliases = [
        {
            "seqalias_id": 16,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "ncbiac/e",
            "added": datetime.datetime(2020, 7, 6, 5, 27, 23),
            "is_current": 1,
            "namespace": "Ensembl",
        },
        {
            "seqalias_id": 16,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "ncbiac/e",
            "added": datetime.datetime(2020, 7, 6, 5, 27, 23),
            "is_current": 1,
            "namespace": "ensembl",
        },
        {
            "seqalias_id": 3,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "be8a4c35767bb783a7b8b6dc04ba3718",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "MD5",
        },
        {
            "seqalias_id": 5,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "ncbiac",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "NCBI",
        },
        {
            "seqalias_id": 5,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "ncbiac",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "refseq",
        },
        {
            "seqalias_id": 4,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "5W5mCzikufDcezdNTGKLa9zricw",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "SEGUID",
        },
        {
            "seqalias_id": 2,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "e56e660b38a4b9f0dc7b374d4c628b6bdceb89cc",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "SHA1",
        },
        {
            "seqalias_id": 1,
            "seq_id": "9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "alias": "GS_9Sn3d56Fzds_c6ovS__sj1fbMd_Xd3J6",
            "added": datetime.datetime(2020, 7, 6, 5, 10, 57),
            "is_current": 1,
            "namespace": "VMC",
        },
    ]
