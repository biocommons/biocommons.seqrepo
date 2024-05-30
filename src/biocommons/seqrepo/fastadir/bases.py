import abc
from typing import Optional

import six


@six.add_metaclass(abc.ABCMeta)
class BaseReader:
    @abc.abstractmethod
    def fetch(self, seq_id: str, start: Optional[int] = None, end: Optional[int] = None) -> str:
        raise NotImplementedError

    def __getitem__(self, ac: str) -> str:
        return self.fetch(ac)


@six.add_metaclass(abc.ABCMeta)
class BaseWriter:
    @abc.abstractmethod
    def store(self, seq_id: str, seq: str) -> str:
        pass  # pragma: no cover
