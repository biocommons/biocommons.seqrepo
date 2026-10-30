-- Are versioned ENST ids unique to a sequence?  Run against enst.duckdb.

-- ids with >1 digest within a single release and seqtype (expect 0)
SELECT count(*) AS within_release_multi FROM (
  SELECT release, seqtype, enst_id FROM enst GROUP BY ALL HAVING count(DISTINCT digest) > 1);

-- ids with >1 digest across releases
SELECT seqtype, count(*) AS ids, count(*) FILTER (WHERE nd > 1) AS ids_multi_digest, max(nd) AS max_nd
FROM (SELECT seqtype, enst_id, count(DISTINCT digest) AS nd FROM enst GROUP BY ALL)
GROUP BY ALL ORDER BY ALL;

-- release in which a new digest first appears for an already-seen id
WITH first_seen AS (SELECT seqtype, enst_id, digest, min(release) AS r FROM enst GROUP BY ALL),
id_first AS (SELECT seqtype, enst_id, min(r) AS r0 FROM first_seen GROUP BY ALL)
SELECT f.r AS release,
       count(*) FILTER (WHERE f.seqtype = 'cdna') AS cdna,
       count(*) FILTER (WHERE f.seqtype = 'cds') AS cds
FROM first_seen f JOIN id_first i USING (seqtype, enst_id)
WHERE f.r > i.r0
GROUP BY ALL ORDER BY release;

-- ids whose digest switched more than once (reversions)
WITH runs AS (
  SELECT seqtype, enst_id, release, digest,
         lag(digest) OVER (PARTITION BY seqtype, enst_id ORDER BY release) AS prev
  FROM enst),
multi AS (SELECT seqtype, enst_id FROM runs GROUP BY ALL HAVING count(*) FILTER (WHERE digest <> prev) > 1)
SELECT seqtype, enst_id, digest, min(release) AS rmin, max(release) AS rmax, count(*) AS nrel
FROM enst JOIN multi USING (seqtype, enst_id) GROUP BY ALL ORDER BY seqtype, enst_id, rmin;

-- ids absent from an intermediate release
SELECT seqtype, count(*) AS ids_with_gaps FROM (
  SELECT seqtype, enst_id FROM enst GROUP BY ALL HAVING max(release) - min(release) + 1 <> count(*))
GROUP BY ALL ORDER BY ALL;

-- for ids whose cds changed, did the cdna also change?
WITH chg AS (SELECT enst_id FROM enst WHERE seqtype = 'cds' GROUP BY ALL HAVING count(DISTINCT digest) > 1),
cd AS (SELECT enst_id, count(DISTINCT digest) AS nd FROM enst WHERE seqtype = 'cdna' GROUP BY ALL)
SELECT count(*) AS cds_changed, count(cd.enst_id) AS has_cdna, count(*) FILTER (WHERE nd = 1) AS cdna_constant
FROM chg LEFT JOIN cd USING (enst_id);
