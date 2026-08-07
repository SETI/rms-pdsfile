##########################################################################################
# tests/holdings_maintenance/test_crlf.py
#
# Unit tests for holdings_maintenance/pds3/crlf.py: its pure line-terminator
# classifier, and the command line that drives it.
#
# These are holdings-free: they build their own tiny files in tmp_path and run
# everywhere, including on runners with no holdings at all (hence the
# `holdings_free` marker). The command line is driven in-process, by calling
# main() through support.run_tool_in_process(); the tool imports no PdsFile class
# and reads neither holdings root, so the class-level-cache hazard that keeps the
# other tools on subprocesses (see the package header) cannot arise. Two tests keep
# the subprocess, for the two things an in-process call cannot show: that
# `python -m ...` reaches main() at all, and the process exit code of an uncaught
# exception.
#
# Collection trap: crlf.test_crlf is itself named test_*. Doing
# `from ...crlf import test_crlf` would make pytest collect the *imported*
# function as a test and fail it on a missing `filepath` fixture. Import the
# module and call crlf.test_crlf(...) -- never import the name.
##########################################################################################

import sys

import pytest

from pdsfile.holdings_maintenance.pds3 import crlf
from tests.holdings_maintenance import support

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

        The non-ASCII fraction divides by the decoded length with no guard for an
        empty file, so a run over a tree containing one dies instead of reporting
        it. That is a defect, pinned here as current behaviour: a fix has to
        decide what an empty file classifies as and invert this assertion.
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


class TestCommandLine:
    """What main() reports for a command line, and what it leaves on disk."""

    def test_only_invalid_files_are_listed(self, tmp_path):
        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')
        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', ok, bad)
        assert run.returncode == 0, run.describe()
        assert f'{bad} INVALID' in run.stdout, run.describe()
        assert 'ok.txt' not in run.stdout, run.describe()
        assert '1/2 files invalid' in run.stdout, run.describe()

    def test_verbose_lists_every_file(self, tmp_path):
        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')
        binary = write(tmp_path, 'binary.dat', b'\x00' * 10 + b'A' * 90)

        run = support.run_tool_in_process('crlf', '--verbose', ok, binary)
        assert run.returncode == 0, run.describe()
        assert f'{ok} OK' in run.stdout, run.describe()
        assert f'{binary} BINARY' in run.stdout, run.describe()
        assert '2 files tested' in run.stdout, run.describe()

    def test_repair_rewrites_the_file_and_reports_it(self, tmp_path):
        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')
        bad = write(tmp_path, 'bad.txt', b'ONE\nTWO\r\n')

        run = support.run_tool_in_process('crlf', '--repair', ok, bad)
        assert run.returncode == 0, run.describe()
        assert f'{bad} REPAIRED' in run.stdout, run.describe()
        assert '1/2 files repaired' in run.stdout, run.describe()
        assert bad.read_bytes() == b'ONE\r\nTWO\r\n'
        assert ok.read_bytes() == b'ONE\r\n'

    def test_a_single_file_gets_no_summary_line(self, tmp_path):
        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', bad)
        assert run.returncode == 0, run.describe()
        assert run.stdout == f'{bad} INVALID\n', run.describe()

    def test_two_repairs_print_no_summary_at_all(self, tmp_path):
        """Pin the summary gap: the count is reported only when it is exactly one.

        The repaired branch is guarded by `if repairs == 1`, so a run that fixes
        two or more files lists them and then says nothing about how many. Pinned
        as current behaviour, not endorsed: a fix has to invert this assertion
        deliberately.
        """

        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')
        first = write(tmp_path, 'first.txt', b'ONE\n')
        second = write(tmp_path, 'second.txt', b'TWO\n')

        run = support.run_tool_in_process('crlf', '--repair', ok, first, second)
        assert run.returncode == 0, run.describe()
        assert f'{first} REPAIRED' in run.stdout, run.describe()
        assert f'{second} REPAIRED' in run.stdout, run.describe()
        assert 'files repaired' not in run.stdout, run.describe()
        assert 'files invalid' not in run.stdout, run.describe()
        assert 'files tested' not in run.stdout, run.describe()

    def test_flags_are_accepted_among_the_paths(self, tmp_path):
        """The flags may sit anywhere among the paths, not only in front of them."""

        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')
        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', ok, '--verbose', bad, '--repair')
        assert run.returncode == 0, run.describe()
        assert f'{ok} OK' in run.stdout, run.describe()
        assert f'{bad} REPAIRED' in run.stdout, run.describe()
        assert bad.read_bytes() == b'ONE\r\n'

    def test_no_arguments_prints_nothing(self):
        run = support.run_tool_in_process('crlf')
        assert run.returncode == 0, run.describe()
        assert run.stdout == '', run.describe()

    @pytest.mark.parametrize('flag', ['--help', '-h'])
    def test_help_names_every_flag(self, flag):
        run = support.run_tool_in_process('crlf', flag)
        assert run.returncode == 0, run.describe()
        # The program name argparse prints is taken from sys.argv[0], which the
        # in-process runner sets: without that it would name pytest.
        assert run.stdout.startswith('usage: crlf.py'), run.describe()
        for named in ('--repair', '--verbose'):
            assert named in run.stdout, run.describe()

    @pytest.mark.parametrize('argument', ['--verbose=1', '--repair=yes'])
    def test_a_store_true_flag_rejects_an_explicit_value(self, tmp_path, argument):
        """`--repair=yes` is a usage error, and rewrites nothing.

        Neither flag takes a value, so argparse rejects the whole command line
        rather than reading the value as truthy.
        """

        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', argument, bad)
        assert run.returncode == 2, run.describe()
        assert 'ignored explicit argument' in run.output, run.describe()
        assert bad.read_bytes() == b'ONE\n'

    def test_an_unrecognized_flag_is_a_usage_error(self, tmp_path):
        ok = write(tmp_path, 'ok.txt', b'ONE\r\n')

        run = support.run_tool_in_process('crlf', '--bogus', ok)
        assert run.returncode == 2, run.describe()
        assert 'crlf.py: error: unrecognized arguments: --bogus' in run.stderr, \
            run.describe()

    def test_an_abbreviated_flag_is_a_usage_error_and_rewrites_nothing(self, tmp_path):
        """`--rep` is not `--repair`: an option has to be spelled out.

        The parser sets allow_abbrev=False. With argparse's default, `--rep`
        would mean `--repair` and rewrite every file named after it, so this is
        the assertion that keeps a misspelling from modifying holdings.
        """

        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', '--rep', bad)
        assert run.returncode == 2, run.describe()
        assert 'unrecognized arguments: --rep' in run.output, run.describe()
        assert bad.read_bytes() == b'ONE\n'

    def test_a_repeated_flag_is_accepted(self, tmp_path):
        """Naming a flag twice is a flag, not a path."""

        bad = write(tmp_path, 'bad.txt', b'ONE\n')

        run = support.run_tool_in_process('crlf', '--verbose', '--verbose', bad)
        assert run.returncode == 0, run.describe()
        assert f'{bad} INVALID' in run.stdout, run.describe()

    def test_a_path_beginning_with_a_dash_needs_a_path_and_a_separator_before_it(
            self, tmp_path, monkeypatch):
        """argparse reads a leading `-` as an option, so such a path needs `--`.

        Only the two outcomes that hold on every supported interpreter are
        asserted. What `crlf -- -dash.txt` does -- `--` in first position, with no
        plain positional in front of it -- depends on the Python version, because
        `parse_intermixed_args` splits argv at the first `--` and re-parses the
        remainder: through 3.12 the remainder is read with the optionals still
        live and the command line is rejected, and from 3.13 it is not. Asserting
        either answer would pin one interpreter's, so neither is asserted here.
        """

        write(tmp_path, '-dash.txt', b'ONE\n')
        write(tmp_path, 'ok.txt', b'ONE\r\n')
        monkeypatch.chdir(tmp_path)

        bare = support.run_tool_in_process('crlf', '-dash.txt')
        assert bare.returncode == 2, bare.describe()
        assert '-dash.txt' not in bare.stdout, bare.describe()

        after = support.run_tool_in_process('crlf', 'ok.txt', '--', '-dash.txt')
        assert after.returncode == 0, after.describe()
        assert '-dash.txt INVALID' in after.stdout, after.describe()

    def test_an_unreadable_file_raises_rather_than_being_reported(self, tmp_path):
        """A path that cannot be opened kills the run; nothing catches it."""

        with pytest.raises(FileNotFoundError):
            support.run_tool_in_process('crlf', tmp_path / 'no_such_file.txt')


def test_the_module_is_runnable_as_python_m(tmp_path):
    """`python -m ...` reaches main(), and the process exit code is its return value.

    Driven as a subprocess with neither holdings variable set, which the
    in-process cases above cannot show: they call main() by name, so they would
    pass whether or not the module has a `__main__` block, and they inherit this
    process's environment.
    """

    bad = write(tmp_path, 'bad.txt', b'ONE\n')

    run = support.run_tool_without_holdings('crlf', '--repair', bad, cwd=tmp_path)
    assert run.returncode == 0, run.describe()
    assert f'{bad} REPAIRED' in run.stdout, run.describe()
    assert bad.read_bytes() == b'ONE\r\n'


class TestArgvContract:
    """Both halves of main(argv=None), called directly rather than through a runner.

    support.run_tool_in_process() sets sys.argv *and* passes argv, so it cannot
    tell the two apart: main() could ignore its parameter, or the runner could
    stop passing one, and every test that goes through it would still pass. These
    call main() themselves.
    """

    def test_an_explicit_argv_is_what_gets_parsed(self, tmp_path, monkeypatch,
                                                  capsys):
        bad = write(tmp_path, 'bad.txt', b'ONE\n')
        other = write(tmp_path, 'other.txt', b'TWO\n')
        monkeypatch.setattr(sys, 'argv', ['crlf.py', str(other)])

        assert crlf.main(['crlf.py', str(bad)]) == 0
        captured = capsys.readouterr()
        assert captured.out == f'{bad} INVALID\n', captured.out

    def test_the_in_process_runner_leaves_sys_argv_as_it_found_it(self, tmp_path):
        """The runner rebinds sys.argv for the call; nothing may see that after.

        Without the restore, every test that ran later would see a tool's command
        line in sys.argv, and pytest's own argv would be gone.
        """

        before = list(sys.argv)
        support.run_tool_in_process('crlf', write(tmp_path, 'ok.txt', b'ONE\r\n'))
        assert sys.argv == before

        # ...including when argparse exits out of the call.
        support.run_tool_in_process('crlf', '--bogus')
        assert sys.argv == before

    def test_no_argument_means_sys_argv(self, tmp_path, monkeypatch, capsys):
        bad = write(tmp_path, 'bad.txt', b'ONE\n')
        monkeypatch.setattr(sys, 'argv', ['crlf.py', str(bad)])

        assert crlf.main() == 0
        captured = capsys.readouterr()
        assert captured.out == f'{bad} INVALID\n', captured.out


def test_an_unreadable_file_ends_the_process_with_a_traceback(tmp_path):
    """A file that cannot be opened exits 1 with the traceback, uncaught.

    A subprocess, because that is the only place the *process* exit code of an
    uncaught exception is observable; the in-process case above can only see the
    exception. Nothing in either tool catches one, and this is what says so.
    """

    run = support.run_tool_without_holdings('crlf', tmp_path / 'no_such_file.txt',
                                            cwd=tmp_path)
    assert run.returncode == 1, run.describe()
    assert 'FileNotFoundError' in run.stderr, run.describe()
    assert run.stdout == '', run.describe()
