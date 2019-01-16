import logging
import os
import re

import bioutils.digests

from .seqaliasdb import SeqAliasDB
from .fastadir import FastaDir
from .py2compat import makedirs

_logger = logging.getLogger(__name__)

# commit thresholds: commit fasta file and db when any one is exceeded
ct_n_seqs = 20000
ct_n_aliases = 60000
ct_n_residues = 1e9

# namespace-alias separator
nsa_sep = u":"

uri_re = re.compile(r"([^:]+):(.+)")


class SeqRepo(object):
    """Implements a filesystem-backed non-redundant repository of
    sequences and sequence aliases.

    The current implementation uses block-gzip fasta files for
    sequence storage, essentially as a transaction-based journal, and
    a very simple sqlite database for aliases.

    Updates add new sequence files and new aliases.  This approach
    means that distribution of updates involve incremental transfers
    of sequences and a wholesale replacement of the database.

    The pysam.FastaFile module is key here as it provides fasa index
    to bgz files and fast sequence slicing.

    """

    def __init__(self, root_dir, writeable=False, upcase=True, translate_ncbi_namespace=False, check_same_thread=False):
        self._root_dir = root_dir
        self._upcase = upcase
        self._db_path = os.path.join(self._root_dir, "aliases.sqlite3")
        self._seq_path = os.path.join(self._root_dir, "sequences")
        self._pending_sequences = 0
        self._pending_sequences_len = 0
        self._pending_aliases = 0
        self._writeable = writeable
        self.translate_ncbi_namespace = translate_ncbi_namespace
        self._check_same_thread = True if writeable else check_same_thread

        if self._writeable:
            makedirs(self._root_dir, exist_ok=True)

        if not os.path.exists(self._root_dir):
            raise OSError("Unable to open SeqRepo directory {}".format(self._root_dir))

        self.sequences = FastaDir(self._seq_path, writeable=self._writeable, check_same_thread=self._check_same_thread)
        self.aliases = SeqAliasDB(self._db_path,
                                  writeable=self._writeable,
                                  translate_ncbi_namespace=self.translate_ncbi_namespace,
                                  check_same_thread=self._check_same_thread)

    def __contains__(self, nsa):
        ns, a = nsa.split(nsa_sep) if nsa_sep in nsa else (None, nsa)
        return self.aliases.find_aliases(alias=a, namespace=ns).fetchone() is not None

    def __getitem__(self, nsa):
        # lookup aliases, optionally namespaced, like NM_01234.5 or NCBI:NM_01234.5
        ns, a = nsa.split(nsa_sep) if nsa_sep in nsa else (None, nsa)
        return self.fetch(alias=a, namespace=ns)

    def __iter__(self):
        """iterate over all sequences, yielding tuples of (sequence_record, [alias_records])

        Both records are dicts.
        """
        for srec in self.sequences:
            arecs = self.aliases.fetch_aliases(srec["seq_id"])
            yield (srec, arecs)

    def __str__(self):
        return "SeqRepo(root_dir={self._root_dir}, writeable={self._writeable})".format(self=self)

    def commit(self):
        self.sequences.commit()
        self.aliases.commit()
        if self._pending_sequences + self._pending_aliases > 0:
            _logger.info("Committed {} sequences ({} residues) and {} aliases".format(
                self._pending_sequences, self._pending_sequences_len, self._pending_aliases))
        self._pending_sequences = 0
        self._pending_sequences_len = 0
        self._pending_aliases = 0


    def fetch(self, alias, start=None, end=None, namespace=None):
        seq_id = self._get_unique_seqid(alias=alias, namespace=namespace)
        return self.sequences.fetch(seq_id, start, end)


    def fetch_uri(self, uri, start=None, end=None):
        """fetch sequence for URI/CURIE of the form namespace:alias, such as
        NCBI:NM_000059.3.

        """

        namespace, alias = uri_re.match(uri).groups()
        return self.fetch(alias=alias, namespace=namespace, start=start, end=end)


    def store(self, seq, nsaliases):
        """nsaliases is a list of dicts, like:

          [{"namespace": "en", "alias": "rose"},
           {"namespace": "fr", "alias": "rose"},
           {"namespace": "es", "alias": "rosa"}]

        """
        if not self._writeable:
            raise RuntimeError("Cannot write -- opened read-only")

        if self._upcase:
            seq = seq.upper()

        try:
            seqhash = bioutils.digests.seq_seqhash(seq)
        except Exception as e:
            import pprint
            _logger.critical("Exception raised for " + pprint.pformat(nsaliases))
            raise
        seq_id = seqhash

        # add sequence if not present
        n_seqs_added = n_aliases_added = 0
        msg = "sh{nsa_sep}{seq_id:.10s}... ({l} residues; {na} aliases {aliases})".format(
            seq_id=seq_id,
            l=len(seq),
            na=len(nsaliases),
            nsa_sep=nsa_sep,
            aliases=", ".join("{nsa[namespace]}:{nsa[alias]}".format(nsa=nsa) for nsa in nsaliases))
        if seq_id not in self.sequences:
            _logger.info("Storing " + msg)
            if len(seq) > ct_n_residues:    # pragma: no cover
                _logger.debug("Precommit for large sequence")
                self.commit()
            self.sequences.store(seq_id, seq)
            n_seqs_added += 1
            self._pending_sequences += 1
            self._pending_sequences_len += len(seq)
            self._pending_aliases += self._update_digest_aliases(seq_id, seq)
        else:
            _logger.debug("Sequence exists: " + msg)

        # add/update external aliases for new and existing sequences
        # updating is optimized to load only new <seq_id,ns,alias> tuples
        existing_aliases = self.aliases.fetch_aliases(seq_id)
        ea_tuples = [(r["seq_id"], r["namespace"], r["alias"]) for r in existing_aliases]
        new_tuples = [(seq_id, r["namespace"], r["alias"]) for r in nsaliases]
        upd_tuples = set(new_tuples) - set(ea_tuples)
        if upd_tuples:
            _logger.info("{} new aliases for {}".format(len(upd_tuples), msg))
            for _, namespace, alias in upd_tuples:
                self.aliases.store_alias(seq_id=seq_id, namespace=namespace, alias=alias)
            self._pending_aliases += len(upd_tuples)
            n_aliases_added += len(upd_tuples)
        if (self._pending_sequences > ct_n_seqs or self._pending_aliases > ct_n_aliases
                or self._pending_sequences_len > ct_n_residues):    # pragma: no cover
            _logger.info("Hit commit thresholds ({self._pending_sequences} sequences, "
                        "{self._pending_aliases} aliases, {self._pending_sequences_len} residues)".format(self=self))
            self.commit()
        return n_seqs_added, n_aliases_added


    def translate_alias(self, alias, namespace=None, target_namespaces=None, translate_ncbi_namespace=None):
        """given an alias and optional namespace, return a list of all other
        aliases for same sequence

        """

        if translate_ncbi_namespace is None:
            translate_ncbi_namespace = self.translate_ncbi_namespace
        seq_id = self._get_unique_seqid(alias=alias, namespace=namespace)
        aliases = self.aliases.fetch_aliases(seq_id=seq_id,
                                             translate_ncbi_namespace=translate_ncbi_namespace)
        if target_namespaces:
            aliases = [a for a in aliases if a["namespace"] in target_namespaces]
        return aliases


    def translate_identifier(self, identifier, target_namespaces=None, translate_ncbi_namespace=None):
        """Given a string identifier, return a list of aliases (as
        identifiers) that refer to the same sequence.

        """
        namespace, alias = identifier.split(nsa_sep) if nsa_sep in identifier else (None, identifier)
        aliases = self.translate_alias(alias=alias,
                                       namespace=namespace,
                                       target_namespaces=target_namespaces,
                                       translate_ncbi_namespace=translate_ncbi_namespace)
        return [nsa_sep.join((a["namespace"], a["alias"])) for a in aliases]


    ############################################################################
    # Internal Methods 

    def _get_unique_seqid(self, alias, namespace):
        """given alias and namespace, return seq_id if exactly one distinct
        sequence id is found, raise KeyError if there's no match, or
        raise ValueError if there's more than one match.

        """

        recs = self.aliases.find_aliases(alias=alias, namespace=namespace)
        seq_ids = set(r["seq_id"] for r in recs)
        if len(seq_ids) == 0:
            raise KeyError("Alias {} (namespace: {})".format(alias, namespace))
        if len(seq_ids) > 1:
            # This should only happen when namespace is None
            raise KeyError("Alias {} (namespace: {}): not unique".format(alias, namespace))
        return seq_ids.pop()


    def _update_digest_aliases(self, seq_id, seq):

        """compute digest aliases for seq and update; returns number of digest
        aliases (some of which may have already existed)

        For the moment, sha512 is computed for seq_id separately from
        the sha512 here.  We should fix that.

        """

        ir = bioutils.digests.seq_vmc_identifier(seq)
        seq_aliases = [
            {
                "namespace": ir["namespace"],
                "alias": ir["accession"],
            },
            {
                "namespace": "SHA1",
                "alias": bioutils.digests.seq_sha1(seq)
            },
            {
                "namespace": "MD5",
                "alias": bioutils.digests.seq_md5(seq)
            },
            {
                "namespace": "SEGUID",
                "alias": bioutils.digests.seq_seguid(seq)
            },
        ]
        for sa in seq_aliases:
            self.aliases.store_alias(seq_id=seq_id, **sa)
        return len(seq_aliases)
