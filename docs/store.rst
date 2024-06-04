Storing New Sequences and Aliases
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

SeqRepo can store user-provided sequences and sequence aliases alongside biocommons-provided data snapshots.

.. this should be a "note" admonition if we ever get around to making RTD-hosted docs

Storing new sequences and aliases requires that the SeqRepo data directory files, as well as associated sqlite database files, are writeable by the user.

* In UNIX environments, use commands like ``ls -al`` to check file and directory permissions, and ``chown`` and ``chmod`` to change file/directory ownership and permissions, respectively (see e.g. `here <https://www.redhat.com/sysadmin/linux-file-permissions-explained>`_ for more information). In recent SeqRepo releases, files downloaded by the ``pull`` command should inherit permissions from their parent directory, so if a SeqRepo database needs to be writeable, it's often easiest to download it to a location within user space.

* For a sqlite database to be writeable, **both the database file and its parent directory must be writeable by the user.** Additionally, no other process may currently be using the sqlite database file. Ensure that this is the case for both ``$SEQREPO_ROOT_DIR/aliases.sqlite3`` and ``$SEQREPO_ROOT_DIR/sequences/db.sqlite3``.

To add a new sequence and/or aliases in a Python environment, construct a ``SeqRepo`` instance with the ``writeable`` parameter set to ``True``, and pass the sequence and a list of namespaced aliases (i.e. a ``dict`` with ``namespace`` and ``alias`` keys) to the ``store()`` method.

.. code-block:: python

   from biocommons.seqrepo import SeqRepo

   sr = SeqRepo("/usr/local/share/seqrepo/latest", writeable=True)

   sequence = "AAAAGGGGGCCCCCCTTTTT"
   nsaliases = [{"namespace": "en", "alias": "rose"}]
   n_seqs_added, n_aliases_added = sr.store(sequence, nsaliases)
   print(n_seqs_added, n_aliases_added)
   # (1, 1)
   sr.commit()

``store()`` returns a tuple containing the number of new sequences and aliases that were successfully added (the sha512t24u sequence hash is not counted as a new alias, because it is automatically added with a new sequence as the main sequence identifier).

Note that the ``commit()`` method MUST be called before the end of an interpreter session for data to be durably committed to the database. ``store()`` only stages pending database additions, but only makes calls to ``commit()`` when the number of staged changes exceeds a (relatively large) threshold, for performance reasons.

.. and this should be a "tip" admonition or something of that nature

Load FASTA files
@@@@@@@@@@@@@@@@

The command line interface can also load sequences directly from FASTA files with the ``seqrepo load`` command. See ``docs/loading-notes.rst`` for an example.
