.DELETE_ON_ERROR:
.SUFFIXES:
.PHONY: default dl vrsids uniqueness classify clean cleanest

SHELL:=zsh -eu -o pipefail -o null_glob

# FASTA ids are unversioned before release 83
RELEASES:=$(shell seq 83 116)
SEQTYPES:=cdna cds

DLs:=$(foreach r, ${RELEASES}, $(foreach c, ${SEQTYPES}, ftp.ensembl.org/pub/release-$r/fasta/homo_sapiens/$(c)/Homo_sapiens.GRCh38.$(c).all.fa.gz))
VRSIDs:=$(DLs:.fa.gz=.fa.gz.vrsids)

default: enst.duckdb
dl: ${DLs}
vrsids: ${VRSIDs}

# download sequences
ftp.ensembl.org/pub/release-%.fa.gz:
	wget -mq "https://$@"

# compute VRS IDs
%.fa.gz.vrsids: %.fa.gz
	fasta-sequence-digest <$< | sort -u >$@

# one table of (release, seqtype, enst_id, digest), digest truncated to 15 chars
enst.duckdb: sql/load.sql ${VRSIDs}
	rm -f $@
	duckdb $@ <$<

uniqueness: enst.duckdb
	duckdb -readonly $< <sql/uniqueness.sql

# every digest of each (seqtype, enst_id) that has >1 digest, with release range
changed-digests.tsv: sql/changed-digests.sql enst.duckdb
	duckdb -readonly enst.duckdb <$<

# before/after sequence comparison for each changed id
changed-pairs.tsv: changed-digests.tsv compare.py
	python3 -I compare.py $< ftp.ensembl.org >$@

classify: changed-pairs.tsv
	duckdb <sql/classify.sql

clean:
	/bin/rm -fv enst.duckdb changed-*.tsv
cleanest: clean
	/bin/rm -fv ftp.ensembl.org/**/*.vrsids
