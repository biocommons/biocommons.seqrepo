-- Every digest of each (seqtype, enst_id) that has >1 digest, with release range.
-- Input to compare.py.

COPY (
  WITH multi AS (SELECT seqtype, enst_id FROM enst GROUP BY ALL HAVING count(DISTINCT digest) > 1)
  SELECT seqtype, enst_id, digest, min(release) AS rmin, max(release) AS rmax, count(*) AS nrel
  FROM enst JOIN multi USING (seqtype, enst_id)
  GROUP BY ALL ORDER BY seqtype, enst_id, rmin
) TO 'changed-digests.tsv' (DELIMITER '\t', HEADER);
