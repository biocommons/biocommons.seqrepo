SEQREPO_VERSION=0.6.5
SEQREPO_DATA_RELEASE=2021-01-29

docker-image: ${SEQREPO_DATA_RELEASE}.log

%.log:
	./build ${SEQREPO_VERSION} $* 2>&1 | tee $@.tmp
	mv $@.tmp $@