"""provides an abstract class for all data access required for
VRS, and a concrete implementation based on seqrepo.

See https://vr-spec.readthedocs.io/en/1.1/impl-guide/required_data.html

"""

import datetime
import functools
import logging
import os
from abc import ABC, abstractmethod
from http import HTTPStatus
from typing import Optional
from urllib.parse import urlparse

import requests
from bioutils.accessions import coerce_namespace

from .seqrepo import SeqRepo

_logger = logging.getLogger(__name__)


class _DataProxy(ABC):
    """abstract class / interface for VRS data needs

    The proxy MUST support the use of GA4GH sequence identifers (i.e.,
    `ga4gh:SQ...`) as keys, and return these identifiers among the
    aliases for a sequence.  These identifiers may be supported
    natively by the data source or synthesized by the proxy from the
    data source or synthesized.

    """

    @abstractmethod
    def get_sequence(
        self, identifier: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> str:
        """return the specified sequence or subsequence

        start and end are optional

        If the given sequence does not exist, KeyError is raised.

        >> dp.get_sequence("NM_000551.3", 0, 10)
        'CCTCGCCTCC'

        """

    @abstractmethod
    def get_metadata(self, identifier: str) -> dict:
        """for a given identifier, return a structure (dict) containing
        sequence length, aliases, and other optional info

        If the given sequence does not exist, KeyError is raised.

        >> dp.get_metadata("NM_000551.3")
        {'added': '2016-08-24T05:03:11Z',
         'aliases': ['MD5:215137b1973c1a5afcf86be7d999574a',
                     'RefSeq:NM_000551.3',
                     'SEGUID:T12L0p2X5E8DbnL0+SwI4Wc1S6g',
                     'SHA1:4f5d8bd29d97e44f036e72f4f92c08e167354ba8',
                     'ga4gh:SQ.v_QTc1p-MUYdgrRv4LMT6ByXIOsdw3C_',
                     'gi:319655736'],
         'alphabet': 'ACGT',
         'length': 4560}

        """
        raise NotImplementedError

    @functools.lru_cache(maxsize=128)  # noqa: B019
    def translate_sequence_identifier(
        self, identifier: str, namespace: Optional[str] = None
    ) -> list[str]:
        """Translate given identifier to a list of identifiers in the
        specified namespace.

        `identifier` must be a string
        `namespace` is case-sensitive

        On success, returns string identifier.  Raises KeyError if given
        identifier isn't found.

        """

        try:
            md = self.get_metadata(identifier)
        except (ValueError, KeyError, IndexError) as e:
            raise KeyError(identifier) from e
        aliases = list(set(md["aliases"]))  # ensure uniqueness
        if namespace is not None:
            nsd = namespace + ":"
            aliases = [a for a in aliases if a.startswith(nsd)]
        return aliases


class _SeqRepoDataProxyBase(_DataProxy):
    # wraps seqreqpo classes in order to provide translation to/from
    # `ga4gh` identifiers.

    def get_metadata(self, identifier: str) -> dict:
        md = self._get_metadata(identifier)
        md["aliases"] = list(md["aliases"])
        return md

    def get_sequence(self, identifier: str, start: Optional[int] = None, end: Optional[int] = None):
        return self._get_sequence(identifier, start=start, end=end)

    @abstractmethod
    def _get_metadata(self, identifier: str) -> dict:  # pragma: no cover
        raise NotImplementedError

    @abstractmethod
    def _get_sequence(
        self, identifier: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> str:  # pragma: no cover
        raise NotImplementedError


class SeqRepoDataProxy(_SeqRepoDataProxyBase):
    """DataProxy based on a local instance of SeqRepo"""

    def __init__(self, sr: SeqRepo) -> None:
        super().__init__()
        self.sr = sr

    def _get_sequence(
        self, identifier: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> str:
        # fetch raises KeyError if not found
        return self.sr.fetch_uri(coerce_namespace(identifier), start, end)

    def _get_metadata(self, identifier: str) -> dict:
        ns, a = coerce_namespace(identifier).split(":", 2)
        r = list(self.sr.aliases.find_aliases(namespace=ns, alias=a))
        if len(r) == 0:
            raise KeyError(identifier)
        seq_id = r[0]["seq_id"]
        seqinfo = self.sr.sequences.fetch_seqinfo(seq_id)
        aliases = self.sr.aliases.find_aliases(seq_id=seq_id)
        md = {
            "length": seqinfo["len"],
            "alphabet": seqinfo["alpha"],
            "added": _isoformat(seqinfo["added"]),
            "aliases": [f"{a['namespace']}:{a['alias']}" for a in aliases],
        }
        return md


class SeqRepoRESTDataProxy(_SeqRepoDataProxyBase):
    """DataProxy based on a REST instance of SeqRepo, as provided by seqrepo-rest-services"""

    rest_version = "1"

    def __init__(self, base_url: str) -> None:
        super().__init__()
        self.base_url = f"{base_url}/{self.rest_version}/"

    def _get_sequence(
        self, identifier: str, start: Optional[int] = None, end: Optional[int] = None
    ) -> str:
        url = self.base_url + f"sequence/{identifier}"
        params = {"start": start, "end": end}
        _logger.info("Fetching %s %s", url, params if (start or end) else "")
        resp = requests.get(url, params=params, timeout=60)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise KeyError(identifier)
        resp.raise_for_status()
        return resp.text

    def _get_metadata(self, identifier: str) -> dict:
        url = self.base_url + f"metadata/{identifier}"
        _logger.info("Fetching %s", url)
        resp = requests.get(url, timeout=60)
        if resp.status_code == HTTPStatus.NOT_FOUND:
            raise KeyError(identifier)
        resp.raise_for_status()
        data = resp.json()
        return data


def _isoformat(o: datetime.datetime):
    """convert datetime.datetime to iso formatted timestamp

    >>> dt = datetime.datetime(2019, 10, 15, 10, 23, 41, 115927)
    >>> _isoformat(dt)
    '2019-10-15T10:23:41.115927Z'

    """

    # stolen from connexion flask_app.py
    if not isinstance(o, datetime.datetime):
        msg = f"Expected datetime.datetime, got {type(o).__name__}"
        raise TypeError(msg)
    if o.tzinfo:
        # eg: '2015-09-25T23:14:42.588601+00:00'
        return o.isoformat("T")
    # No timezone present - assume UTC.
    # eg: '2015-09-25T23:14:42.588601Z'
    return o.isoformat("T") + "Z"


# Future implementations
# * The RefGetDataProxy is waiting on support for sequence lookup by alias
# class RefGetDataProxy(_DataProxy):
#     def __init__(self, base_url):
#         super().__init__()
#         self.base_url = base_url


def create_dataproxy(uri: Optional[str] = None) -> _DataProxy:
    """Create a dataproxy from uri or SEQREPO_DATAPROXY_URI

    Currently accepted URI schemes:

    * seqrepo+file:///path/to/seqrepo/root
    * seqrepo+:../relative/path/to/seqrepo/root
    * seqrepo+http://localhost:5000/seqrepo
    * seqrepo+https://somewhere:5000/seqrepo

    """

    uri = uri or os.environ.get("SEQREPO_DATAPROXY_URI", None)

    if uri is None:
        msg = "No data proxy URI provided or found in SEQREPO_DATAPROXY_URI"
        raise ValueError(msg)

    parsed_uri = urlparse(uri)
    scheme = parsed_uri.scheme

    if "+" not in scheme:
        msg = "create_dataproxy scheme must include provider (e.g., `seqrepo+http:...`)"
        raise ValueError(msg)

    provider, proto = scheme.split("+")

    if provider == "seqrepo":
        if proto in ("", "file"):
            sr = SeqRepo(root_dir=parsed_uri.path)
            dp = SeqRepoDataProxy(sr)
        elif proto in ("http", "https"):
            dp = SeqRepoRESTDataProxy(uri[len(provider) + 1 :])
        else:
            msg = f"SeqRepo URI scheme {parsed_uri.scheme} not implemented"
            raise ValueError(msg)

    else:
        msg = f"DataProxy provider {provider} not implemented"
        raise ValueError(msg)

    return dp
