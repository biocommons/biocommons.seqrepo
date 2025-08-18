"""Provide abstract interfaces for FASTA reader/writer classes."""

import abc


class BaseReader(metaclass=abc.ABCMeta):
    """Abstract FASTA reader interface."""

    @abc.abstractmethod
    def fetch(self, seq_id: str, start: int | None = None, end: int | None = None) -> str:
        """Get sequence slice."""
        raise NotImplementedError

    def __getitem__(self, ac: str) -> str:
        return self.fetch(ac)


class BaseWriter(metaclass=abc.ABCMeta):
    """Abstract FASTA dir writer instance."""

    @abc.abstractmethod
    def store(self, seq_id: str, seq: str) -> str:
        """Store a sequence and its ID."""
