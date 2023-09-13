# See https://github.com/biocommons/biocommons.seqrepo/issues/11
# Issue: seqrepo raises exceptions in (some) multithreaded environments

# Here's my understanding: sqlite support for multthreading (Python or
# otherwise) varies by version, platform, and compilation flags.  It
# is always safe to create separate readers after spawning threads.
# Alternatively, depending on sqlite library support, it *may* be
# possible to share an instances across threads by allocating before
# spawning threads.  Furthermore, some versions of sqlite issue
# warnings if the library is used in a threaded environment without
# check_same_thread=False, but that this check is advisory only (i.e.,
# it doesn't change library behavior).

# For Reece:
# sys.platform: linux2
# sys.version: 2.7.13 (default, Jan 19 2017, 14:48:08)  [GCC 6.3.0 20170118]
# sqlite3.sqlite_version: 3.16.2
# pid 9659 created SeqRepo(root_dir=/tmp/sr, writeable=False)
# (9660, 9659, 'SMELLASSWEET')
# pid 9659 created SeqRepo(root_dir=/tmp/sr, writeable=True)
# (9662, 9659, 'SMELLASSWEET')


import os
from multiprocessing import Process, Queue
import sqlite3
import sys

from biocommons.seqrepo import SeqRepo


def fetch_in_thread(sr, nsa):
    """fetch a sequence in a thread

    """

    def fetch_seq(q, nsa):
        pid, ppid = os.getpid(), os.getppid()
        q.put((pid, ppid, sr[nsa]))
    
    q = Queue()
    p = Process(target=fetch_seq, args=(q, nsa))
    p.start()
    pid, ppid, seq = q.get()
    p.join()

    assert pid != ppid, "sequence was not fetched from thread"
    return pid, ppid, seq
    

def make_seqrepo(writeable):    
    sr = SeqRepo("/tmp/sr", writeable=True)
    sr.store("SMELLASSWEET", [{"namespace": "en", "alias": "rose"}, {"namespace": "fr", "alias": "rose"}])

    if writeable is False:
        del sr
        sr = SeqRepo("/tmp/sr", writeable=writeable)

    print("pid {pid} created {sr}".format(pid=os.getpid(), sr=sr))
    return sr


if __name__ == "__main__":
    nsa = "en:rose"

    def _test(sr):
        r = fetch_in_thread(sr, nsa)
        print(r)

    print("sys.platform: " + sys.platform)
    print("sys.version: " + sys.version.replace("\n", " "))
    print("sqlite3.sqlite_version: " + sqlite3.sqlite_version)
    
    _test(make_seqrepo(writeable=False))
    _test(make_seqrepo(writeable=True))
