##########################################################################################
# tests/holdings_maintenance/test_validate_exceptions.py
#
# What the two PDS3 comparison functions do with an exception raised inside them.
#
# pdschecksums.validate_pairs() and pdsinfoshelf.validate_infodict() used to end
# `finally: return ...`, and a return in a finally discards whatever the except clause
# re-raised. validate_pairs then handed back the flag as it stood -- True for a failure
# part way through a comparison that had so far agreed -- and validate_infodict handed
# back the log level's counts as a result. A KeyboardInterrupt went the same way. Both
# PDS4 twins already returned after the finally; these two now do too.
#
# Nothing in a real run reaches these branches, which is why each raise has to be
# arranged rather than provoked: the bodies only iterate and compare. Both halves are
# asserted, because the except clause is the only thing that logs and the finally is the
# only thing that used to discard, so a test that checked one would pass against half
# the function.
#
# The tests build their own inputs and need no holdings tree.
##########################################################################################

import pdslogger
import pytest

from pdsfile.holdings_maintenance.pds3 import pdschecksums, pdsinfoshelf

pytestmark = pytest.mark.holdings_free


class _StubPdsdir:
    """Just enough of a PdsFile for validate_infodict: a root and an abspath."""

    root_ = '/'
    abspath = '/nonexistent-holdings/volumes/VS_0xxx/VOL_0001'


class _ExplodingKeys(dict):
    """A shelf dictionary whose keys() raises, which is where the try block can fail."""

    def keys(self):
        raise RuntimeError('reading the shelved keys failed')


def _logger(tmp_path):
    """A logger of this test's own, writing to a file the assertions can read."""

    logger = pdslogger.PdsLogger('pds.test.' + tmp_path.name)
    logger.add_handler(pdslogger.file_handler(str(tmp_path / 'run.log')))

    return logger


def test_validate_pairs_logs_and_reraises_an_exception_raised_inside_it(tmp_path):
    """It logs and re-raises; it does not report a comparison it never finished."""

    def exploding_pairs():
        raise RuntimeError('reading the shelved pairs failed')
        yield  # pragma: no cover - unreachable, and needed to make this a generator

    logger = _logger(tmp_path)

    with pytest.raises(RuntimeError, match='reading the shelved pairs failed'):
        pdschecksums.validate_pairs([], exploding_pairs(), logger=logger)

    assert 'reading the shelved pairs failed' in (tmp_path / 'run.log').read_text()


def test_validate_infodict_logs_and_reraises_an_exception_raised_inside_it(tmp_path):
    """It logs and re-raises; it does not return the log level's counts as a result."""

    logger = _logger(tmp_path)

    with pytest.raises(RuntimeError, match='reading the shelved keys failed'):
        pdsinfoshelf.validate_infodict(_StubPdsdir(), {}, _ExplodingKeys(), None,
                                       logger=logger)

    assert 'reading the shelved keys failed' in (tmp_path / 'run.log').read_text()
