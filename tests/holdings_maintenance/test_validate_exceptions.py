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
from pdsfile.holdings_maintenance.pds4 import pds4checksums, pds4infoshelf

pytestmark = pytest.mark.holdings_free


class _StubPdsdir:
    """Just enough of a PdsFile for validate_infodict: a root and an abspath."""

    root_ = '/'
    abspath = '/nonexistent-holdings/volumes/VS_0xxx/VOL_0001'


class _StubShelfPdsdir:
    """Just enough of a PdsFile for write_infodict: a root and a shelf path."""

    root_ = '/'
    abspath = '/nonexistent-holdings/volumes/VS_0xxx/VOL_0001'

    def __init__(self, shelf_path):
        self._shelf_path = shelf_path

    def shelf_path_and_lskip(self, _id):
        """Return the shelf path and the characters to trim from an absolute path."""

        return (self._shelf_path, len(self.abspath) + 1)


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


##########################################################################################
# What a module's own default limits reach
#
# Four functions built a merged limits dictionary from the module's defaults and the
# caller's argument and then opened the log level with the caller's argument alone, so
# the module's defaults reached nothing. All four constants are empty today, which is
# why the defect was latent and why these tests set one.
#
# validate_pairs can be pinned by what it logs. write_infodict's second scope writes the
# sidecar and emits no line of its own, so there is nothing a limit could suppress
# there; what is pinned instead is the value the scope is opened with, which is the
# whole of what the fix changes.
##########################################################################################

@pytest.mark.parametrize('module', [pytest.param(pdschecksums, id='pdschecksums'),
                                    pytest.param(pds4checksums, id='pds4checksums')])
def test_validate_pairs_applies_the_modules_own_limits(module, tmp_path, monkeypatch):
    """A limit in this module's defaults caps the comparison's error lines."""

    monkeypatch.setattr(module, 'VALIDATE_PAIRS_LIMITS', {'error': 1})
    logger = _logger(tmp_path)

    walked = [('/a/ONE.TXT', 'd' * 32), ('/a/TWO.TXT', 'd' * 32)]
    module.validate_pairs(walked, [], logger=logger)

    text = (tmp_path / 'run.log').read_text()
    assert text.count('Missing checksum') == 1, text
    assert 'suppressed' in text, text


@pytest.mark.parametrize('module', [pytest.param(pdsinfoshelf, id='pdsinfoshelf'),
                                    pytest.param(pds4infoshelf, id='pds4infoshelf')])
def test_write_infodict_opens_both_scopes_with_the_merged_limits(module, tmp_path,
                                                                 monkeypatch):
    """Both of the call's two scopes take this module's defaults, not just the first."""

    monkeypatch.setattr(module, 'WRITE_INFODICT_LIMITS', {'info': 7})
    opened = []
    real_open = pdslogger.PdsLogger.open

    def recording_open(self, title, *args, **kwargs):
        opened.append((title, kwargs.get('limits')))
        return real_open(self, title, *args, **kwargs)

    monkeypatch.setattr(pdslogger.PdsLogger, 'open', recording_open)

    shelf_path = tmp_path / 'VOL_0001_info.pickle'
    pdsdir = _StubShelfPdsdir(str(shelf_path))
    entry = (10, 0, '2026-01-02 03:04:05.000000', 'd' * 32, (0, 0))

    module.write_infodict(pdsdir, {pdsdir.abspath + '/ONE.TXT': entry},
                          logger=_logger(tmp_path))

    titles = [title for (title, _limits) in opened]
    assert titles == ['Writing info file info for', 'Writing Python dictionary'], titles
    assert [limits for (_title, limits) in opened] == [{'info': 7}, {'info': 7}], opened

    # The sidecar really was written, so the scope pinned above is the one that ran.
    assert (tmp_path / 'VOL_0001_info.py').exists()


##########################################################################################
# What generate_checksums returns when a selection matches nothing, or too much
#
# Both of those paths return early, and the PDS3 tool returned an empty dict where every
# other return of the same function is a list of pairs. Every caller tests the value for
# truth alone, so nothing broke; a caller that iterated it would have got keys.
##########################################################################################

@pytest.mark.parametrize('module', [pytest.param(pdschecksums, id='pdschecksums'),
                                    pytest.param(pds4checksums, id='pds4checksums')])
@pytest.mark.parametrize('selection', ['NOSUCH.TXT', 'TWICE.TXT'],
                         ids=['unmatched', 'multiple'])
def test_generate_checksums_returns_a_list_for_a_selection_it_cannot_use(module,
                                                                         selection,
                                                                         tmp_path):
    """Both early returns are a list of pairs, which is what every other return is."""

    (tmp_path / 'DATA').mkdir()
    (tmp_path / 'TWICE.TXT').write_bytes(b'one\n')
    (tmp_path / 'DATA' / 'TWICE.TXT').write_bytes(b'the other\n')

    pdsdir = _StubShelfPdsdir(str(tmp_path / 'unused'))
    pdsdir.abspath = str(tmp_path)

    (pairs, _mtime) = module.generate_checksums(pdsdir, selection,
                                                logger=_logger(tmp_path))

    assert pairs == [], pairs
    assert isinstance(pairs, list), type(pairs)
