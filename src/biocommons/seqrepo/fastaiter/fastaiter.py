"""Provide handler for getting header-sequence pairs from FASTA files"""

from collections.abc import Iterator
from io import StringIO


def FastaIter(handle: StringIO) -> Iterator[tuple[str, str]]:  # noqa: N802
    """Create a generator that returns (header, sequence) tuples from an open FASTA file handle

    Lines before the start of the first record are ignored.
    """
    seq_lines = None
    header = None
    for line in handle:
        if line.startswith(">"):
            if header is not None and seq_lines is not None:  # not the first record
                yield header, "".join(seq_lines)
            seq_lines = []
            header = line[1:].rstrip()
        else:
            if header is not None and seq_lines is not None:  # not the first record
                seq_lines.append(line.strip())

    if header is not None and seq_lines is not None:
        yield header, "".join(seq_lines)
    else:  # no FASTA records in file
        return
