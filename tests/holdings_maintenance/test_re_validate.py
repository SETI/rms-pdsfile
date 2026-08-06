##########################################################################################
# tests/holdings_maintenance/test_re_validate.py
#
# Tests for holdings_maintenance/pds3/re_validate.py.
#
# These run IN-PROCESS, unlike every other module in this directory, which drives its
# tool as a subprocess. That convention exists because PdsFile.CACHE is a class-level
# cache keyed by *logical* path and the test session preloads the real holdings tree, so
# an in-process call can resolve a temporary-tree path back to the real tree.
#
# Running in-process here is safe for a reason that has to be maintained, not for a
# property of the code. Five of the functions under test touch the real Pds3File class:
#
#   validate_one_volume, run_interactive, run_batch and print_batch_status construct
#     PdsFile objects through Pds3File.from_abspath;
#   main calls Pds3File.set_log_root, a classmethod that writes class state every later
#     caller in the process sees.
#
# EVERY test that drives one of those five replaces `re_validate.pdsfile` with a stub
# first -- the `volume_tree` fixture does it for the first, each main test does it for
# itself -- and a new test that does not inherits the cache hazard, or leaks a log root,
# in full. Two tests call run_interactive and one calls print_batch_status without a
# stub; each is safe only because it returns before the construction, which is a reason
# to check rather than to copy.
#
# Everything else under test -- option derivation, log parsing, find_modified_volumes,
# the missing-volume report, format_email, resolve_log_root -- is pure over text, paths
# and an argparse namespace. Nothing here reads or writes a holdings tree, so the whole
# module is holdings_free.
#
# Five tests use a subprocess: the two import-inertness tests, which need an interpreter
# that has not imported the module yet, and the three that run the whole program through
# `python -m`.
#
# What is deliberately not covered: the five sibling tools validate_one_volume calls,
# which their own modules cover; get_volume_info, which globs a real holdings tree; and
# send_email's socket half. The message send_email builds is covered through
# format_email.
##########################################################################################

import os
import subprocess
import sys
import types

import pytest

import pdsfile
from pdsfile.holdings_maintenance.pds3 import re_validate

pytestmark = pytest.mark.holdings_free

LOGNAME = 'pds.validation'


class Namespace:
    """A stand-in for the parsed command line, holding only what a test sets."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def subprocess_env():
    """Return an environment in which a subprocess can import pdsfile."""

    src = os.path.dirname(os.path.dirname(os.path.abspath(pdsfile.__file__)))
    env = dict(os.environ)
    env['PYTHONPATH'] = src + os.pathsep + env.get('PYTHONPATH', '')

    return env


def run_module(*args):
    """Run the tool as `python -m ...` and return the CompletedProcess."""

    return subprocess.run([sys.executable, '-m',
                           'pdsfile.holdings_maintenance.pds3.re_validate', *args],
                          capture_output=True, text=True, env=subprocess_env(),
                          check=False)


def parse(*argv):
    """Return the namespace the tool's parser produces for these arguments."""

    return re_validate.build_parser().parse_args(list(argv))


def write_log(directory, volname, *, abspath, modtime='2026-01-01 00:00:00',
              tag='2026-01-02T03-04-05', error=False, fatal=False,
              elapsed='0:00:12.345678', logname=LOGNAME, records=None):
    """Write one re-validate log file and return its path.

    Args:
        directory: The volset directory to write into. Created if absent.
        volname: The volume name the log's basename starts with.
        abspath: The volume path recorded in the log's first line.
        modtime: The value of the "Last modification" line.
        tag: The time tag in the basename, which is what orders the versions.
        error: True to include an ERROR record.
        fatal: True to include a FATAL record.
        elapsed: The elapsed time, or None to omit the closing record entirely.
        logname: The logger name in the second field, which identifies the tool.
        records: Complete replacement records, bypassing every argument above
            except volname and tag. Used for the malformed cases.

    Returns:
        str: The path written.
    """

    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f'{volname}_re-validate_{tag}.log')

    if records is None:
        records = [f'2026-01-02 03:04:05 | {logname} | | HEADER | '
                   f'Re-validate {abspath}',
                   f'2026-01-02 03:04:05 | {logname} | | INFO | '
                   f'Last modification: {modtime}']
        if error:
            records.append(f'2026-01-02 03:04:06 | {logname} | | ERROR | bad')
        if fatal:
            records.append(f'2026-01-02 03:04:06 | {logname} | | FATAL | worse')
        if elapsed is not None:
            records.append(f'2026-01-02 03:04:17 | {logname} | | SUMMARY | '
                           f'Elapsed time = {elapsed}')

    with open(path, 'w') as f:
        f.write('\n'.join(records) + '\n')

    return path


##########################################################################################
# Importing the module must do nothing
##########################################################################################

def test_importing_the_module_runs_no_command_line():
    """Importing the module is inert, whatever sys.argv happens to hold.

    Before this module had a main(), every statement of the program ran at import:
    a bare `import` parsed sys.argv, and with an argv the tool disliked it called
    sys.exit() from inside the import. Anything that imports this module -- pytest
    collection included -- would have inherited that.
    """

    script = ('import sys\n'
              "sys.argv = ['re_validate.py', '--batch', '/no/such/holdings']\n"
              'from pdsfile.holdings_maintenance.pds3 import re_validate\n'
              "print('IMPORTED', re_validate.main.__name__)\n")
    done = subprocess.run([sys.executable, '-c', script], capture_output=True,
                          text=True, env=subprocess_env(), check=False)

    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == 'IMPORTED main', done.stdout
    assert 'No holdings path identified' not in done.stdout
    assert 'Missing volume path' not in done.stdout


def test_importing_the_module_builds_no_logger():
    """Importing the module registers no logger and sets no log root.

    The program used to construct its PdsLogger and call Pds3File.set_log_root() at
    import, so importing it mutated process-wide state that every later caller saw.
    """

    script = ('import logging, sys\n'
              "sys.argv = ['re_validate.py']\n"
              'before = set(logging.Logger.manager.loggerDict)\n'
              'from pdsfile.holdings_maintenance.pds3 import re_validate\n'
              'after = set(logging.Logger.manager.loggerDict)\n'
              "print(sorted(n for n in after - before if 'pds.validation' in n))\n")
    done = subprocess.run([sys.executable, '-c', script], capture_output=True,
                          text=True, env=subprocess_env(), check=False)

    assert done.returncode == 0, done.stderr
    assert done.stdout.strip() == '[]', done.stdout


##########################################################################################
# Option derivation
##########################################################################################

def test_previews_flag_selects_previews():
    """--previews selects the preview tree.

    It used to be parsed and never read: the previews tree was appended by
    `if args.calibrated`, so --previews alone selected nothing, fell through to the
    "no volume type named" default, and silently behaved like --all.
    """

    (voltypes, _tests) = re_validate.derive_options(parse('--previews'))

    assert voltypes == ['previews']


def test_previews_is_not_dropped_beside_another_volume_type():
    """--volumes --previews selects both, not just volumes."""

    (voltypes, _tests) = re_validate.derive_options(parse('--volumes', '--previews'))

    assert voltypes == ['volumes', 'previews']


def test_calibrated_does_not_also_select_previews():
    """--calibrated selects only the calibrated tree."""

    (voltypes, _tests) = re_validate.derive_options(parse('--calibrated'))

    assert voltypes == ['calibrated']


@pytest.mark.parametrize('argv', [(), ('--all',), ('-a',)])
def test_no_volume_type_and_all_both_select_everything(argv):
    """Naming no volume type, or naming --all, selects all five trees."""

    (voltypes, _tests) = re_validate.derive_options(parse(*argv))

    assert voltypes == ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews']


def test_all_overrides_a_narrower_selection():
    """--all wins over a volume-type flag named beside it."""

    (voltypes, _tests) = re_validate.derive_options(parse('--volumes', '--all'))

    assert voltypes == ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews']


@pytest.mark.parametrize('argv', [(), ('--full',), ('-F',)])
def test_no_test_flag_and_full_both_select_every_test(argv):
    """Naming no test, or naming --full, runs all five tests."""

    (_voltypes, tests) = re_validate.derive_options(parse(*argv))

    assert tests == ['checksums', 'archives', 'infoshelves', 'linkshelves',
                     'dependencies']


def test_one_test_flag_selects_only_that_test():
    """Naming one test runs only it."""

    (_voltypes, tests) = re_validate.derive_options(parse('--checksums'))

    assert tests == ['checksums']


def test_dependencies_are_dropped_without_the_volumes_tree():
    """The dependency test needs the volumes tree and is dropped without it."""

    args = parse('--dependencies', '--metadata')
    (_voltypes, tests) = re_validate.derive_options(args)

    assert tests == []
    assert args.dependencies is False


def test_linkshelves_are_dropped_without_a_tree_that_has_them():
    """The linkshelf test is dropped when no tree it covers is selected."""

    args = parse('--links', '--diagrams')
    (_voltypes, tests) = re_validate.derive_options(args)

    assert tests == []
    assert args.linkshelves is False


@pytest.mark.parametrize('voltype', ['--volumes', '--calibrated', '--metadata'])
def test_linkshelves_survive_each_tree_that_has_them(voltype):
    """The linkshelf test survives every tree a link shelf exists for."""

    args = parse('--links', voltype)
    (_voltypes, tests) = re_validate.derive_options(args)

    assert tests == ['linkshelves']
    assert args.linkshelves is True


def test_timeless_survives_with_the_dependency_test():
    """--timeless stays set while the dependency test runs."""

    args = parse('--timeless', '--dependencies')
    re_validate.derive_options(args)

    assert args.timeless is True


def test_timeless_is_cleared_without_the_dependency_test():
    """--timeless is cleared when the dependency test is not going to run.

    It only suppresses a check the dependency test makes, so it means nothing on
    its own -- and validate_one_volume picks the log's wording off it.
    """

    args = parse('--timeless', '--checksums')
    re_validate.derive_options(args)

    assert args.timeless is False


def test_derived_tests_are_written_back_onto_the_namespace():
    """The derived tests land on args, which is where validate_one_volume reads them."""

    args = parse('--checksums')
    re_validate.derive_options(args)

    assert args.checksums is True
    assert args.archives is False
    assert args.infoshelves is False
    assert args.linkshelves is False
    assert args.dependencies is False


def test_deriving_twice_does_not_accumulate():
    """Deriving from a second namespace is unaffected by the first.

    The default volume-type list is rebuilt per call rather than shared, so one run
    cannot append to the list a later run sees.
    """

    first = re_validate.derive_options(parse())[0]
    first.append('bogus')
    second = re_validate.derive_options(parse())[0]

    assert 'bogus' not in second


##########################################################################################
# Log parsing
##########################################################################################

def test_get_log_info_reads_a_good_log(tmp_path):
    """Every field of a well-formed log is recovered."""

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001',
                     modtime='2026-01-01 00:00:00')

    info = re_validate.get_log_info(path)

    assert info == ('2026-01-02 03:04:05', '0:00:12.345678', '2026-01-01 00:00:00',
                    '/h/holdings/volumes/VS_1xxx/VOL_0001', False, False)


def test_get_log_info_reports_an_error_record(tmp_path):
    """An ERROR record anywhere in the log sets the had_error flag."""

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001', error=True)

    assert re_validate.get_log_info(path)[4] is True


def test_get_log_info_reports_a_fatal_record(tmp_path):
    """A FATAL record anywhere in the log sets the had_fatal flag."""

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001', fatal=True)

    assert re_validate.get_log_info(path)[5] is True


def test_get_log_info_treats_a_truncated_log_as_fatal(tmp_path):
    """A log with no elapsed-time record is treated as fatal, not as a success.

    A run that was killed leaves no closing record, and re-reading it as a clean
    result would retire a volume that was never finished.
    """

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001', elapsed=None)

    info = re_validate.get_log_info(path)

    assert info[1] is None
    assert info[5] is True


def test_get_log_info_rejects_an_empty_log(tmp_path):
    """An empty file raises ValueError."""

    path = write_log(str(tmp_path), 'VOL_0001', abspath='x', records=[])

    with pytest.raises(ValueError, match='Empty log file'):
        re_validate.get_log_info(path)


def test_get_log_info_rejects_a_one_line_log(tmp_path):
    """A log with a header and nothing else raises ValueError, not IndexError.

    The length guard used to sit after the second record had already been indexed,
    so a one-line log raised IndexError -- which get_all_log_info does not catch,
    so one truncated log aborted the whole batch scan.
    """

    path = write_log(str(tmp_path), 'VOL_0001', abspath='x',
                     records=[f'2026-01-02 03:04:05 | {LOGNAME} | | HEADER | '
                              f'Re-validate /a'])

    with pytest.raises(ValueError, match='Not a re-validate log file'):
        re_validate.get_log_info(path)


def test_get_log_info_rejects_another_tools_log(tmp_path):
    """A log written by a different tool raises ValueError."""

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001',
                     logname='pds.validation.archives')

    with pytest.raises(ValueError, match='Not a re-validate log file'):
        re_validate.get_log_info(path)


def test_get_log_info_rejects_a_log_with_no_modification_line(tmp_path):
    """A log whose second record is not the modification time raises ValueError."""

    path = write_log(str(tmp_path), 'VOL_0001', abspath='x',
                     records=[f'2026-01-02 03:04:05 | {LOGNAME} | | HEADER | '
                              f'Re-validate /a',
                              f'2026-01-02 03:04:06 | {LOGNAME} | | INFO | '
                              f'something else'])

    with pytest.raises(ValueError, match='Missing modification time'):
        re_validate.get_log_info(path)


def test_volume_abspath_from_log_reads_the_first_record(tmp_path):
    """The volume path is recovered from the log's opening record."""

    path = write_log(str(tmp_path), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001')

    assert (re_validate.volume_abspath_from_log(path)
            == '/h/holdings/volumes/VS_1xxx/VOL_0001')


def test_volume_abspath_from_log_returns_empty_for_an_empty_log(tmp_path):
    """An empty log yields the empty string, which the caller treats as unknown."""

    path = write_log(str(tmp_path), 'VOL_0001', abspath='x', records=[])

    assert re_validate.volume_abspath_from_log(path) == ''


def test_key_from_volume_abspath():
    """The key is the last two path components."""

    assert (re_validate.key_from_volume_abspath(
        '/h/holdings/volumes/VS_1xxx/VOL_0001') == 'VS_1xxx/VOL_0001')


def test_key_from_log_path():
    """The key is the log's parent directory and the basename up to the time tag.

    This used to read a bare `abspath` that was neither its parameter nor a local,
    so every call raised NameError; it resolved to a name at all only because the
    module-level program left one bound as a global.
    """

    assert (re_validate.key_from_log_path(
        '/logs/re-validate/VS_1xxx/VOL_0001_re-validate_2026-01-02T03-04-05.log')
        == 'VS_1xxx/VOL_0001')


def test_key_from_log_path_agrees_with_the_key_get_all_log_info_builds(tmp_path):
    """It returns the same key the batch scan derives inline for the same log."""

    path = write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001',
                     abspath='/h/holdings/volumes/VS_1xxx/VOL_0001')
    (_info, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    assert re_validate.key_from_log_path(path) in logs_for_key


def test_get_all_log_info_finds_one_log_per_volume(tmp_path):
    """Every volume with a usable log contributes one entry, keyed by volset/volume."""

    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0001')
    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0002',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0002')

    (info_list, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    assert sorted(logs_for_key) == ['VS_1xxx/VOL_0001', 'VS_1xxx/VOL_0002']
    assert sorted(i[3] for i in info_list) == [
        '/h/holdings/volumes/VS_1xxx/VOL_0001',
        '/h/holdings/volumes/VS_1xxx/VOL_0002']


def test_get_all_log_info_prefers_the_newest_log(tmp_path):
    """The latest time tag wins, and every version is still listed."""

    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001', tag='2026-01-01T00-00-00',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0001',
              modtime='older')
    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001', tag='2026-06-01T00-00-00',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0001',
              modtime='newer')

    (info_list, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    assert [i[2] for i in info_list] == ['newer']
    assert len(logs_for_key['VS_1xxx/VOL_0001']) == 2


def test_get_all_log_info_skips_a_fatal_log_and_falls_back(tmp_path):
    """A log that recorded a FATAL is passed over for the newest one that did not."""

    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001', tag='2026-01-01T00-00-00',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0001', modtime='good')
    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001', tag='2026-06-01T00-00-00',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0001', modtime='doomed',
              fatal=True)

    (info_list, _logs) = re_validate.get_all_log_info(str(tmp_path))

    assert [i[2] for i in info_list] == ['good']


def test_get_all_log_info_skips_a_log_whose_internal_path_disagrees(tmp_path):
    """A log filed under one volume but describing another is ignored.

    The holdings tree is occasionally reorganized, which can leave a log sitting in
    a directory that no longer matches the volume path recorded inside it.
    """

    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001',
              abspath='/h/holdings/volumes/VS_9xxx/VOL_9999')

    (info_list, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    assert list(logs_for_key) == ['VS_1xxx/VOL_0001']
    assert info_list == []


def test_get_all_log_info_ignores_files_that_are_not_logs(tmp_path):
    """Files without the tool's naming pattern are not log files."""

    directory = tmp_path / 'VS_1xxx'
    os.makedirs(str(directory))
    (directory / 'VOL_0001_re-validate_2026.txt').write_text('not a log\n')
    (directory / 'VOL_0001_pdsarchives_2026.log').write_text('other tool\n')

    (info_list, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    assert logs_for_key == {}
    assert info_list == []


def test_get_all_log_info_skips_a_malformed_log_without_raising(tmp_path):
    """A one-line log is skipped, and the good log beside it is still found."""

    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0001', abspath='x',
              records=[f'2026-01-02 03:04:05 | {LOGNAME} | | HEADER | '
                       f'Re-validate /a'])
    write_log(str(tmp_path / 'VS_1xxx'), 'VOL_0002',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_0002')

    (info_list, _logs) = re_validate.get_all_log_info(str(tmp_path))

    assert [i[3] for i in info_list] == ['/h/holdings/volumes/VS_1xxx/VOL_0002']


##########################################################################################
# find_modified_volumes
##########################################################################################

def log_tuple(abspath, modtime, *, start='2025-06-01', elapsed='0:00:10',
              had_error=False, had_fatal=False):
    """Return one get_log_info-shaped tuple."""

    return (start, elapsed, modtime, abspath, had_error, had_fatal)


def test_find_modified_volumes_reports_a_changed_volume():
    """A volume whose modification time no longer matches its log is due again."""

    holdings = [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'new')]
    logs = [log_tuple('/h/holdings/volumes/VS_1xxx/VOL_0001', 'old')]

    (modified, current, missing) = re_validate.find_modified_volumes(holdings, logs)

    assert modified == [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'new')]
    assert current == []
    assert missing == []


def test_a_changed_volume_is_not_also_listed_as_validated():
    """A volume that is both changed and previously logged appears exactly once.

    The log entry used to survive alongside the modified entry, so batch mode
    listed the volume twice and validated it twice in one run.
    """

    holdings = [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'new')]
    logs = [log_tuple('/h/holdings/volumes/VS_1xxx/VOL_0001', 'old')]

    (modified, current, _missing) = re_validate.find_modified_volumes(holdings, logs)

    assert [p[0] for p in modified] == ['/h/holdings/volumes/VS_1xxx/VOL_0001']
    assert [i[3] for i in current] == []


def test_find_modified_volumes_keeps_an_unchanged_volume():
    """A volume whose modification time still matches its log is not due again."""

    holdings = [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'same')]
    logs = [log_tuple('/h/holdings/volumes/VS_1xxx/VOL_0001', 'same')]

    (modified, current, missing) = re_validate.find_modified_volumes(holdings, logs)

    assert modified == []
    assert [i[3] for i in current] == ['/h/holdings/volumes/VS_1xxx/VOL_0001']
    assert missing == []


def test_find_modified_volumes_reports_a_volume_that_is_gone():
    """A volume with a log and no directory is reported missing and dropped."""

    holdings = [('/h/holdings/volumes/VS_1xxx/VOL_0001', 'same')]
    logs = [log_tuple('/h/holdings/volumes/VS_1xxx/VOL_0001', 'same'),
            log_tuple('/h/holdings/volumes/VS_1xxx/VOL_9999', 'same')]

    (_modified, current, missing) = re_validate.find_modified_volumes(holdings, logs)

    assert missing == ['VS_1xxx/VOL_9999']
    assert [i[3] for i in current] == ['/h/holdings/volumes/VS_1xxx/VOL_0001']


def test_find_modified_volumes_redirects_a_relocated_tree():
    """A log from another holdings tree is redirected to the tree being validated."""

    holdings = [('/new/holdings/volumes/VS_1xxx/VOL_0001', 'same')]
    logs = [log_tuple('/old/holdings/volumes/VS_1xxx/VOL_0001', 'same')]

    (_modified, current, missing) = re_validate.find_modified_volumes(holdings, logs)

    assert [i[3] for i in current] == ['/new/holdings/volumes/VS_1xxx/VOL_0001']
    assert missing == []


def test_find_modified_volumes_orders_modified_volumes_oldest_first():
    """The volumes due again are ordered from oldest modification time to newest."""

    holdings = [('/h/holdings/volumes/VS_1xxx/VOL_0002', '2026-02-01'),
                ('/h/holdings/volumes/VS_1xxx/VOL_0001', '2026-01-01')]

    (modified, _current, _missing) = re_validate.find_modified_volumes(holdings, [])

    assert [p[1] for p in modified] == ['2026-01-01', '2026-02-01']


##########################################################################################
# The missing-volume report
##########################################################################################

class RecordingLogger:
    """A stand-in that records the error() calls the report makes."""

    def __init__(self):
        self.errors = []

    def error(self, message, path=None, **_kwargs):
        self.errors.append((message, path))


def test_missing_volume_is_reported(tmp_path):
    """A volume whose logs came from this holdings tree is reported as missing.

    The two statements that collect each key's holdings trees used to sit after a
    `continue` in the same block, so the set they filled was always empty, the
    intersection below it was always empty, and this error never fired at all.
    """

    directory = str(tmp_path / 'VS_1xxx')
    write_log(directory, 'VOL_9999',
              abspath='/h/holdings/volumes/VS_1xxx/VOL_9999')
    (_info, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    logger = RecordingLogger()
    re_validate.report_missing_volumes(['VS_1xxx/VOL_9999'], logs_for_key,
                                       {'/h/holdings'}, logger)

    assert logger.errors == [('Missing volume',
                              '/h/holdings/volumes/VS_1xxx/VOL_9999')]


def test_missing_volume_in_another_tree_is_not_reported(tmp_path):
    """A volume whose logs came from a tree this run is not validating is ignored."""

    directory = str(tmp_path / 'VS_1xxx')
    write_log(directory, 'VOL_9999',
              abspath='/other/holdings/volumes/VS_1xxx/VOL_9999')
    (_info, logs_for_key) = re_validate.get_all_log_info(str(tmp_path))

    logger = RecordingLogger()
    re_validate.report_missing_volumes(['VS_1xxx/VOL_9999'], logs_for_key,
                                       {'/h/holdings'}, logger)

    assert logger.errors == []


def test_missing_volume_with_only_empty_logs_is_not_reported(tmp_path):
    """A key whose logs are all empty names no holdings tree, so nothing is said."""

    directory = str(tmp_path / 'VS_1xxx')
    write_log(directory, 'VOL_9999', abspath='x', records=[])
    logs_for_key = {'VS_1xxx/VOL_9999': [os.path.join(
        directory, 'VOL_9999_re-validate_2026-01-02T03-04-05.log')]}

    logger = RecordingLogger()
    re_validate.report_missing_volumes(['VS_1xxx/VOL_9999'], logs_for_key,
                                       {'/h/holdings'}, logger)

    assert logger.errors == []


##########################################################################################
# validate_one_volume, driven against a temporary tree with the five sibling tools
# and the logger replaced
##########################################################################################

class StubLogger:
    """Records what validate_one_volume logs, instead of logging it."""

    def __init__(self, close_result=(0, 0, 0, 0)):
        self.opens = []
        self.infos = []
        self.exceptions = []
        self.close_result = close_result

    def blankline(self):
        pass

    def open(self, message, path=None, **_kwargs):
        self.opens.append((message, path))

    def info(self, message, path=None, **_kwargs):
        self.infos.append((message, path))

    def error(self, message, path=None, **_kwargs):
        pass

    def close(self):
        # The real PdsLogger returns (fatal, errors, warnings, tests). The counts
        # are distinguishable on purpose, so a test can tell the positions apart.
        return self.close_result

    def exception(self, e):
        self.exceptions.append(e)


class StubBatchLogger(StubLogger):
    """A StubLogger that also answers the calls main() and the batch driver make."""

    def __init__(self, close_result=(0, 0, 0, 0)):
        super().__init__(close_result)
        self.handlers = []

    def add_root(self, root):
        pass

    def add_handler(self, handler):
        self.handlers.append(handler)


class StubPdsdir:
    """The attributes the tool reads off a volume directory."""

    def __init__(self, abspath):
        self.abspath = abspath
        self.date = '2026-01-01'
        self.root_ = abspath.split('/volumes/')[0] + '/'
        self.volset_ = 'VS_1xxx/'
        self.volname = abspath.rstrip('/').rpartition('/')[2]


@pytest.fixture
def volume_tree(tmp_path, monkeypatch):
    """Return a real volume directory, with everything outside the tool stubbed.

    The directory tree is real, so os.path.exists and glob.glob are the genuine
    functions answering about genuine paths. What is replaced is only what reaches
    outside this module: the log-path helper, the pdslogger handler factories, the
    PdsFile class, and the five sibling tools whose own modules test them.
    """

    holdings = tmp_path / 'holdings'
    for voltype in re_validate.ALL_VOLTYPES:
        (holdings / voltype / 'VS_1xxx' / 'VOL_0001').mkdir(parents=True)

    logfiles = [str(tmp_path / 'a' / 'volumes' / 'VOL_0001_re-validate_x.log'),
                str(tmp_path / 'b' / 'volumes' / 'VOL_0001_re-validate_x.log')]

    calls = []
    log_path_kwargs = {}

    def fake_log_paths_for(pdsf, method, *args, **kwargs):
        log_path_kwargs.update(method=method, args=args, kwargs=kwargs)
        return list(logfiles)

    monkeypatch.setattr(re_validate._common, 'log_paths_for', fake_log_paths_for)
    monkeypatch.setattr(re_validate.pdslogger, 'file_handler', lambda p: ('file', p))
    monkeypatch.setattr(re_validate.pdslogger, 'error_handler', lambda d: ('err', d))
    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(from_abspath=StubPdsdir)))
    for name in ('pdschecksums', 'pdsarchives', 'pdsinfoshelf', 'pdslinkshelf'):
        monkeypatch.setattr(re_validate, name, types.SimpleNamespace(
            validate=lambda *a, **k: calls.append('validate')))
    monkeypatch.setattr(re_validate, 'pdsdependency', types.SimpleNamespace(
        test=lambda *a, **k: calls.append('dependency')))

    def add_tarballs():
        """Create one archive tarball per volume type, as a real holdings tree has.

        Without these, glob.glob returns [] in both `archives-` loops and the two
        message sites inside them are never reached.
        """

        for voltype in re_validate.ALL_VOLTYPES:
            directory = holdings / ('archives-' + voltype) / 'VS_1xxx'
            directory.mkdir(parents=True, exist_ok=True)
            (directory / 'VOL_0001.tar.gz').write_bytes(b'')

    return types.SimpleNamespace(
        pdsdir=StubPdsdir(str(holdings / 'volumes' / 'VS_1xxx' / 'VOL_0001')),
        holdings=holdings, logfiles=logfiles, calls=calls,
        add_tarballs=add_tarballs, log_path_kwargs=log_path_kwargs)


def run_one_volume(volume_tree, logger, **flags):
    """Run validate_one_volume over the tree with every test enabled by default."""

    args = Namespace(checksums=True, archives=True, infoshelves=True,
                     linkshelves=True, dependencies=True, timeless=False)
    args.__dict__.update(flags)

    return re_validate.validate_one_volume(volume_tree.pdsdir,
                                           list(re_validate.ALL_VOLTYPES),
                                           ['checksums'], args, logger)


def test_the_dependency_line_names_the_volume(volume_tree):
    """The dependency test is logged against the volume it is about.

    It used to log a bare `abspath` left over from an earlier per-voltype loop. In
    the common case -- no archive tarballs present -- that was the empty list
    glob.glob had just returned, and PdsLogger renders a falsy filepath as no path
    at all, so the line named nothing.
    """

    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    dependency = [o for o in logger.opens if 'ependency re-validation' in o[0]]

    assert dependency == [('Dependency re-validation for',
                           volume_tree.pdsdir.abspath)]


def test_the_timeless_dependency_line_names_the_volume(volume_tree):
    """The --timeless wording is logged against the volume too."""

    logger = StubLogger()
    run_one_volume(volume_tree, logger, timeless=True)

    dependency = [o for o in logger.opens if 'ependency re-validation' in o[0]]

    assert dependency == [('Timeless dependency re-validation for',
                           volume_tree.pdsdir.abspath)]


def test_the_archive_checksum_block_runs(volume_tree):
    """The per-archive checksum pass reads the parsed command line, not a global.

    `if checksums and args.archives` read a module global that only existed
    because the whole program ran at import. Under a main() the name is a local of
    main(), so the read raises NameError -- and the bare `except Exception` around
    this loop swallows it, so the block would simply have stopped running with
    nothing but a logged traceback to show for it.
    """

    archives = volume_tree.holdings / 'archives-volumes' / 'VS_1xxx'
    archives.mkdir(parents=True)
    (archives / 'VOL_0001.tar.gz').write_bytes(b'')

    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    assert logger.exceptions == []
    assert ('Checksum re-validation for',
            str(archives / 'VOL_0001.tar.gz')) in logger.opens


# The six log messages that carried the misspelling. All six must be reachable in
# one run, or a test that asserts over "every message logged" silently covers fewer
# sites than it claims.
MISSPELLED_SITES = ['Checksum re-validation for',      # per volume type
                    'Archive re-validation for',       # per volume type
                    'Infoshelf re-validation for',     # per volume type
                    'Linkshelf re-validation for',     # per volume type
                    'Checksum re-validation for',      # per archive tarball
                    'Infoshelf re-validation for']     # per archive tarball


def test_no_log_message_misspells_re_validation(volume_tree):
    """No log message says "re-validatation", at any of the six sites that did.

    The two sites inside the `archives-` loops are only reached when a tarball is
    there to be found, so this test builds them. Without that, `glob.glob` returns
    [] and an assertion over "every message logged" would cover four sites while
    appearing to cover six.
    """

    volume_tree.add_tarballs()
    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    messages = [o[0] for o in logger.opens]
    tarball = str(volume_tree.holdings
                  / 'archives-volumes' / 'VS_1xxx' / 'VOL_0001.tar.gz')

    assert not [m for m in messages if 're-validatation' in m]
    for site in set(MISSPELLED_SITES):
        assert site in messages, site
    # Both of the tarball sites were reached, which is what makes the loop above
    # an assertion about six sites rather than four.
    assert ('Checksum re-validation for', tarball) in logger.opens
    assert ('Infoshelf re-validation for', tarball) in logger.opens


def test_every_per_voltype_line_names_its_own_directory(volume_tree):
    """Each per-volume-type message names the directory that test ran against."""

    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    def directory(voltype):
        return str(volume_tree.holdings / voltype / 'VS_1xxx' / 'VOL_0001')

    for voltype in re_validate.ALL_VOLTYPES:
        assert ('Checksum re-validation for', directory(voltype)) in logger.opens
        assert ('Archive re-validation for', directory(voltype)) in logger.opens
        assert ('Infoshelf re-validation for', directory(voltype)) in logger.opens

    # A link shelf exists for three of the five trees. Asserting on each of the
    # three separately is what makes this more than a check that the volumes path
    # appears: that one is also pdsdir.abspath, so it would still be there if every
    # line named the volume instead of its own directory.
    for voltype in re_validate.LINKSHELF_VOLTYPES:
        assert ('Linkshelf re-validation for', directory(voltype)) in logger.opens
    for voltype in ('diagrams', 'previews'):
        assert ('Linkshelf re-validation for', directory(voltype)) not in logger.opens


def test_the_log_is_written_under_the_tool_subdirectory(volume_tree):
    """The per-volume log goes to the tool's own log subdirectory."""

    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    assert volume_tree.log_path_kwargs['method'] == 'log_path_for_volume'
    assert volume_tree.log_path_kwargs['args'] == ('_re-validate',)
    assert volume_tree.log_path_kwargs['kwargs'] == {'dir': 're-validate'}


def test_the_fatal_and_error_counts_are_returned_in_that_order(volume_tree):
    """The return is (log path, fatal, errors), and batch mode reads it that way."""

    logger = StubLogger(close_result=(7, 5, 3, 1))
    (_log_path, fatal, errors) = run_one_volume(volume_tree, logger)

    assert (fatal, errors) == (7, 5)


def test_the_returned_log_path_is_the_last_one_written(volume_tree):
    """The returned path is the last log path, with the '/volumes/' level dropped.

    Batch mode prints it in its error messages. It used to be a loop variable that
    leaked out of the handler loop; it is now taken from the list explicitly, and
    the value is deliberately unchanged.
    """

    logger = StubLogger()
    (log_path, fatal, errors) = run_one_volume(volume_tree, logger)

    assert log_path == volume_tree.logfiles[-1].replace('/volumes/', '/')
    assert (fatal, errors) == (0, 0)
    assert log_path != volume_tree.logfiles[0].replace('/volumes/', '/')


def test_a_test_count_is_logged(volume_tree):
    """The closing line counts the tests that ran, against the volume."""

    logger = StubLogger()
    run_one_volume(volume_tree, logger)

    counts = [i for i in logger.infos if 're-validation test' in i[0]]

    assert len(counts) == 1
    assert counts[0][1] == volume_tree.pdsdir.abspath


##########################################################################################
# The email report
##########################################################################################

def test_format_email_accepts_one_address_as_a_string():
    """A single recipient may be given as a bare string."""

    (recipients, msg) = format_message('pds@example.org')

    assert recipients == ['pds@example.org']
    assert 'To: pds@example.org\n' in msg


def test_format_email_accepts_a_string_subclass():
    """A str subclass is still one address, not an iterable of characters.

    The type was compared with `==` against str, so anything that merely inherits
    from str fell through to the list branch and was split into its characters.
    """

    class Address(str):
        pass

    (recipients, _msg) = format_message(Address('pds@example.org'))

    assert recipients == ['pds@example.org']


def test_format_email_accepts_a_list_of_addresses():
    """Several recipients are joined into one To header and all are returned."""

    (recipients, msg) = format_message(['a@example.org', 'b@example.org'])

    assert recipients == ['a@example.org', 'b@example.org']
    assert 'To: a@example.org,b@example.org\n' in msg


def test_format_email_builds_the_expected_headers():
    """The message carries the four headers, then a blank line, then the body."""

    (_recipients, msg) = format_message('pds@example.org')

    assert msg == ('From: ' + re_validate.FROM_ADDR + '\n'
                   'To: pds@example.org\n'
                   'Subject: a subject\n'
                   'Date: 01/01/2026 00:00:00\n'
                   '\n'
                   'a body')


def format_message(to_addr):
    """Call format_email with fixed subject, body and date."""

    return re_validate.format_email(to_addr, 'a subject', 'a body',
                                    date='01/01/2026 00:00:00')


##########################################################################################
# Exit codes
##########################################################################################

def test_interactive_mode_with_no_path_exits_1(capsys):
    """Naming no volume is an error, reported before anything is logged."""

    with pytest.raises(SystemExit) as exc:
        re_validate.run_interactive(Namespace(volume=[]), [], [], None, ['x'])

    assert exc.value.code == 1
    assert capsys.readouterr().out == 'Missing volume path\n'


def test_interactive_mode_with_a_missing_path_exits_1(capsys):
    """A volume path that does not exist is an error."""

    with pytest.raises(SystemExit) as exc:
        re_validate.run_interactive(Namespace(volume=['/no/such/volume']), [], [],
                                    None, ['x'])

    assert exc.value.code == 1
    assert capsys.readouterr().out == 'Volume path not found: /no/such/volume\n'


def test_batch_mode_with_no_path_exits_1(capsys):
    """Naming no holdings directory is an error."""

    with pytest.raises(SystemExit) as exc:
        re_validate.resolve_holdings_paths([])

    assert exc.value.code == 1
    assert capsys.readouterr().out == 'No holdings path identified\n'


def test_batch_mode_with_a_missing_path_exits_1(capsys):
    """A holdings path that does not exist is an error."""

    with pytest.raises(SystemExit) as exc:
        re_validate.resolve_holdings_paths(['/no/such/holdings'])

    assert exc.value.code == 1
    assert capsys.readouterr().out == 'Holdings path not found: /no/such/holdings\n'


def test_batch_mode_with_a_non_holdings_path_exits_1(tmp_path, capsys):
    """A directory that is not named "holdings" is an error."""

    with pytest.raises(SystemExit) as exc:
        re_validate.resolve_holdings_paths([str(tmp_path)])

    assert exc.value.code == 1
    assert capsys.readouterr().out.startswith('Not a holdings directory: ')


def test_batch_mode_accepts_a_holdings_path_once(tmp_path):
    """The same holdings root named twice is resolved to one absolute path."""

    holdings = tmp_path / 'holdings'
    holdings.mkdir()

    resolved = re_validate.resolve_holdings_paths([str(holdings),
                                                   str(holdings) + '/'])

    assert resolved == [os.path.realpath(str(holdings))]


def test_batch_status_exits_0(capsys):
    """--batch-status stops after printing, with a success status."""

    with pytest.raises(SystemExit) as exc:
        re_validate.print_batch_status([], [])

    # sys.exit() with no argument, whose code is None and whose status is 0.
    assert exc.value.code is None
    assert capsys.readouterr().out == ''


def test_interactive_mode_exits_1_after_an_error(tmp_path, monkeypatch):
    """Interactive mode reports failure when the run logged a fatal or an error.

    This is the branch batch mode deliberately does not share: there, the status is
    0 whatever was logged.
    """

    volume = tmp_path / 'holdings' / 'volumes' / 'VS_1xxx' / 'VOL_0001'
    volume.mkdir(parents=True)
    pdsdir = StubPdsdir(str(volume))
    pdsdir.category_ = 'volumes/'
    pdsdir.interior = ''

    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(from_abspath=lambda p: pdsdir)))
    monkeypatch.setattr(re_validate, 'validate_one_volume',
                        lambda *a, **k: ('/logs/x.log', 0, 0))

    # (fatal, errors, warnings, tests) -- one error and no fatal is enough.
    logger = StubBatchLogger(close_result=(0, 1, 0, 0))

    with pytest.raises(SystemExit) as exc:
        re_validate.run_interactive(Namespace(volume=[str(volume)]), ['volumes'],
                                    ['checksums'], logger, ['re_validate.py'])

    assert exc.value.code == 1


def test_batch_mode_exits_0_even_after_a_fatal(tmp_path, monkeypatch, capsys):
    """Batch mode reports success whatever the run logged.

    A nonzero status would cancel the launch daemon that schedules the run, so the
    exit is 0 even when a volume logged a fatal. This is the deliberate choice the
    commented-out `sys.exit(status)` used to sit beside.
    """

    holdings = tmp_path / 'holdings'
    (holdings / 'volumes' / 'VS_1xxx' / 'VOL_0001').mkdir(parents=True)

    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(from_abspath=StubPdsdir)))
    monkeypatch.setattr(re_validate, 'get_volume_info',
                        lambda h: [(str(holdings / 'volumes/VS_1xxx/VOL_0001'), 'x')])
    # One fatal and one error, which in interactive mode would make the status 1.
    monkeypatch.setattr(re_validate, 'validate_one_volume',
                        lambda *a, **k: ('/logs/VOL_0001.log', 1, 1))

    args = Namespace(volume=[str(holdings)], log=str(tmp_path / 'logs'),
                     batch_status=False, minutes=60, email=[], error_email=[])

    with pytest.raises(SystemExit) as exc:
        re_validate.run_batch(args, ['volumes'], ['checksums'], StubBatchLogger(),
                              ['re_validate.py', '--batch', str(holdings)])

    assert exc.value.code == 0
    assert '***** Fatal = 1; Errors = 1; /logs/VOL_0001.log' in capsys.readouterr().out


def test_main_uses_the_argv_it_is_given(monkeypatch):
    """main(argv) parses that argv and hands the same list to the mode it selects.

    Everything main() reaches outside itself is replaced, so this test builds no
    logger and sets no log root on the real PdsFile class.
    """

    seen = {}
    monkeypatch.setattr(re_validate.pdslogger, 'PdsLogger',
                        lambda *a, **k: StubBatchLogger())
    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(
            set_log_root=lambda root: seen.__setitem__('log_root', root))))
    monkeypatch.setattr(re_validate, 'run_interactive',
                        lambda args, voltypes, tests, logger, argv:
                        seen.update(args=args, voltypes=voltypes, tests=tests,
                                    argv=argv))
    monkeypatch.delenv(re_validate._common.LOGROOT_ENV, raising=False)

    argv = ['re_validate.py', '--quiet', '--previews', '/some/volume']
    re_validate.main(argv)

    assert seen['argv'] is argv
    assert seen['args'].volume == ['/some/volume']
    assert seen['args'].quiet is True
    assert seen['voltypes'] == ['previews']
    assert seen['log_root'] is None


def test_main_defaults_to_sys_argv(monkeypatch):
    """With no argument, main() reads sys.argv."""

    seen = {}
    monkeypatch.setattr(re_validate.pdslogger, 'PdsLogger',
                        lambda *a, **k: StubBatchLogger())
    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(set_log_root=lambda root: None)))
    monkeypatch.setattr(re_validate, 'run_batch',
                        lambda args, voltypes, tests, logger, argv:
                        seen.update(argv=argv))
    monkeypatch.delenv(re_validate._common.LOGROOT_ENV, raising=False)
    monkeypatch.setattr(sys, 'argv', ['re_validate.py', '--batch-status', '/h'])

    re_validate.main()

    assert seen['argv'] == ['re_validate.py', '--batch-status', '/h']


def test_main_adds_a_terminal_handler_unless_quiet(monkeypatch, tmp_path):
    """Without --quiet the run logs to the terminal; with it, it does not."""

    def run(*flags):
        logger = StubBatchLogger()
        monkeypatch.setattr(re_validate.pdslogger, 'PdsLogger',
                            lambda *a, **k: logger)
        monkeypatch.setattr(re_validate.pdslogger, 'stdout_handler', 'STDOUT')
        monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
            Pds3File=types.SimpleNamespace(set_log_root=lambda root: None)))
        monkeypatch.setattr(re_validate, 'run_interactive',
                            lambda *a, **k: None)
        monkeypatch.delenv(re_validate._common.LOGROOT_ENV, raising=False)
        re_validate.main(['re_validate.py', *flags, '/some/volume'])
        return logger.handlers

    assert 'STDOUT' in run()
    assert 'STDOUT' not in run('--quiet')


def test_main_adds_an_error_handler_under_the_tool_subdirectory(monkeypatch,
                                                                tmp_path):
    """With a log root, the run's error log goes to <root>/re-validate."""

    logger = StubBatchLogger()
    monkeypatch.setattr(re_validate.pdslogger, 'PdsLogger', lambda *a, **k: logger)
    monkeypatch.setattr(re_validate.pdslogger, 'error_handler',
                        lambda directory: ('error_handler', directory))
    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(set_log_root=lambda root: None)))
    monkeypatch.setattr(re_validate, 'run_interactive', lambda *a, **k: None)

    re_validate.main(['re_validate.py', '--quiet', '--log', str(tmp_path),
                      '/some/volume'])

    assert ('error_handler', os.path.join(str(tmp_path), 're-validate')) \
        in logger.handlers


def test_main_takes_the_log_root_from_the_environment(monkeypatch, tmp_path):
    """An unset --log falls back to the environment variable."""

    seen = {}
    monkeypatch.setattr(re_validate.pdslogger, 'PdsLogger',
                        lambda *a, **k: StubBatchLogger())
    monkeypatch.setattr(re_validate.pdslogger, 'error_handler', lambda d: ('err', d))
    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(
            set_log_root=lambda root: seen.__setitem__('log_root', root))))
    monkeypatch.setattr(re_validate, 'run_interactive', lambda *a, **k: None)
    monkeypatch.setenv(re_validate._common.LOGROOT_ENV, str(tmp_path))

    re_validate.main(['re_validate.py', '--quiet', '/some/volume'])

    assert seen['log_root'] == str(tmp_path)


def test_interactive_mode_logs_the_command_line_it_was_given(monkeypatch,
                                                             tmp_path):
    """The run's log opens with the command line, taken from argv, not sys.argv."""

    volume = tmp_path / 'holdings' / 'volumes' / 'VS_1xxx' / 'VOL_0001'
    volume.mkdir(parents=True)
    pdsdir = StubPdsdir(str(volume))
    pdsdir.category_ = 'volumes/'
    pdsdir.interior = ''

    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(from_abspath=lambda p: pdsdir)))
    monkeypatch.setattr(re_validate, 'validate_one_volume',
                        lambda *a, **k: ('/logs/x.log', 0, 0))
    monkeypatch.setattr(sys, 'argv', ['SYS_ARGV_MUST_NOT_BE_READ'])

    logger = StubBatchLogger()
    argv = ['re_validate.py', '--checksums', str(volume)]

    with pytest.raises(SystemExit) as exc:
        re_validate.run_interactive(Namespace(volume=[str(volume)]), ['volumes'],
                                    ['checksums'], logger, argv)

    assert exc.value.code == 0
    assert (' '.join(argv), None) in logger.opens
    assert not [o for o in logger.opens if 'SYS_ARGV_MUST_NOT_BE_READ' in o[0]]


def test_batch_mode_logs_the_command_line_it_was_given(tmp_path, monkeypatch):
    """Batch mode opens its log with the command line it was given too."""

    holdings = tmp_path / 'holdings'
    (holdings / 'volumes' / 'VS_1xxx' / 'VOL_0001').mkdir(parents=True)

    monkeypatch.setattr(re_validate, 'pdsfile', types.SimpleNamespace(
        Pds3File=types.SimpleNamespace(from_abspath=StubPdsdir)))
    monkeypatch.setattr(re_validate, 'get_volume_info', lambda h: [])
    monkeypatch.setattr(sys, 'argv', ['SYS_ARGV_MUST_NOT_BE_READ'])

    logger = StubBatchLogger()
    argv = ['re_validate.py', '--batch', str(holdings)]
    args = Namespace(volume=[str(holdings)], log=str(tmp_path / 'logs'),
                     batch_status=False, minutes=60, email=[], error_email=[])

    with pytest.raises(SystemExit):
        re_validate.run_batch(args, ['volumes'], ['checksums'], logger, argv)

    assert (' '.join(argv), None) in logger.opens
    assert not [o for o in logger.opens if 'SYS_ARGV_MUST_NOT_BE_READ' in o[0]]


##########################################################################################
# The shared log-root helper this tool put into _common
##########################################################################################

def test_resolve_log_root_keeps_an_explicit_path():
    """A --log path given on the command line is left alone."""

    args = Namespace(log='/explicit/root')
    re_validate._common.resolve_log_root(args)

    assert args.log == '/explicit/root'


def test_resolve_log_root_falls_back_to_the_environment(monkeypatch):
    """An unset --log takes the environment variable's value."""

    monkeypatch.setenv(re_validate._common.LOGROOT_ENV, '/from/env')
    args = Namespace(log='')
    re_validate._common.resolve_log_root(args)

    assert args.log == '/from/env'


def test_resolve_log_root_is_none_when_nothing_is_set(monkeypatch):
    """With neither --log nor the variable, there is no duplicate log tree."""

    monkeypatch.delenv(re_validate._common.LOGROOT_ENV, raising=False)
    args = Namespace(log='')
    re_validate._common.resolve_log_root(args)

    assert args.log is None


##########################################################################################
# The whole program, through `python -m`
##########################################################################################

def test_the_program_exits_1_with_no_arguments():
    """The whole program, run as `python -m`, refuses an empty command line."""

    done = run_module()

    assert done.returncode == 1
    assert done.stdout.strip() == 'Missing volume path'


def test_the_program_exits_1_in_batch_mode_with_no_holdings():
    """The whole program, run as `python -m`, refuses batch mode with no path."""

    done = run_module('--batch')

    assert done.returncode == 1
    assert done.stdout.strip() == 'No holdings path identified'


def test_the_program_reports_its_own_usage():
    """--help succeeds and names every flag the tool accepts."""

    done = run_module('--help')

    assert done.returncode == 0
    for flag in ('--batch-status', '--error-email', '--timeless', '--previews',
                 '--minutes', '--quiet', '--log'):
        assert flag in done.stdout, flag
