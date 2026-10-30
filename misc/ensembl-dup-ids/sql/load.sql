-- One table of (release, seqtype, enst_id, digest), digest truncated to 15 chars.
-- release and seqtype are parsed from each .vrsids path.

CREATE TABLE enst AS
SELECT regexp_extract(filename, 'release-([0-9]+)/', 1)::USMALLINT AS release,
       regexp_extract(filename, '/(cds|cdna)/', 1) AS seqtype,
       enst_id,
       substr(vrsid, 10, 15) AS digest
FROM read_csv('ftp.ensembl.org/pub/release-*/fasta/homo_sapiens/*/*.fa.gz.vrsids',
              delim='\t', header=false, filename=true,
              columns={'vrsid': 'VARCHAR', 'enst_id': 'VARCHAR'})
ORDER BY release, seqtype, enst_id;
