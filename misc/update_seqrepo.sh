#!/bin/bash

SEQREPO_RELEASE_DIR=/biocommons/dl.biocommons.org/seqrepo
SEQREPO_ROOT=/usr/local/share/seqrepo

mkdir -p $SEQREPO_ROOT
rm -rf $SEQREPO_ROOT/master


# Copy the latest release to work on
LATEST_RELEASE=$(ls -d $SEQREPO_RELEASE_DIR/????-??-?? | tail -n 1)

cp -a $LATEST_RELEASE $SEQREPO_ROOT/master


# Add write permission to folders and databases
chmod u+w $SEQREPO_ROOT/master $SEQREPO_ROOT/master/sequences \
          $SEQREPO_ROOT/master/aliases.sqlite3 $SEQREPO_ROOT/master/sequences/db.sqlite3

chmod u+w $(ls -d $SEQREPO_ROOT/master/sequences/*/ | tail -n 1)


# Load sequences
seqrepo -r $SEQREPO_ROOT load -n NCBI \
    /biocommons/mirrors-ncbi/latest/refseq/H_sapiens/mRNA_Prot/human.*f[na]a.gz \
    /biocommons/mirrors-ncbi/latest/refseq/H_sapiens/RefSeqGene/refseqgene.*f[na]a.gz \
    /biocommons/mirrors-ncbi/latest/genomes/refseq/vertebrate_mammalian/Homo_sapiens/all_assembly_versions/*/GCF_*_genomic.f[na]a.gz

if [ $? -ne 0 ]; then
    echo "Error: seqrepo load failed"
    exit 1
fi


# Make a snapshot
seqrepo -r $SEQREPO_ROOT -v snapshot

if [ $? -ne 0 ]; then
    echo "Error: seqrepo snapshot failed"
    exit 2
fi


# Push snapshot to download area
NEW_RELEASE=$(ls -d $SEQREPO_ROOT/????-??-?? | tail -n 1 | rev | cut -f1 -d'/' | rev)

rsync -aP --link-dest=$LATEST_RELEASE/ $SEQREPO_ROOT/$NEW_RELEASE/ $SEQREPO_RELEASE_DIR/$NEW_RELEASE/

