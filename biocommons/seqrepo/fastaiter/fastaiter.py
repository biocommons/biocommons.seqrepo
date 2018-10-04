def FastaIter(handle):
    """generator that returns (header, sequence) tuples from an open FASTA file handle

    Lines before the start of the first record are ignored.
    """

    header = None
    for line in handle:
        if line.startswith(">"):
            if header is not None:  # not the first record
                yield header, "".join(seq_lines)
            seq_lines = list()
            header = line[1:].rstrip()
        else:
            seq_lines.append(line.strip())

    yield header, "".join(seq_lines)
