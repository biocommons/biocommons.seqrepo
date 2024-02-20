# seqrepo loading Makefile
# 

SEQREPO_RELEASE_DIR=/biocommons/dl.biocommons.org/seqrepo
SEQREPO_ROOT=${SEQREPO_RELEASE_DIR}
BUILD_DIR=/biocommons/tmp/seqrepo

RELEASES=$(subst ${SEQREPO_RELEASE_DIR}/,,$(wildcard ${SEQREPO_RELEASE_DIR}/????-??-??))
LATEST_INSTANCE=$(lastword $(sort ${RELEASES}))
BUILD_INSTANCE=${LATEST_INSTANCE}+


builddir: ${BUILD_DIR}/${BUILD_INSTANCE}
loadlog: ${BUILD_DIR}/${BUILD_INSTANCE}.loadlog

${BUILD_DIR}/${BUILD_INSTANCE}: ${SEQREPO_RELEASE_DIR}/${LATEST_INSTANCE}
	mkdir $@/sequences -p 
	cd $<; \
	cp -av aliases.sqlite3 $@/; \
	chmod u+w $@/aliases.sqlite3; \
	cd sequences; \
	cp -av db.sqlite3 $@/sequences/; \
	chmod u+w $@/sequences/db.sqlite3; \
	for d in 2???; do cp -alv $$d $@/sequences/; done

%.loadlog: %
	seqrepo -r ${BUILD_DIR} load -i ${BUILD_INSTANCE} -n NCBI \
    	/biocommons/mirrors-ncbi/latest/refseq/H_sapiens/mRNA_Prot/human.*f[na]a.gz \
    	/biocommons/mirrors-ncbi/latest/refseq/H_sapiens/RefSeqGene/refseqgene.*f[na]a.gz \
    	/biocommons/mirrors-ncbi/latest/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/*/GCF_*_genomic.f[na]a.gz \
	| tee $@

