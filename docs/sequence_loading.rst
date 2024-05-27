Storing New Sequences and Aliases
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!


.. code-block:: python

   sequence = metadata.target_sequence

   # Add custom digest to SeqRepo for both Protein and DNA Sequence
   psequence_id = f"SQ.{sha512t24u(sequence.encode('ascii'))}"
   alias_dict_list = [{"namespace": "ga4gh", "alias": psequence_id}]
   sr.sr.store(sequence, nsaliases=alias_dict_list)

