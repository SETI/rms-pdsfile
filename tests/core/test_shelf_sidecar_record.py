##########################################################################################
# tests/core/test_shelf_sidecar_record.py
#
# Tests for _eval_null_key_record, the parse behind shelf_lookup's shortcut: for a
# bundle -- the null key of an info shelf -- it reads the values off the second
# line of the readable "<bundlename>_info.py" sidecar instead of unpickling the
# whole "<bundlename>_info.pickle".
#
# Nothing else in the suite reaches it. A holdings tree carries the sidecars only
# where the maintenance tools have written them, and the copy the goldens are
# tuned to has the .pickle half alone, so the branch is dark in every full-data
# run. These tests build their own record and need no holdings tree.
#
# The parse accepts its input with eval(), so what it does with a malformed line
# is behavior, not an accident: the cases below pin what happens today, including
# the two ways a record can be misread silently.
##########################################################################################

import pytest

from pdsfile._shelves import _eval_null_key_record

pytestmark = pytest.mark.holdings_free

# A verbatim second line as the holdings_maintenance tools write it: the columns
# are padded out, the key is empty, and the value is a five-item tuple whose third
# element carries two more colons than the one the parse splits on.
_RECORD = ('    ""                                                              '
           '     : ( 4594843481,   9, "2014-07-08 17:47:46.000000", ""          '
           '                      , (   0,   0)),\n')

_VALUES = (4594843481, 9, '2014-07-08 17:47:46.000000', '', (0, 0))


class TestAWellFormedRecord:

    def test_the_five_values_come_back_as_python_objects(self):
        values = _eval_null_key_record(_RECORD)

        assert values == _VALUES
        # Not the source text: the sizes are ints and the shape is a real tuple,
        # which is what shelf_lookup hands to its callers.
        assert [type(v) for v in values] == [int, int, str, str, tuple]

    def test_the_split_is_the_first_colon_and_not_one_of_the_timestamps(self):
        # The timestamp holds two colons of its own. Splitting on the last one, or
        # on all of them, would silently truncate the record.
        assert _RECORD.count(':') == 3
        assert _eval_null_key_record(_RECORD)[2] == '2014-07-08 17:47:46.000000'

    def test_a_line_read_back_off_a_written_sidecar_parses(self, tmp_path):
        # The same two readline() calls shelf_lookup makes, so the trailing
        # newline and the leading indentation are present exactly as they are in a
        # real file.
        sidecar = tmp_path / 'NOSUCH_0001_info.py'
        sidecar.write_text('info = {\n' + _RECORD + '}\n')

        with sidecar.open() as f:
            f.readline()
            rec = f.readline()

        assert _eval_null_key_record(rec) == _VALUES


class TestAMalformedRecord:
    """What happens today, recorded so a later change to this parse is visible."""

    @pytest.mark.parametrize(
        ('label', 'rec'),
        [
            ('no colon at all', 'nothing to partition here\n'),
            ('an unclosed tuple', '"": ( 1,   2,\n'),
            ('nothing after the colon', '"":\n'),
        ]
    )
    def test_an_unparseable_line_raises_syntax_error(self, label, rec):
        with pytest.raises(SyntaxError):
            _eval_null_key_record(rec)

    def test_the_last_character_is_dropped_whether_or_not_it_is_the_comma(self):
        # The trailing comma is removed by position, not by matching it. A record
        # written without one loses a real character instead -- here turning 123
        # into 12, with no error. This is the reason the sidecars are only ever
        # written by this package's own tools.
        assert _eval_null_key_record('"": 123\n') == 12

    def test_an_unknown_name_is_a_name_error(self):
        # eval() resolves a bare name against the function's locals, then this
        # module's globals, then the builtins. A record written by the maintenance
        # tools is a tuple of literals and never reaches this path.
        with pytest.raises(NameError):
            _eval_null_key_record('"": no_such_name,\n')

##########################################################################################
