##########################################################################################
# tests/core/test_shelves_only_fallbacks.py
#
# What os_path_exists and os_path_isdir answer under SHELVES_ONLY for a tree whose info
# shelves have not been written.
#
# Both functions ask the info shelf first. For a path that is itself a covered directory
# the key is empty, and every shelf file carries an entry under the empty key, so the
# existence of the shelf file is the whole answer and the file need not be opened. That
# shortcut used to return its result: a bundle whose shelf had never been written came
# back as absent and as not-a-directory, and the fallbacks below it -- the info shelf
# tree, the checksum path, and finally the filesystem -- were never reached. Its
# consequence reached all the way out to from_path(): the preload records only the names
# it can see as directories, so no bundle of such a tree entered the $VOLS and $RANKS
# tables, and a bare bundle name resolved through them raised KeyError or, on the
# recovery path, UnboundLocalError.
#
# The PDS4 half of the reference holdings root is exactly that tree -- it carries no
# _infoshelf-bundles at all -- which is why five pds4 blackbox tests failed under
# --mode s and none under --mode ns.
#
# The tests build a holdings-shaped tree of their own and need no holdings root. Each
# sets SHELVES_ONLY through monkeypatch, so the class attribute is restored afterwards
# and no later test in the session inherits the setting.
##########################################################################################

import pytest

from pdsfile import Pds3File, Pds4File

pytestmark = pytest.mark.holdings_free

# Each flavor, with the holdings directory name it uses and a category and unit set of
# its own vocabulary.
FLAVORS = [
    pytest.param(Pds3File, 'holdings', 'volumes', 'COUVIS_0xxx', 'COUVIS_0001',
                 id='pds3'),
    pytest.param(Pds4File, 'pds4-holdings', 'bundles', 'uranus_occs_earthbased',
                 'uranus_occ_u0_kao_91cm', id='pds4'),
]


@pytest.fixture
def unshelved_tree(tmp_path):
    """Return a builder for a holdings-shaped tree with no shelves beside it."""

    def build(holdings_name, category, unit_set, unit):
        unit_dir = tmp_path / holdings_name / category / unit_set / unit
        unit_dir.mkdir(parents=True)
        (unit_dir / 'AAREADME.TXT').write_bytes(b'a real file\r\n')

        return unit_dir

    return build


@pytest.mark.parametrize(('cls', 'holdings_name', 'category', 'unit_set', 'unit'),
                         FLAVORS)
def test_a_unit_with_no_shelf_still_exists_and_is_a_directory(cls, holdings_name,
                                                              category, unit_set, unit,
                                                              unshelved_tree,
                                                              monkeypatch):
    """A directory the filesystem has is not made to vanish by a missing shelf."""

    unit_dir = unshelved_tree(holdings_name, category, unit_set, unit)
    monkeypatch.setattr(cls, 'SHELVES_ONLY', True)

    assert cls.os_path_exists(str(unit_dir))
    assert cls.os_path_isdir(str(unit_dir))


@pytest.mark.parametrize(('cls', 'holdings_name', 'category', 'unit_set', 'unit'),
                         FLAVORS)
def test_the_fallback_still_answers_no_for_what_is_not_there(cls, holdings_name,
                                                             category, unit_set, unit,
                                                             unshelved_tree,
                                                             monkeypatch):
    """Falling through to the filesystem is not the same as answering yes.

    The fix replaces one hard False with a fall-through, so the case that has to be
    checked beside it is the one where the fall-through must still say no.
    """

    unit_dir = unshelved_tree(holdings_name, category, unit_set, unit)
    monkeypatch.setattr(cls, 'SHELVES_ONLY', True)

    assert not cls.os_path_exists(str(unit_dir.parent / 'no_such_unit'))
    assert not cls.os_path_isdir(str(unit_dir / 'AAREADME.TXT'))
    assert cls.os_path_exists(str(unit_dir / 'AAREADME.TXT'))
