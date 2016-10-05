import hashlib
import logging
import os

import bioutils.digests
import six

from .seqaliasdb import SeqAliasDB
from .fastadir import FastaDir
from .py2compat import makedirs

logger = logging.getLogger(__name__)

# commit thresholds: commit when any one is exceeded
ct_n_seqs = 20000
ct_n_aliases = 60000
ct_n_residues = 1e9

# namespace-alias separator
nsa_sep = ":"


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

    def __init__(self, root_dir, writeable=False, upcase=True):
        self._root_dir = root_dir
        self._upcase = upcase
        self._db_path = os.path.join(self._root_dir, "aliases.sqlite3")
        self._seq_path = os.path.join(self._root_dir, "sequences")
        self._pending_sequences = 0
        self._pending_sequences_len = 0
        self._pending_aliases = 0
        self._logger = logger    # avoids issue with logger going out of scope before __del__
        self._writeable = writeable

        if self._writeable:
            makedirs(self._root_dir, exist_ok=True)

        self.sequences = FastaDir(self._seq_path, writeable=self._writeable)
        self.aliases = SeqAliasDB(self._db_path, writeable=self._writeable)

    def fetch(self, alias, start=None, end=None, namespace=None):
        recs = self.aliases.find_aliases(alias=alias, namespace=namespace)

        seq_ids = set(r["seq_id"] for r in recs)
        if len(seq_ids) == 0:
            raise KeyError("Alias {} (namespace: {})".format(alias, namespace))
        if len(seq_ids) > 1:
            # This should only happen when namespace is None
            raise KeyError("Alias {} (namespace: {}): not unique".format(alias, namespace))

        return self.sequences.fetch(seq_ids.pop(), start, end)

    def __getitem__(self, nsa):
        # lookup aliases, optionally namespaced, like NM_01234.5 or ncbi:NM_01234.5
        ns, a = nsa.split(nsa_sep) if nsa_sep in nsa else (None, nsa)
        return self.fetch(alias=a, namespace=ns)

    def __contains__(self, nsa):
        ns, a = nsa.split(nsa_sep) if nsa_sep in nsa else (None, nsa)
        return self.aliases.find_aliases(alias=a, namespace=ns).fetchone() is not None

    def __iter__(self):
        """iterate over all sequences, yielding tuples of (sequence_record, [alias_records])

        Both records are dicts.
        """
        for srec in self.sequences:
            arecs = self.aliases.fetch_aliases(srec["seq_id"])
            yield (srec, arecs)

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

        seqhash = bioutils.digests.seq_seqhash(seq)
        seq_id = seqhash

        # add sequence if not present
        n_seqs_added = n_aliases_added = 0
        msg = "sh{nsa_sep}{seq_id:.10s}... ({l} residues; {na} aliases {aliases})".format(
            seq_id=seq_id, l=len(seq), na=len(nsaliases), nsa_sep=nsa_sep,
            aliases=", ".join("{nsa[namespace]}:{nsa[alias]}".format(nsa=nsa) for nsa in nsaliases))
        if seq_id not in self.sequences:
            logger.info("Storing " + msg)
            if len(seq) > ct_n_residues:  # pragma: no cover
                logger.debug("Precommit for large sequence")
                self.commit()
            self.sequences.store(seq_id, seq)
            seq_aliases = [
                {"namespace": "sh",
                 "alias": seqhash},
                {"namespace": "sha512",
                 "alias": bioutils.digests.seq_sha512(seq)},
                {"namespace": "sha1",
                 "alias": bioutils.digests.seq_sha1(seq)},
                {"namespace": "md5",
                 "alias": bioutils.digests.seq_md5(seq)},
                {"namespace": "seguid",
                 "alias": bioutils.digests.seq_seguid(seq)},
            ]
            for sa in seq_aliases:
                self.aliases.store_alias(seq_id=seq_id, **sa)
            self._pending_sequences += 1
            self._pending_sequences_len += len(seq)
            self._pending_aliases += len(seq_aliases)
            n_seqs_added += 1
        else:
            logger.debug("Sequence exists: " + msg)

        # add/update aliases
        # updating is optimized to load only new <seq_id,ns,alias> tuples
        existing_aliases = self.aliases.fetch_aliases(seq_id)
        ea_tuples = [(r["seq_id"], r["namespace"], r["alias"]) for r in existing_aliases]
        new_tuples = [(seq_id, r["namespace"], r["alias"]) for r in nsaliases]
        upd_tuples = set(new_tuples) - set(ea_tuples)
        if upd_tuples:
            logger.info("{} new aliases for {}".format(len(upd_tuples), msg))
            for _, namespace, alias in upd_tuples:
                self.aliases.store_alias(seq_id=seq_id, namespace=namespace, alias=alias)
            self._pending_aliases += len(upd_tuples)
            n_aliases_added += len(upd_tuples)
        if (self._pending_sequences > ct_n_seqs
            or self._pending_aliases > ct_n_aliases
            or self._pending_sequences_len > ct_n_residues):  # pragma: no cover
            logger.info("Hit commit thresholds ({self._pending_sequences} sequences, "
                        "{self._pending_aliases} aliases, {self._pending_sequences_len} residues)".format(self=self))
            self.commit()
        return n_seqs_added, n_aliases_added

    def commit(self):
        self.sequences.commit()
        self.aliases.commit()
        if self._pending_sequences + self._pending_aliases > 0:
            self._logger.info("Committed {} sequences ({} residues) and {} aliases".format(
                self._pending_sequences, self._pending_sequences_len, self._pending_aliases))
        self._pending_sequences = 0
        self._pending_sequences_len = 0
        self._pending_aliases = 0

    def __del__(self):
        self.commit()
