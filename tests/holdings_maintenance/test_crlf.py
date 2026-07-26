##########################################################################################
# tests/holdings_maintenance/test_crlf.py
#
# Unit tests for the pure line-terminator classifier in holdings_maintenance/pds3/crlf.py.
#
# These are holdings-free: they build their own tiny files in tmp_path and run
# everywhere, including on runners with no holdings at all (hence the
# `holdings_free` marker).
#
# Collection trap: crlf.test_crlf is itself named test_*. Doing
# `from ...crlf import test_crlf` would make pytest collect the *imported*
# function as a test and fail it on a missing `filepath` fixture. Import the
# module and call crlf.test_crlf(...) -- never import the name.
##########################################################################################

import pytest

from pdsfile.holdings_maintenance.pds3 import crlf

pytestmark = pytest.mark.holdings_free


def write(tmp_path, name, data):
    """Write bytes to a file under tmp_path and return its path."""

    path = tmp_path / name
    path.write_bytes(data)

    return path


class TestClassifier:
    """The four return values of crlf.test_crlf in task='test' mode."""

    def test_ok_when_every_record_ends_in_crlf(self, tmp_path):
        path = write(tmp_path, 'ok.txt', b'ONE\r\nTWO\r\nTHREE\r\n')
        assert crlf.test_crlf(path) == 'OK'

    def test_invalid_when_a_record_lacks_the_cr(self, tmp_path):
        path = write(tmp_path, 'bare_lf.txt', b'ONE\r\nTWO\nTHREE\r\n')
        assert crlf.test_crlf(path) == 'INVALID'

    def test_invalid_when_the_final_record_has_no_terminator(self, tmp_path):
        path = write(tmp_path, 'no_final.txt', b'ONE\r\nTWO')
        assert crlf.test_crlf(path) == 'INVALID'

    def test_binary_when_non_ascii_exceeds_the_threshold(self, tmp_path):
        # 10 of 100 bytes are non-ASCII: 0.10 > the 0.01 default threshold.
        path = write(tmp_path, 'binary.dat', b'\x00' * 10 + b'A' * 90)
        assert crlf.test_crlf(path) == 'BINARY'

    def test_threshold_is_honored(self, tmp_path):
        # The same file is text once the threshold is raised above 0.10.
        path = write(tmp_path, 'binary.dat', b'\x00' * 10 + b'A' * 89 + b'\r\n')
        assert crlf.test_crlf(path, threshold=0.5) == 'OK'
        assert crlf.test_crlf(path, threshold=0.05) == 'BINARY'

    def test_tab_cr_and_lf_do_not_count_as_non_ascii(self, tmp_path):
        # NON_ASCIIS maps \t, \r and \n to None, so a tab-heavy file stays text.
        path = write(tmp_path, 'tabs.txt', b'\t' * 50 + b'A' * 50 + b'\r\n')
        assert crlf.test_crlf(path) == 'OK'


class TestRepair:
    """task='repair' rewrites the file in place and reports REPAIRED."""

    def test_repair_adds_missing_carriage_returns(self, tmp_path):
        path = write(tmp_path, 'bare_lf.txt', b'ONE\r\nTWO\nTHREE\r\n')
        assert crlf.test_crlf(path, task='repair') == 'REPAIRED'
        assert path.read_bytes() == b'ONE\r\nTWO\r\nTHREE\r\n'
        # Idempotent: a repaired file is already OK.
        assert crlf.test_crlf(path, task='repair') == 'OK'

    def test_repair_terminates_the_final_record(self, tmp_path):
        path = write(tmp_path, 'no_final.txt', b'ONE\r\nTWO')
        assert crlf.test_crlf(path, task='repair') == 'REPAIRED'
        assert path.read_bytes() == b'ONE\r\nTWO\r\n'

    def test_repair_leaves_a_valid_file_untouched(self, tmp_path):
        path = write(tmp_path, 'ok.txt', b'ONE\r\nTWO\r\n')
        assert crlf.test_crlf(path, task='repair') == 'OK'
        assert path.read_bytes() == b'ONE\r\nTWO\r\n'

    def test_repair_never_rewrites_a_binary_file(self, tmp_path):
        original = b'\x00' * 10 + b'A' * 90
        path = write(tmp_path, 'binary.dat', original)
        assert crlf.test_crlf(path, task='repair') == 'BINARY'
        assert path.read_bytes() == original

    def test_test_mode_never_rewrites(self, tmp_path):
        original = b'ONE\r\nTWO\nTHREE\r\n'
        path = write(tmp_path, 'bare_lf.txt', original)
        assert crlf.test_crlf(path, task='test') == 'INVALID'
        assert path.read_bytes() == original

    def test_latin8_bytes_survive_a_repair_round_trip(self, tmp_path):
        # The tool decodes and re-encodes as latin-8; high bytes below the
        # threshold must come back unchanged.
        original = b'CAF\xc9\r\n' + b'A' * 200 + b'\n'
        path = write(tmp_path, 'accent.txt', original)
        assert crlf.test_crlf(path, task='repair') == 'REPAIRED'
        assert path.read_bytes() == b'CAF\xc9\r\n' + b'A' * 200 + b'\r\n'


class TestArgumentValidation:
    """Bad arguments raise ValueError before the file is opened.

    Each case passes a path that does not exist: if validation ever moved after
    the read, these would raise FileNotFoundError instead and fail.
    """

    def test_unknown_task_rejected(self, tmp_path):
        with pytest.raises(ValueError, match='invalid task'):
            crlf.test_crlf(tmp_path / 'no_such_file.txt', task='destroy')

    @pytest.mark.parametrize('threshold', [-0.1, 1.1])
    def test_threshold_out_of_range_rejected(self, tmp_path, threshold):
        with pytest.raises(ValueError, match='invalid threshold'):
            crlf.test_crlf(tmp_path / 'no_such_file.txt', threshold=threshold)

    def test_an_empty_file_raises_zerodivisionerror(self, tmp_path):
        """A zero-byte file divides by zero.

        Pinned as current behaviour; see entry 11 of "From PR-13" in
        critiques/deferred-observations.md.
        """

        path = write(tmp_path, 'empty.txt', b'')
        with pytest.raises(ZeroDivisionError, match='division by zero'):
            crlf.test_crlf(path)


def test_non_asciis_translation_table():
    """The module-level table marks control and high bytes, sparing \\t, \\r, \\n."""

    assert crlf.NON_ASCIIS[0] == 'x'
    assert crlf.NON_ASCIIS[200] == 'x'
    assert crlf.NON_ASCIIS[ord('A')] is None
    for char in ('\t', '\r', '\n'):
        assert crlf.NON_ASCIIS[ord(char)] is None
