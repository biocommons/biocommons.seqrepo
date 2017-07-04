import os
import re


def commonpath(paths):
    """py2 compatible version of py3's os.path.commonpath

    >>> commonpath([""])
    ''
    >>> commonpath(["/"])
    '/'
    >>> commonpath(["/a"])
    '/a'
    >>> commonpath(["/a//"])
    '/a'
    >>> commonpath(["/a", "/a"])
    '/a'
    >>> commonpath(["/a/b", "/a"])
    '/a'
    >>> commonpath(["/a/b", "/a/b"])
    '/a/b'
    >>> commonpath(["/a/b/c", "/a/b/d"])
    '/a/b'
    >>> commonpath(["/a/b/c", "/a/b/d", "//a//b//e//"])
    '/a/b'

    """
    assert os.sep == "/", "tested only on slash-delimited paths"
    split_re = re.compile(os.sep + "+")

    if len(paths) == 0:
        raise ValueError("commonpath() arg is an empty sequence")

    spaths = [p.rstrip(os.sep) for p in paths]
    splitpaths = [split_re.split(p) for p in spaths]
    if all(p.startswith(os.sep) for p in paths):
        abs_paths = True
        splitpaths = [p[1:] for p in splitpaths]
    elif all(not p.startswith(os.sep) for p in paths):
        abs_paths = False
    else:
        raise ValueError("Can't mix absolute and relative paths")

    splitpaths0 = splitpaths[0]
    splitpaths1n = splitpaths[1:]
    min_length = min(len(p) for p in splitpaths)
    equal = [i for i in range(min_length) if all(splitpaths0[i] == sp[i] for sp in splitpaths1n)]
    max_equal = max(equal or [-1])
    commonelems = splitpaths0[:max_equal + 1]
    commonpath = os.sep.join(commonelems)
    return (os.sep if abs_paths else '') + commonpath


if __name__ == "__main__":

    def cmp1(pathlist):
        bi = os.path.commonpath(pathlist)
        c = commonpath(pathlist)
        print("{eq:5s} {bi:20s} {c:20s} {paths}".format(eq=str(bi == c), bi=bi, c=c, paths=", ".join(pathlist)))

    paths = ["/a/b/c", "/a/b/c//", "///a///b///c", "/a/b/d", "/a/b", "/a", "/"]
    paths = ["/a/b/c", "/a/b/c//", "///a///b///c", "/a/b/d", "/a/b", "/a", "/"]
    for i in range(0, len(paths)):
        cmp1(paths[:i + 1])

    paths2 = [p.lstrip("/") for p in paths]
    for i in range(1, len(paths2)):
        cmp1(paths2[:i])
