##########################################################################################
# tests/core/test_pdsviewable_iconset_for.py
#
# Tests for pdsfile.pdsviewable.iconset_for(). The function has no caller inside
# this repository (Viewmaster is the consumer), so these tests are its only coverage.
# The priority it ranks by is recorded on each loaded PdsViewSet by load_icons(),
# which reads it from REQUIRED_ICONS.
#
# The tests populate the icon dictionary the way load_icons() does, without any
# image files, and need no holdings tree.
##########################################################################################

import pytest

from pdsfile import pdsviewable

pytestmark = pytest.mark.holdings_free

# (icon type, priority) triples taken from REQUIRED_ICONS: UNKNOWN is the lowest
# priority and the fallback iconset_for() starts from; IMAGE outranks LABEL.
_PRIORITIES = (('UNKNOWN', 0), ('LABEL', 1), ('IMAGE', 33))


class _StubPdsFile:
    """The only attribute iconset_for() reads from its arguments."""

    def __init__(self, icon_type):
        self.icon_type = icon_type


@pytest.fixture
def icon_sets(monkeypatch):
    """Populate ICON_SET_BY_TYPE under the same keys load_icons() writes.

    The closed and open sets are distinct objects so a test can tell which one was
    returned.
    """

    sets = {}
    for icon_type, priority in _PRIORITIES:
        closed = pdsviewable.PdsViewSet(priority=priority)
        opened = pdsviewable.PdsViewSet(priority=priority)
        sets[icon_type] = closed
        sets[icon_type, False] = closed
        sets[icon_type, True] = opened

    monkeypatch.setattr(pdsviewable, 'ICON_SET_BY_TYPE', sets)
    return sets


class TestIconsetFor:

    @pytest.mark.parametrize(
        ('icon_types', 'expected'),
        [
            (['LABEL', 'IMAGE'], 'IMAGE'),
            (['IMAGE', 'LABEL'], 'IMAGE'),
            (['LABEL', 'UNKNOWN'], 'LABEL'),
            (['UNKNOWN', 'UNKNOWN'], 'UNKNOWN'),
        ]
    )
    def test_the_highest_priority_icon_type_wins(self, icon_sets, icon_types, expected):
        pdsfiles = [_StubPdsFile(icon_type) for icon_type in icon_types]

        assert pdsviewable.iconset_for(pdsfiles) is icon_sets[expected, False]

    def test_a_single_pdsfile_need_not_be_wrapped_in_a_list(self, icon_sets):
        assert (pdsviewable.iconset_for(_StubPdsFile('IMAGE')) is
                icon_sets['IMAGE', False])

    def test_an_empty_list_falls_back_to_the_unknown_icon(self, icon_sets):
        assert pdsviewable.iconset_for([]) is icon_sets['UNKNOWN', False]

    def test_is_open_selects_the_open_icon_set(self, icon_sets):
        pdsfiles = [_StubPdsFile('LABEL'), _StubPdsFile('IMAGE')]

        assert (pdsviewable.iconset_for(pdsfiles, is_open=True) is
                icon_sets['IMAGE', True])

    def test_an_open_only_icon_type_wins_only_when_open_is_requested(self, icon_sets):
        # load_icons() registers the bare icon_type key only for a closed icon, so
        # an icon whose only file ends in "_open" exists under (type, True) alone.
        # It outranks everything when open is requested, and counts for nothing
        # when it is not, because there is no closed set to return.
        opened = pdsviewable.PdsViewSet(priority=99999)
        icon_sets['PDSINFO', True] = opened
        pdsfiles = [_StubPdsFile('IMAGE'), _StubPdsFile('PDSINFO')]

        assert pdsviewable.iconset_for(pdsfiles, is_open=True) is opened
        assert pdsviewable.iconset_for(pdsfiles) is icon_sets['IMAGE', False]

    def test_an_icon_type_with_no_loaded_icon_set_does_not_win(self, icon_sets):
        # A PdsFile can report an icon type for which no icon file was ever loaded.
        # Such a type must not displace a type that does have one, and must not
        # raise on the way there.
        pdsfiles = [_StubPdsFile('NO_SUCH_ICON_TYPE'), _StubPdsFile('LABEL')]

        assert pdsviewable.iconset_for(pdsfiles) is icon_sets['LABEL', False]

##########################################################################################
