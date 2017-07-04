import abc

import six


@six.add_metaclass(abc.ABCMeta)
class BaseReader():
    @abc.abstractmethod
    def fetch(self, seq_id, start, end):
        pass    # pragma: no cover

    def __getitem__(self, ac):
        return self.fetch(ac)


@six.add_metaclass(abc.ABCMeta)
class BaseWriter():
    @abc.abstractmethod
    def store(self, seq_id, seq):
        pass    # pragma: no cover
