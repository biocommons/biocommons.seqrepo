-- fix case on namespaces
-- issue #16
-- 
-- $ sqlite3 master/aliases.sqlite3
-- sqlite> .read /home/reece/projects/biocommons/biocommons.seqrepo/sql/recase.sql



-- GRCh...: no change required

-- ensembl-00: capitalize E
update seqalias set namespace = 'E' || substr(namespace, 2) where namespace like 'ensembl-%';

-- gi: as-is, since most people write as lowercase (and it's dead anyway)

-- uppercase md5, ncbi, seguid, sha1, sha512
update seqalias set namespace = upper(namespace) where namespace in ('md5', 'ncbi', 'seguid', 'sha1', 'sha512');

vacuum;
