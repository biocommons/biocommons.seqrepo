from importlib import reload

import pytest

from biocommons.seqrepo import config


def test_SEQREPO_FD_CACHE_MAXSIZE_default(monkeypatch):
    monkeypatch.delenv("SEQREPO_FD_CACHE_MAXSIZE", raising=False)
    reload(config)
    assert config.SEQREPO_FD_CACHE_MAXSIZE == -1


def test_SEQREPO_LRU_CACHE_MAXSIZE_default(monkeypatch):
    monkeypatch.delenv("SEQREPO_LRU_CACHE_MAXSIZE", raising=False)
    reload(config)
    assert config.SEQREPO_LRU_CACHE_MAXSIZE == 1000000


def test_SEQREPO_LRU_CACHE_MAXSIZE_int(monkeypatch):
    monkeypatch.setenv("SEQREPO_LRU_CACHE_MAXSIZE", "42")
    reload(config)
    assert config.SEQREPO_LRU_CACHE_MAXSIZE == 42


def test_SEQREPO_LRU_CACHE_MAXSIZE_none(monkeypatch):
    monkeypatch.setenv("SEQREPO_LRU_CACHE_MAXSIZE", "nOne")
    reload(config)
    assert config.SEQREPO_LRU_CACHE_MAXSIZE is None


def test_SEQREPO_LRU_CACHE_MAXSIZE_invalid(monkeypatch):
    monkeypatch.setenv("SEQREPO_LRU_CACHE_MAXSIZE", "invalid")
    with pytest.raises(ValueError):
        reload(config)
