##########################################################################################
# tests/core/conftest.py
#
# Fixtures shared by the core-module tests.
##########################################################################################

import pytest

from pdsfile import Pds3File
from tests.core.support import RecordingDictionaryCache


@pytest.fixture
def pds3_cache(monkeypatch):
    """Give Pds3File a throwaway cache for the duration of one test.

    Every test that builds a PdsFile takes this fixture, so a cache write-back
    triggered by the code under test lands here and can never reach the session's
    preloaded cache. CACHE is defined directly on Pds3File and monkeypatch restores
    class attributes from the class __dict__, so the real cache is put back exactly
    as it was.
    """

    # A non-zero default lifetime, as the real caches are built with: a
    # DictionaryCache constructed with lifetime=0 cannot serve set() without an
    # explicit lifetime.
    throwaway = RecordingDictionaryCache(lifetime=86400, limit=100)
    monkeypatch.setattr(Pds3File, 'CACHE', throwaway)
    return throwaway

##########################################################################################
