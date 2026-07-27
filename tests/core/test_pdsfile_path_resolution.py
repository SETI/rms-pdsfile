##########################################################################################
# tests/core/test_pdsfile_path_resolution.py
#
# Tests for two path-resolution behaviors of pdsfile.pdsfile:
#
#   * abspath_for_logical_path() resolves each class against its own holdings
#     environment variable;
#   * infoshelf_path_and_key turns a failed shelf-path lookup into a pair of empty
#     strings, but lets an interrupt through.
#
# The tests build their own inputs and need no holdings tree. The environment
# variables they set are pointed at tmp_path and restored by monkeypatch; no test
# reads either real holdings root.
##########################################################################################

import pytest

from pdsfile import Pds3File, Pds4File
from pdsfile import pdsfile as pdsfile_module
from pdsfile.pdsfile import PdsFile, abspath_for_logical_path
from tests.core.support import blank_pds3file

pytestmark = pytest.mark.holdings_free


##########################################################################################
# abspath_for_logical_path
##########################################################################################
class TestHoldingsEnvironmentVariable:

    def test_each_class_names_its_own_holdings_variable(self):
        named = {cls.__name__: cls._HOLDINGS_ENV
                 for cls in (PdsFile, Pds3File, Pds4File)}

        assert named == {'PdsFile': 'PDS3_HOLDINGS_DIR',
                         'Pds3File': 'PDS3_HOLDINGS_DIR',
                         'Pds4File': 'PDS4_HOLDINGS_DIR'}

    @pytest.mark.parametrize(
        ('cls', 'env_var', 'logical_path'),
        [
            (Pds3File, 'PDS3_HOLDINGS_DIR', 'volumes/COISS_2xxx/COISS_2001'),
            (Pds4File, 'PDS4_HOLDINGS_DIR', 'bundles/cassini_iss'),
        ]
    )
    def test_the_environment_variable_supplies_the_holdings_root(
            self, cls, env_var, logical_path, monkeypatch, tmp_path):
        # Two distinct roots, so a class that reads the wrong variable produces a
        # visibly wrong answer rather than an accidentally right one.
        roots = {'PDS3_HOLDINGS_DIR': str(tmp_path / 'pds3' / 'holdings'),
                 'PDS4_HOLDINGS_DIR': str(tmp_path / 'pds4' / 'pds4-holdings')}
        for name, root in roots.items():
            monkeypatch.setenv(name, root)

        # No preload and no cached list, so the environment variable is the branch
        # that answers.
        monkeypatch.setattr(cls, 'LOCAL_PRELOADED', [])
        monkeypatch.setattr(cls, 'LOCAL_HOLDINGS_DIRS', None)

        abspath = abspath_for_logical_path(logical_path, cls)

        assert abspath == roots[env_var] + '/' + logical_path
        # The resolved root is remembered on the class.
        assert list(cls.LOCAL_HOLDINGS_DIRS) == [roots[env_var]]

    def test_a_preloaded_root_still_wins_over_the_environment(
            self, monkeypatch, tmp_path):
        preloaded = str(tmp_path / 'preloaded' / 'holdings')
        monkeypatch.setenv('PDS3_HOLDINGS_DIR', str(tmp_path / 'from-env' / 'holdings'))
        monkeypatch.setattr(Pds3File, 'LOCAL_PRELOADED', [preloaded])
        monkeypatch.setattr(Pds3File, 'LOCAL_HOLDINGS_DIRS', None)

        abspath = abspath_for_logical_path('volumes/COISS_2xxx', Pds3File)

        assert abspath == preloaded + '/volumes/COISS_2xxx'

    def test_a_class_does_not_borrow_another_class_holdings_root(
            self, monkeypatch, tmp_path):
        # With only the PDS3 root exported, a PDS4 logical path has nowhere to
        # resolve to and says so, rather than quietly answering with the PDS3
        # tree.
        monkeypatch.setenv('PDS3_HOLDINGS_DIR', str(tmp_path / 'pds3' / 'holdings'))
        monkeypatch.delenv('PDS4_HOLDINGS_DIR', raising=False)
        monkeypatch.setattr(Pds4File, 'LOCAL_PRELOADED', [])
        monkeypatch.setattr(Pds4File, 'LOCAL_HOLDINGS_DIRS', None)
        # The last-resort branch globs a MacOS website install; stub it so the
        # test does not depend on what the host happens to have.
        monkeypatch.setattr(pdsfile_module.glob, 'glob', lambda pattern: [])

        with pytest.raises(ValueError, match='No holdings directory'):
            abspath_for_logical_path('bundles/cassini_iss', Pds4File)

    def test_a_path_that_does_not_start_at_a_category_is_rejected(self):
        with pytest.raises(ValueError, match='Not a logical path'):
            abspath_for_logical_path('COISS_2xxx/COISS_2001', Pds3File)


##########################################################################################
# infoshelf_path_and_key
##########################################################################################
def _raise(exception):
    """Return a classmethod that raises, standing in for a shelf-path lookup."""

    def failing(cls, abspath, shelf_type='info'):
        raise exception

    return classmethod(failing)


class TestInfoshelfPathAndKey:

    def test_a_shelf_path_that_cannot_be_built_becomes_a_pair_of_empty_strings(
            self, monkeypatch, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0001')
        monkeypatch.setattr(Pds3File, 'shelf_path_and_key_for_abspath',
                            _raise(ValueError('No shelf files for checksums')))

        assert pdsf.infoshelf_path_and_key == ('', '')

    def test_an_unexpected_error_is_still_absorbed(self, monkeypatch, pds3_cache):
        # Every Exception is absorbed, not just the ones the lookup is known to
        # raise.
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0002')
        monkeypatch.setattr(Pds3File, 'shelf_path_and_key_for_abspath',
                            _raise(AttributeError('abspath is None')))

        assert pdsf.infoshelf_path_and_key == ('', '')

    @pytest.mark.parametrize('exception', [KeyboardInterrupt(), SystemExit(1)])
    def test_an_interrupt_is_not_absorbed(self, exception, monkeypatch, pds3_cache):
        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0003')
        monkeypatch.setattr(Pds3File, 'shelf_path_and_key_for_abspath',
                            _raise(exception))

        with pytest.raises(type(exception)) as raised:
            _ = pdsf.infoshelf_path_and_key

        # The interrupt propagates untouched, not a lookalike raised on its way
        # out of the handler.
        assert raised.value is exception

    def test_a_successful_lookup_is_cached_in_the_object(self, monkeypatch, pds3_cache):
        calls = []

        def succeeding(cls, abspath, shelf_type='info'):
            calls.append((abspath, shelf_type))
            return ('/shelf/path.pickle', 'DATA/FILE.IMG')

        pdsf = blank_pds3file('volumes/NOSUCH_0xxx/NOSUCH_0004/DATA/FILE.IMG')
        monkeypatch.setattr(Pds3File, 'shelf_path_and_key_for_abspath',
                            classmethod(succeeding))

        assert pdsf.infoshelf_path_and_key == ('/shelf/path.pickle', 'DATA/FILE.IMG')
        assert pdsf.infoshelf_path_and_key == ('/shelf/path.pickle', 'DATA/FILE.IMG')
        assert calls == [(pdsf.abspath, 'info')]

##########################################################################################
