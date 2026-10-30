-- Classify before/after sequence changes in changed-pairs.tsv (from compare.py).
-- "5' end": only the first few bases (start codon) and the whole 3' end are shared.

CREATE TEMP TABLE p AS
SELECT *,
  CASE WHEN prefix <= 6 AND suffix >= least(old_len, new_len) - 6 THEN '5'' end'
       WHEN prefix >= least(old_len, new_len) - 6 AND suffix <= 6 THEN '3'' end'
       WHEN prefix <= 6 AND suffix <= 6 THEN 'both ends'
       ELSE 'internal' END AS kind
FROM read_csv('changed-pairs.tsv', delim='\t', header=true);

SELECT seqtype, kind, count(*) AS n,
  count(*) FILTER (WHERE delta % 3 = 0) AS frame_ok,
  count(*) FILTER (WHERE delta < 0) AS shorter,
  count(*) FILTER (WHERE delta > 0) AS longer,
  count(*) FILTER (WHERE starts_with(new_mid, 'N') OR starts_with(old_mid, 'N')) AS n_start,
  median(abs(delta)) AS med_absdelta
FROM p GROUP BY ALL ORDER BY seqtype, n DESC;
