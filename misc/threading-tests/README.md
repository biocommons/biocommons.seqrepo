# Threading Tests

This directory contains seqrepo tests for file descriptor exhaustion, especially in threading context
The idea: make it easy to test threading and cache size combinations.


See https://github.com/biocommons/biocommons.seqrepo/issues/112



## Examples

### single thread, without fd caching

```
snafu$ ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -m 1000 -n 1 
2023-09-13 15:25:56 snafu biocommons.seqrepo.fastadir.fastadir[2274974] INFO File descriptor caching disabled
2023-09-13 15:25:57 snafu root[2274974] INFO Queued 1000 accessions
2023-09-13 15:25:57 snafu root[2274974] INFO Starting run with 1 threads
2023-09-13 15:26:01 snafu root[2274974] INFO <Worker(Thread-1, started 139822207334080)>: Done; processed 1000 accessions
2023-09-13 15:26:01 snafu root[2274974] INFO Fetched 1000 sequences in 4.281685499 s with 1 threads; 234 seq/sec
```

### single thread, with fd caching

```
snafu$ ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -m 1000 -n 1 -f 100
2023-09-13 15:26:07 snafu biocommons.seqrepo.fastadir.fastadir[2275006] WARNING File descriptor caching enabled (size=100)
2023-09-13 15:26:08 snafu root[2275006] INFO Queued 1000 accessions
2023-09-13 15:26:08 snafu root[2275006] INFO Starting run with 1 threads
2023-09-13 15:26:08 snafu root[2275006] INFO <Worker(Thread-1, started 140250961671872)>: Done; processed 1000 accessions
2023-09-13 15:26:08 snafu root[2275006] INFO Fetched 1000 sequences in 0.41264548700000003 s with 1 threads; 2423 seq/sec
CacheInfo(hits=934, misses=66, maxsize=100, currsize=66)
```

### five threads, without caching

```
snafu$ ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -m 1000 -n 5
2023-09-13 15:26:16 snafu biocommons.seqrepo.fastadir.fastadir[2275039] INFO File descriptor caching disabled
2023-09-13 15:26:17 snafu root[2275039] INFO Queued 1000 accessions
2023-09-13 15:26:17 snafu root[2275039] INFO Starting run with 5 threads
2023-09-13 15:26:19 snafu root[2275039] INFO <Worker(Thread-5, started 139965979674304)>: Done; processed 197 accessions
2023-09-13 15:26:19 snafu root[2275039] INFO <Worker(Thread-3, started 139965996459712)>: Done; processed 200 accessions
2023-09-13 15:26:19 snafu root[2275039] INFO <Worker(Thread-4, started 139965988067008)>: Done; processed 210 accessions
2023-09-13 15:26:19 snafu root[2275039] INFO <Worker(Thread-2, started 139966004852416)>: Done; processed 198 accessions
2023-09-13 15:26:19 snafu root[2275039] INFO <Worker(Thread-1, started 139966088738496)>: Done; processed 195 accessions
2023-09-13 15:26:19 snafu root[2275039] INFO Fetched 1000 sequences in 5.946146807 s with 5 threads; 168 seq/sec
```

### five threads, with caching :-(

```
snafu$ ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -m 1000 -n 5 -f 10
2023-09-13 15:26:32 snafu biocommons.seqrepo.fastadir.fastadir[2275104] WARNING File descriptor caching enabled (size=10)
2023-09-13 15:26:33 snafu root[2275104] INFO Queued 1000 accessions
2023-09-13 15:26:33 snafu root[2275104] INFO Starting run with 5 threads
[E::bgzf_uncompress] Inflate operation failed: invalid distance too far back
[E::fai_retrieve] Failed to retrieve block. (Seeking in a compressed, .gzi unindexed, file?)
Exception in thread Thread-5:
Traceback (most recent call last):
  File "/usr/lib/python3.11/threading.py", line 1038, in _bootstrap_inner
    self.run()
```


### 1 thread, cache_size < # available fds

Same as above successful run, but Limit the process to 50 open file descriptors causes failure

```
snafu$ (ulimit -n 50; ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -m 1000 -n 1 -f 100)
2023-09-13 15:31:21 snafu biocommons.seqrepo.fastadir.fastadir[2275776] WARNING File descriptor caching enabled (size=100)
2023-09-13 15:31:21 snafu root[2275776] INFO Queued 1000 accessions
2023-09-13 15:31:21 snafu root[2275776] INFO Starting run with 1 threads
[E::fai_load3_core] Failed to open FASTA index /usr/local/share/seqrepo/2021-01-29/sequences/2020/0412/1420/1586701238.5306098.fa.bgz.gzi: Too many open files
Exception in thread Thread-1:
Traceback (most recent call last):
⋮
```


## Other useful commands

```
# dynamic (/2s) list of open files in seqrepo instance directory
watch lsof +D '/usr/local/share/seqrepo/'

# arbitrarily 
(ulimit -n 200; ./threading-test -s /usr/local/share/seqrepo/2021-01-29/ -a archive/accessions.gz -f 128)
```
