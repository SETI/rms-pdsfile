#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/re_validate.py
################################################################################

"""Re-run five of the PDS3 maintenance validations over whole volumes.

The tools this package installs each validate one kind of derived file. This one is the
scheduler over five of them: for a volume it runs the checksum, archive, info shelf,
link shelf and dependency validations in turn, writes one log per volume covering all
five, and reports how many tests it performed. It fixes nothing -- every task it calls
is a validation, and a failure is logged rather than repaired.

**Five is not all of them.** ``pdsindexshelf`` offers a validate task under the same name
as the four it does call, and this tool neither imports nor runs it, so the index shelves
of a volume's metadata tables are never re-validated here. One more check in this
package goes unrun for a different reason, having no task to call: ``crlf``, which
checks the line terminators of text files.

Run it as::

    python -m pdsfile.holdings_maintenance.pds3.re_validate path [path ...]

Two modes share that command line.

**Interactive mode** is the default. Each path names a volume, or a volume set that is
expanded into its volumes, and every one named is validated before the run exits. The
status is 1 if a path is unusable, or if the run logged a fatal or an error, and 0
otherwise.

**Batch mode**, selected by ``--batch``, takes holdings roots rather than volumes. It
reads the logs of previous runs, works out which volumes have changed since they were
last validated and which have gone longest without one, and validates them in that
order until ``--minutes`` is up. It then mails a report to each ``--email`` address, and
an error-only report to each ``--error-email`` address if anything failed. **Its exit
status is 0 even when the run logged errors**, because a nonzero status would cancel the
launch daemon that schedules it. That holds for anything a validation finds and not for
everything: the mail is sent from the same block that would exit 0, so a mail relay that
cannot be reached ends the run in the exception instead. ``--batch-status`` prints the
same schedule without validating anything.

Which trees are examined is chosen by the five volume-type flags -- ``--volumes``,
``--calibrated``, ``--diagrams``, ``--metadata`` and ``--previews`` -- and which tests
are run by the five test flags -- ``--checksums``, ``--archives``, ``--info``,
``--links`` and ``--dependencies``. Naming none of a group selects all of it, and so
does the group's own ``--all`` or ``--full``. Two tests are then narrowed to the trees
they can run against: link shelves exist only for volumes, calibrated and metadata, and
the dependency test only makes sense over volumes.

Every volume gets its own log file, in the ``re-validate`` subdirectory of a "logs"
directory beside its holdings tree and, when a log root is configured, in the same
subdirectory under that root as well. The volume's category component is dropped from
the path, so a volume's logs sit directly under a directory named for its volume set;
that is the shape batch mode reads a volume set and a volume name back out of.

Batch mode's schedule comes from two places and no third. It walks the log root -- the
one place, not the directories beside the holdings trees -- for the record of what has
been validated, and it globs each holdings tree for the volumes that exist and the date
each carries. What to do next is those two compared: a volume whose current date is not
one the logs recorded goes first, and the rest follow oldest validation first. There is
no state file and no database. So a batch run against a log root holding no logs treats
every volume the glob found as never validated, and a batch run with no log root at all
has nothing to walk and ends in a TypeError.

Nothing here is specific to one dataset. The tests are the other tools' own, called as
library functions rather than as subprocesses, so a change in what one of them validates
changes what this reports without any change here.
"""

import argparse
import datetime
import glob
import os
import socket
import sys
from smtplib import SMTP

import pdslogger

import pdsfile
from pdsfile.holdings_maintenance import _common
from pdsfile.holdings_maintenance.pds3 import (
    pdsarchives,
    pdschecksums,
    pdsdependency,
    pdsinfoshelf,
    pdslinkshelf,
)

LOGNAME = 'pds.validation'

# Read nowhere in this module. Whether it should exist at all is a question for
# whoever owns the batch report, not a cleanup.
MAX_INFO = 50

# The tool's name: the subdirectory of each log root, and the name in --help.
PROGNAME = 're-validate'

# Every volume type this tool knows how to check, in the order it checks them.
ALL_VOLTYPES = ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews']

# The volume types a link shelf exists for.
LINKSHELF_VOLTYPES = ('volumes', 'calibrated', 'metadata')

SERVER = 'list.seti.org'
FROM_ADDR = "PDS Administrator <pds-admin@seti.org>"
REPORT_SUBJ = "Re-validate report from " + socket.gethostname()
REPORT_SUBJ_W_ERRORS = "Re-validate report with ERRORs from " + \
                                              socket.gethostname()
ERROR_REPORT_SUBJ = "Re-validate ERROR report from " + socket.gethostname()

# Default limits
CHECKSUMS_LIMITS  = {'info': 20, 'debug': 10}
ARCHIVES_LIMITS   = {'info': 20, 'debug': 10}
INFOSHELF_LIMITS  = {'info': 20, 'debug': 10}
LINKSHELF_LIMITS  = {'info': 20, 'debug': 10}
DEPENDENCY_LIMITS = {'info': 20, 'debug': 10}

################################################################################
# Function to validate one volume
################################################################################

def validate_one_volume(pdsdir, voltypes, tests, args, logger):
    """Run every selected test over one volume, into a log file of that volume's own.

    The tests are run in a fixed order that is not the order the command line lists
    them in: for each volume type, the checksum and archive validations; then the
    checksums of the archive files themselves; then, for each volume type again, the
    info shelf and link shelf validations; then the info shelves of the archive files;
    then the dependency check. So a volume type's directory is visited twice, and the
    archive tests are grouped by what they read rather than by the type they belong to.

    Which of them actually run depends on what the parsed command line carries, and two
    of the groups need two flags rather than one: the checksums of the archive files
    require both ``--checksums`` and ``--archives``, and their info shelves require both
    ``--info`` and ``--archives``. A volume type whose directory does not exist is
    skipped without a test being counted, and an archive group finding no ``.tar.gz``
    is skipped the same way; where more than one archive file matches, the first the
    glob returns is the one validated.

    Nothing an ordinary test failure does stops a run. Every test is closed in a
    ``finally``, so a test that raises still counts as performed, and the exception is
    logged and swallowed rather than propagated -- a batch run moves on to the next
    volume, and the caller sees the failure only as a fatal in the returned counts.
    What is caught is ``Exception``, so anything outside it, KeyboardInterrupt included,
    escapes with the volume's log already closed. **A test that raises skips every
    remaining test of the volume**, not just the rest of its own group: the handler is
    around the whole sequence rather than around each test. How much is lost depends on
    the volume, since the number of tests it runs is three per volume-type directory that
    exists, two per archive group that found a tarball, one per link-shelf type present
    and one for the dependency check; a failure on the first test loses all but one of
    them, and the count reported is 1.

    Parameters:
        pdsdir: The volume directory, which must be under ``volumes/``. The paths of
            the other volume types are built from its absolute path by substituting the
            category component.
        voltypes (list): The volume types to visit, as derived by ``derive_options()``.
        tests (list): The names of the selected tests. Written into the log header and
            not otherwise read; which tests run is decided by the attributes of
            ``args``.
        args (argparse.Namespace): The parsed command line after ``derive_options()``,
            read for its five test attributes and for ``timeless``.
        logger: The run's logger. One file handler and one error handler are built and
            attached per log path, so a run with a log root configured attaches four
            handlers and the two error handlers point at two different directories. All
            of them are attached for the duration of this call and removed when it
            returns.

    Returns:
        tuple: (log path, fatal count, error count). The log path is the last of the one
        or two written, and that is always the copy beside the holdings tree, whether or
        not a log root is configured: the log-root copy is built first and this is the
        other one. It is the path a batch run puts in its error mail. The two counts are
        read from the close of the volume's log, so they cover every test the volume ran
        and nothing outside it.

    Raises:
        KeyboardInterrupt: from any of the ``validate()`` calls, which the handler here
            does not cover; the volume's log is closed on the way out and the interrupt
            reaches the caller. Nothing an ordinary test raises escapes, because
            everything covered by Exception is logged and swallowed.
        ValueError: from ``from_abspath()``, for a volume type whose substituted path is
            outside every holdings tree the environment knows.
    """

    tests_performed = 0

    # Open logger for this volume
    logfiles = _common.log_paths_for(pdsdir, 'log_path_for_volume', '_re-validate',
                                     dir=PROGNAME)
    logfiles = [f.replace('/volumes/','/') for f in logfiles]  # this subdir not needed

    local_handlers = []
    for logfile in logfiles:
        local_handlers.append(pdslogger.file_handler(logfile))
        logdir = os.path.split(logfile)[0]
        logdir = os.path.split(logdir)[0]

        # These handlers are only used if they don't already exist
        error_handler = pdslogger.error_handler(logdir)
        local_handlers.append(error_handler)

    logger.blankline()
    logger.open('Re-validate ' + pdsdir.abspath, handler=local_handlers)
    try:

        logger.info('Last modification', pdsdir.date)
        logger.info('Volume types', str(voltypes)[1:-1].replace("'",""))
        logger.info('Tests', str(tests)[1:-1].replace("'",""))
        logger.blankline()

        # Checksums and archives for each voltype...
        for voltype in voltypes:
            abspath = pdsdir.abspath.replace('/volumes/',
                                             '/' + voltype + '/')
            if not os.path.exists(abspath):
                continue

            temp_pdsdir = pdsfile.Pds3File.from_abspath(abspath)
            if args.checksums:
                logger.open('Checksum re-validation for', abspath)
                try:
                    pdschecksums.validate(temp_pdsdir,
                                          limits=CHECKSUMS_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

            if args.archives:
                logger.open('Archive re-validation for', abspath)
                try:
                    pdsarchives.validate(temp_pdsdir,
                                         limits=ARCHIVES_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

        # Checksums for each 'archive-' + voltype...
        if args.checksums and args.archives:
            for voltype in voltypes:
                abspath = pdsdir.abspath.replace('/volumes/',
                                                 '/archives-' + voltype + '/')
                abspath += '*.tar.gz'
                tarpaths = glob.glob(abspath)
                if not tarpaths:
                    continue

                abspath = tarpaths[0]   # there should only be one

                (prefix, basename) = os.path.split(abspath)
                temp_pdsdir = pdsfile.Pds3File.from_abspath(prefix)
                logger.open('Checksum re-validation for', abspath)
                try:
                    pdschecksums.validate(temp_pdsdir, basename,
                                          limits=CHECKSUMS_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

        # Infoshelves and linkshelves for each voltype...
        for voltype in voltypes:
            abspath = pdsdir.abspath.replace('/volumes/',
                                             '/' + voltype + '/')
            if not os.path.exists(abspath):
                continue

            temp_pdsdir = pdsfile.Pds3File.from_abspath(abspath)
            if args.infoshelves:
                logger.open('Infoshelf re-validation for', abspath)
                try:
                    pdsinfoshelf.validate(temp_pdsdir,
                                          limits=INFOSHELF_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

            if args.linkshelves and voltype in LINKSHELF_VOLTYPES:
                logger.open('Linkshelf re-validation for', abspath)
                try:
                    pdslinkshelf.validate(temp_pdsdir,
                                          limits=LINKSHELF_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

        # Infoshelves for each 'archive-' + voltype...
        if args.infoshelves and args.archives:
            for voltype in voltypes:
                abspath = pdsdir.abspath.replace('/volumes/',
                                                 '/archives-' + voltype + '/')
                abspath += '*.tar.gz'
                tarpaths = glob.glob(abspath)
                if not tarpaths:
                    continue

                abspath = tarpaths[0]   # there should only be one

                (prefix, basename) = os.path.split(abspath)
                temp_pdsdir = pdsfile.Pds3File.from_abspath(prefix)
                logger.open('Infoshelf re-validation for', abspath)
                try:
                    pdsinfoshelf.validate(temp_pdsdir, basename,
                                          limits=INFOSHELF_LIMITS)
                finally:
                    tests_performed += 1
                    logger.close()

        # Dependencies
        if args.dependencies:
            if args.timeless:
                logger.open('Timeless dependency re-validation for',
                            pdsdir.abspath)
            else:
                logger.open('Dependency re-validation for', pdsdir.abspath)
            try:
                pdsdependency.test(pdsdir, limits=DEPENDENCY_LIMITS,
                                   check_newer=(not args.timeless))
            finally:
                tests_performed += 1
                logger.close()

    except Exception as e:
        logger.exception(e)

    finally:
        if tests_performed == 1:
            logger.info('1 re-validation test performed', pdsdir.abspath,
                        force=True)
        else:
            logger.info('%d re-validation tests performed' % tests_performed,
                        pdsdir.abspath, force=True)
        (fatal, errors, _warnings, _tests) = logger.close()

    return (logfiles[-1], fatal, errors)

################################################################################
# Log and volume management for batch mode
################################################################################

def volume_abspath_from_log(log_path):
    """Return the volume path a validation log says it is about.

    The path is recovered from the log's first record, whose text is the volume's
    absolute path preceded by a fixed phrase. The record is split on the pipe that
    separates a pdslogger record's fields, the last field is taken, and its last
    space-separated token is the answer. **A holdings root whose path contains a space
    is therefore truncated to whatever follows its last space**, because the record
    carries no quoting to recover the path by.

    Parameters:
        log_path (str): The log file to read. Only its first line is read.

    Returns:
        str: The volume's absolute path, or the empty string for a log file that is
        empty, which is what an interrupted run can leave behind.

    Raises:
        OSError: from the ``open()`` of a log file that does not exist or cannot be
            read.
        UnicodeDecodeError: from the ``readline()`` of a log that is not valid UTF-8.
            The only caller does not catch it, so one corrupt log ends the report. The
            same file is survivable through ``get_log_info()``, whose caller catches
            ValueError and this is a subclass of it.
    """

    with open(log_path) as f:
        rec = f.readline()

    parts = rec.split('|')
    return parts[-1].strip().split(' ')[-1]


def key_from_volume_abspath(abspath):
    """Return the volume set and volume name a volume path ends in, as one key.

    This is the key batch mode organizes everything by: it identifies a volume without
    saying which holdings tree the volume is in, which is what lets a log written
    against one tree be matched against the same volume in another.

    Parameters:
        abspath (str): A volume's absolute path. Only its last two components are read,
            and neither is checked, so a path that is not a volume path yields a key
            just the same.

    Returns:
        str: The last two components joined by a slash. A path with fewer than two
        components yields what it has.
    """

    parts = abspath.split('/')
    return '/'.join(parts[-2:])


def key_from_log_path(log_path):
    """Return the same volume set and volume name key, from a log file's path instead.

    A log file's name is the volume name followed by ``_re-validate_`` and a time tag,
    and its directory is named for the volume set, because the category component is
    dropped when the log path is built. So the key can be read off the path without
    opening the file.

    This is the arithmetic ``get_all_log_info()`` performs inline when it groups the
    logs it finds. Nothing in this module calls this function; it is the public form of
    that step, and it is what the tests hold the grouping to.

    Parameters:
        log_path (str): A log file's path, or any path of the same shape. Neither the
            directory nor the basename is checked.

    Returns:
        str: The parent directory's name and the part of the basename before
        ``_re-validate_``, joined by a slash. A basename without that marker yields the
        whole basename, since the split leaves it in the first element.
    """

    parts = log_path.split('/')
    bundlename = parts[-1].split('_re-validate_')[0]

    return parts[-2] + '/' + bundlename


def get_log_info(log_path):
    """Summarize one validation log, reading the whole of it.

    Four things are read from fixed positions: the start time and the logger name from
    the first record, the volume path from the end of that same record, and the
    volume's modification time from the second. The rest is a scan for three markers, of
    which only two can ever be found. The last elapsed time in the file wins, so a log
    holding several is summarized by its final one.

    **The fatal marker is a string no log this tool writes contains.** The scan looks for
    ``| FATAL |``, and pdslogger renders a fatal record as ``| CRITICAL |`` and a logged
    exception as ``| EXCEPTION |``; "fatal" is a level alias and not a rendered name. So
    the fatal flag is true exactly when there is no elapsed time, which is the state an
    interrupted or still-running validation leaves, and a validation whose every test
    raised writes a log that reads back here as neither fatal nor in error. Only the
    error scan is unaffected, and it too misses a run that failed by exception rather
    than by logging an error.

    Parameters:
        log_path (str): The log file to read.

    Returns:
        tuple: (start time, elapsed time, volume modification time, volume absolute
        path, whether an error was logged, whether the log counts as fatal). The three
        times are the strings the log carries, not parsed values.

    Raises:
        ValueError: for a file this cannot summarize -- one that is empty or whose
            first record has no field separator, one whose first record names a
            different logger, one with only a single record, and one whose second
            record is not the modification time. Three messages cover those four cases,
            so a log naming another logger and a log with one record cannot be told
            apart; every caller here treats them alike in any event. A fifth case carries
            no message of this function's at all: a log that is not valid UTF-8 raises
            ``UnicodeDecodeError``, which is a subclass of this and reaches the same
            handlers.
        OSError: from the ``open()`` of a log file that does not exist or cannot be
            read.
    """

    with open(log_path) as f:
        recs = f.readlines()

    if not recs:
        raise ValueError('Empty log file: ' + log_path)

    parts = recs[0].split('|')
    if len(parts) < 2:
        raise ValueError('Empty log file: ' + log_path)

    start_time = parts[0].rstrip()
    if parts[1].strip() != LOGNAME:
        raise ValueError('Not a re-validate log file')

    abspath = parts[-1].strip().split(' ')[-1]

    if len(recs) < 2:
        raise ValueError('Not a re-validate log file')

    if 'Last modification' not in recs[1]:
        raise ValueError('Missing modification time')

    modtime = recs[1].split('modification:')[-1].strip()

    error = False
    fatal = False
    elapsed = None
    for rec in recs:
        error |= ('| ERROR |' in rec)
        fatal |= ('| FATAL |' in rec)

        k = rec.find('Elapsed time = ')
        if k >= 0:
            elapsed = rec[k + len('Elapsed time = '):].strip()

    if elapsed is None:
        fatal = True

    return (start_time, elapsed, modtime, abspath, error, fatal)


def get_all_log_info(logroot):
    """Find every validation log under one root and summarize the newest usable one.

    The walk collects every file whose name ends in ``.log`` and holds
    ``_re-validate_`` exactly once, keyed by the name of the directory holding it and
    the part of the basename before that marker. Within a key the paths come out in
    chronological order, and nothing sorts them by time to achieve it: the time tag is
    written most-significant-first, so sorting the names of one directory sorts them by
    date, and one volume's logs under one log root are all in one directory.

    For each key the search then runs backwards from the newest, and takes the first
    log that summarizes cleanly, is not fatal, and names a volume whose own key matches
    the key the path gave. "Is not fatal" is in practice "has an elapsed time", for the
    reason ``get_log_info()`` gives: the fatal marker it scans for is a string these logs
    never carry, so a validation that ended in an exception is taken here for a completed
    one. The last of those three matters after a holdings tree has
    been reorganized, when a log's path and the volume path inside it can disagree; such
    a log is passed over rather than trusted. A key whose logs all fail these tests
    contributes nothing to the first result and still appears in the second.

    Parameters:
        logroot (str): The directory tree to walk. Everything below it is searched, so
            logs of more than one holdings tree under one root are all found.

    Returns:
        tuple: (list of log summaries, dictionary of log paths). Each summary is what
        ``get_log_info()`` returns, one per key that had a usable log, in the order the
        walk found the keys. The dictionary is keyed the same way and holds every log
        path found, usable or not, in chronological order.

    Raises:
        TypeError: from the ``walk()`` when the log root is None, which is what
            ``_common.resolve_log_root()`` leaves when neither ``--log`` nor the
            environment variable is set.
        OSError: from ``get_log_info()`` on a log file that is found by the walk and
            then cannot be read.
    """

    # Create a dictionary keyed by volset/bundlename that returns the chronological
    # list of all associated log paths
    logs_for_volset_volume = {}
    for (root, _dirs, files) in os.walk(logroot):
        files = list(files)
        files.sort()
        for file in files:
            if not file.endswith('.log'):
                continue
            parts = file.split('_re-validate_')
            if len(parts) != 2:
                continue
            key = os.path.basename(root) + '/' + parts[0]
            if key not in logs_for_volset_volume:
                logs_for_volset_volume[key] = []
            logs_for_volset_volume[key].append(os.path.join(root, file))

    # Create a list containing info about the last log path that did not
    # produce a FATAL error.
    info_list = []
    for key, log_paths in logs_for_volset_volume.items():
        for log_path in log_paths[::-1]:
            try:
                info = get_log_info(log_path)
            except ValueError:
                continue

            # On rare occasions when the holdings tree has been reorganized, the
            # the log path and internal volume path can disagree.
            test = key_from_volume_abspath(info[3])     # info[3] is the abspath
            if test != key:
                continue

            if not info[-1]:    # info[-1] is had_fatal
                info_list.append(info)
                break

    return (info_list, logs_for_volset_volume)


def get_volume_info(holdings):
    """Return every volume under one holdings tree, with the date each was last changed.

    Volumes are found by globbing ``volumes/*_*/*_*``, so a directory qualifies by
    having an underscore in its name at both levels rather than by any check of what it
    holds. The date is the PdsFile object's own ``date``, a display string of the form
    ``YYYY-MM-DD HH:MM:SS`` rather than a number, and the empty string where there is no
    recorded modification time. It is compared as a string everywhere it is used, which
    that format makes safe.

    Parameters:
        holdings (str): The holdings directory, joined to the glob pattern as given.
            Its path is carried into the result unchanged, so a relative path or an
            unresolved symlink comes back the way it was passed in.

    Returns:
        list: One (path, date) pair per volume, in the order the glob returned them,
        which is neither sorted nor guaranteed. An empty list for a tree with no
        ``volumes/`` directory.
    """

    path = os.path.join(holdings, 'volumes/*_*/*_*')
    abspaths = glob.glob(path)

    info_list = []
    for abspath in abspaths:
        pdsdir = pdsfile.Pds3File.from_abspath(abspath)
        info_list.append((abspath, pdsdir.date))

    return info_list


def find_modified_volumes(holdings_info, log_info):
    """Work out what a batch run should validate, and in what order.

    A volume counts as modified when the (date, key) pair the holdings tree gives is not
    one of the pairs the logs give. That is a set difference on the pair, not a
    comparison of dates, so a volume whose date has moved in either direction counts,
    and a volume validated at one date and then reverted to it does not.

    The result is in two lists and a third thing that is neither. Modified volumes come
    first, sorted oldest date first, because a volume nothing has validated at its
    current date is the more urgent. Everything else is sorted by its log summary, whose
    first field is the start time of that validation, so the volume longest since
    validated leads. A key in the logs with no volume in holdings is in neither list and
    is reported separately.

    One correction is applied on the way through. A log summary whose volume path is not
    the path holdings currently gives for that key has the holdings path substituted, so
    a volume that has moved between trees is validated where it is now rather than where
    its last log says it was.

    A key names a volume and not the tree it is in, which is what makes that correction
    possible and also its cost. Where two holdings trees of one run carry the same
    volume, the dictionary keeps only the second one seen, so one path is scheduled --
    but the modified set is built from (date, key) pairs rather than from keys, so two
    trees whose copies carry different dates put that one path in the schedule **twice**,
    and the batch run validates it twice.

    Parameters:
        holdings_info (list): The (path, date) pairs from ``get_volume_info()``, over
            every holdings tree of the run.
        log_info (list): The log summaries from ``get_all_log_info()``.

    Returns:
        tuple: (modified volumes, other volumes, missing keys). The first is (path,
        date) pairs as they came from holdings. The second is log summaries, corrected
        as above. The third is the keys the logs know and holdings does not, in the
        order the log dictionary held them.
    """

    # Create a dictionary of log info organized by volset/volume
    # Also create the set (modtime, volset/volume) for each log volume
    log_dict = {}
    log_modtimes = set()
    for info in log_info:
        (_start, _elapsed, modtime, abspath, _had_error, _had_fatal) = info
        key = key_from_volume_abspath(abspath)
        log_dict[key] = info
        log_modtimes.add((modtime, key))

    # Create a dictionary of holdings info organized by volset/volume
    # Also create the set (modtime, volset/bundlename) for each holdings volume
    holdings_dict = {}
    holdings_modtimes = set()
    for (abspath, modtime) in holdings_info:
        parts = abspath.split('/')
        key = parts[-2] + '/' + parts[-1]
        holdings_dict[key] = (abspath, modtime)
        holdings_modtimes.add((modtime, key))

    # Determine the set of entries that have been modified since their last
    # validation
    modified_holdings = holdings_modtimes - log_modtimes

    # Update content to an ordered list of tuples (abspath, modtime)
    modified_holdings = list(modified_holdings)
    modified_holdings.sort()    # from oldest to newest
    modified_keys = [info[1] for info in modified_holdings]
    modified_holdings = [holdings_dict[key] for key in modified_keys]

    # Delete these keys from the log info dictionary
    for key in modified_keys:
        log_dict.pop(key, None)

    # Identify previously logged volumes not found in holdings
    # Delete these from the log dictionary
    missing_keys = [key for key in log_dict if key not in holdings_dict]
    for key in missing_keys:
        del log_dict[key]

    # If a log file is from a holdings directory tree not currently being
    # validated, redirect this validation to the correct directory tree.
    for key, info in log_dict.items():
        old_path = info[3]
        new_path = holdings_dict[key][0]
        if new_path != old_path:
            info = list(info)
            info[3] = new_path
            log_dict[key] = tuple(info)

    # Sort the remaining logged volumes from oldest to newest
    current_log_info = list(log_dict.values())
    current_log_info.sort()

    return (modified_holdings, current_log_info, missing_keys)


def format_email(to_addr, subject, message, date=None):
    """Return the recipient list and the message text an email report is sent as.

    The message is assembled as text rather than through the email package: a From, To,
    Subject and Date header, a blank line, and the body. The To header names every
    recipient, and the same text goes to each of them, so a recipient sees who else
    received it.

    Parameters:
        to_addr (str or list): One address, or a list of them. A string is wrapped in a
            list, so the two forms behave alike from here on.
        subject (str): The subject line.
        message (str): The body, inserted after one blank line and not wrapped.
        date (str): The value of the Date header. Defaults to the current local time
            written day-first, which is not the format the mail standards specify; a
            caller wanting a conforming header has to supply one.

    Returns:
        tuple: (recipients, message text). The recipients are a list whatever was passed
        in, and the text is one string with no trailing newline.
    """

    if date is None:
        date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    if isinstance(to_addr, str):
        to_addr = [to_addr]

    to_addr_in_msg = ','.join(to_addr)

    msg = ("From: %s\nTo: %s\nSubject: %s\nDate: %s\n\n%s" \
           % (FROM_ADDR, to_addr_in_msg, subject, date, message))

    return (to_addr, msg)


def send_email(to_addr, subject, message):
    """Mail one report, one message per recipient.

    The connection is opened to a fixed host and port, unauthenticated and unencrypted,
    which is what an internal mail relay accepts. The message is built once and sent once
    per address, so a failure part way through the list leaves the earlier recipients
    mailed and the later ones not.

    Parameters:
        to_addr (str or list): One address, or a list of them, as ``format_email()``
            takes it. Every address named appears in the To header of every copy.
        subject (str): The subject line.
        message (str): The body.

    Raises:
        OSError: from ``connect()``, if the mail host cannot be reached. Nothing here
            catches it, so a batch run that cannot mail its report ends in it, after the
            validations are done and the log is closed.
        smtplib.SMTPException: from ``sendmail()`` or ``quit()``, if the host refuses the
            message or the session.
    """

    smtp = SMTP()
    smtp.connect(SERVER, 25)

    (to_addr, msg) = format_email(to_addr, subject, message)

    for addr in to_addr:
        smtp.sendmail(FROM_ADDR, addr, msg)

    smtp.quit()

################################################################################
# Command line
################################################################################

def build_parser():
    """Return the argument parser for this tool.

    The parser is this tool's own rather than the shared one the ten specification
    driven tools use, because none of their five task flags applies here: everything
    this tool does is a validation, and what a command line selects is which validations
    over which directory trees. What it does share is the text of ``--log`` and
    ``--quiet``, taken from the same two constants the shared parser uses. That covers
    eleven of the thirteen tool modules in this subpackage -- the ten specification
    driven ones and this. Of the other two, ``pdsdependency`` carries its own copy of
    both texts, byte-identical today and tied to nothing, and ``crlf`` has neither
    option.

    Every selection flag stores true and defaults to false, so "none given" and "not
    wanted" are one state at this point; ``derive_options()`` is what turns it into a
    selection. Abbreviations are left enabled, unlike ``crlf``, the one tool here that
    switches them off, so a prefix of an option name is accepted where it is unambiguous.

    Returns:
        argparse.ArgumentParser: The parser, holding 21 arguments: the positional paths,
        ``--log`` and ``--quiet``, the three mode options, the two email options, the
        five test flags and ``--full``, the five volume-type flags and ``--all``, and
        ``--timeless``.
    """

    parser = argparse.ArgumentParser(
        description='re-validate: Perform various validation tasks on an online '  +
                    'volume or volumes.')

    parser.add_argument('volume', nargs='*', type=str,
                        help='Paths to volumes or volume sets for validation. '    +
                             'In batch mode, provide the path to the holdings '    +
                             'directory.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help=_common.LOG_HELP.format(env=_common.LOGROOT_ENV,
                                                     progname=PROGNAME))

    parser.add_argument('--batch', '-b', action='store_true',
                        help='Operate in batch mode. In this mode, the program '   +
                             'searches the existing logs and the given holdings '  +
                             'directories and validates any new volumes found. '   +
                             'Afterward, it validates volumes starting with the '  +
                             'ones with the oldest logs. Use --minutes to limit '  +
                             'the duration of the run.')

    parser.add_argument('--minutes', type=int, default=60,
                        help='In batch mode, this is the rough upper limit of '    +
                             'the duration of the run. The program will iterate '  +
                             'through available volumes but will not start a new ' +
                             'one once the time limit in minutes has been reached.')

    parser.add_argument('--batch-status', action='store_true',
                        help='Prints a summary of what the program would do now '  +
                             'if run in batch mode.')

    parser.add_argument('--email', type=str, action='append', default=[],
                        metavar='ADDR',
                        help='Email address to which to send a report when a '     +
                             'batch job completes. Repeat for multiple recipients.')

    parser.add_argument('--error-email',  type=str, action='append', default=[],
                        metavar='ADDR',
                        help='Email address to which to send an error report '     +
                             'when a batch job completes. If no errors are '       +
                             'found, no message is sent. Repeat for multiple '     +
                             'recipients.')

    parser.add_argument('--quiet', '-q', action='store_true',
                        help=_common.QUIET_HELP)

    parser.add_argument('--checksums', '-C', action='store_true',
                        help='Validate MD5 checksums.')

    parser.add_argument('--archives', '-A', action='store_true',
                        help='Validate archive files.')

    parser.add_argument('--info', '-I', action='store_true',
                        help='Validate infoshelves.')

    parser.add_argument('--links', '-L', action='store_true',
                        help='Validate linkshelves.')

    parser.add_argument('--dependencies', '-D', action='store_true',
                        help='Validate dependencies.')

    parser.add_argument('--full', '-F', action='store_true',
                        help='Perform the full set of validation tests '           +
                             '(checksums, archives, infoshelves, linkshelves, '    +
                             'dependencies). This is the default.')

    parser.add_argument('--timeless', '-T', action='store_true',
                        help='Suppress "newer modification date" tests for '       +
                             'dependencies. These tests are unnecessary during a ' +
                             'full validation because the contents of archive, '   +
                             'checksum and shelf files are also checked, so the '  +
                             'dates on these files are immaterial.')

    parser.add_argument('--volumes', '-v', action='store_true',
                        help='Check volume directories.')

    parser.add_argument('--calibrated', '-c', action='store_true',
                        help='Check calibrated directories.')

    parser.add_argument('--diagrams', '-d', action='store_true',
                        help='Check diagram directories.')

    parser.add_argument('--metadata', '-m', action='store_true',
                        help='Check metadata directories.')

    parser.add_argument('--previews', '-p', action='store_true',
                        help='Check preview directories.')

    parser.add_argument('--all', '-a', action='store_true',
                        help='Check all directories and files related to the '     +
                             'selected volume(s), i.e., those in volumes/, '       +
                             'calibrated/, diagrams/, metadata/, and previews/, '  +
                             'plus their checksums and archives. This is the '     +
                             'default.')

    return parser


def derive_options(args):
    """Work out which volume types and which tests one command line calls for.

    Each of the five volume-type flags selects one directory tree; naming none of
    them, or naming --all, selects every tree. Each of the five test flags selects
    one test; naming none of them, or naming --full, selects every test. Two of
    the tests are then narrowed to the trees they can run against at all, and
    --timeless survives only for as long as the dependency test does.

    Parameters:
        args (argparse.Namespace): The parsed command line. Five attributes are
            overwritten with the derived values -- ``checksums``, ``archives``,
            ``infoshelves``, ``linkshelves`` and ``dependencies`` -- and so is
            ``timeless``. Two of those names are not the ones the parser wrote:
            ``--info`` parses into ``info`` and ``--links`` into ``links``, and both of
            those are read once here and then left holding what the command line said
            while the derived values go to the longer names. ``validate_one_volume()``
            reads the longer names.

    Returns:
        tuple: (volume types, test names), each in this module's own fixed order rather
        than the order the command line named them. The volume types are the directory
        trees each test is run over, and both lists are written into the log header.
        Which tests run is not read from the second list but from the attributes above,
        so the list names the tests and does not select them.
    """

    # Interpret file types
    voltypes = []
    if args.volumes:
        voltypes += ['volumes']
    if args.calibrated:
        voltypes += ['calibrated']
    if args.diagrams:
        voltypes += ['diagrams']
    if args.metadata:
        voltypes += ['metadata']
    if args.previews:
        voltypes += ['previews']

    if voltypes == [] or args.all:
        voltypes = list(ALL_VOLTYPES)

    # Determine which tests to perform
    checksums    = args.checksums
    archives     = args.archives
    infoshelves  = args.info
    linkshelves  = args.links
    dependencies = args.dependencies

    if args.full or not (checksums or archives or infoshelves or linkshelves or
                         dependencies):
        checksums    = True
        archives     = True
        infoshelves  = True
        linkshelves  = True
        dependencies = True

    dependencies &= ('volumes' in voltypes)
    linkshelves  &= any(voltype in voltypes for voltype in LINKSHELF_VOLTYPES)

    args.checksums    = checksums
    args.archives     = archives
    args.infoshelves  = infoshelves
    args.linkshelves  = linkshelves
    args.dependencies = dependencies

    tests = []
    if checksums:
        tests.append('checksums')
    if archives:
        tests.append('archives')
    if infoshelves:
        tests.append('infoshelves')
    if linkshelves:
        tests.append('linkshelves')
    if dependencies:
        tests.append('dependencies')

    args.timeless = args.timeless and args.dependencies

    return (voltypes, tests)

################################################################################
# Interactive mode
################################################################################

def run_interactive(args, voltypes, tests, logger, argv):
    """Validate every volume named on the command line, then exit.

    Every path is checked before any of them is validated, and a bad one ends the run
    with a message and no log record written: no path given, a path that does not exist,
    and a path that is not a volume or volume set directory under ``volumes/``. A volume
    set is expanded into its volumes at that point, so the run validates volumes only.
    A configured log root does get its ``re-validate`` directory and an empty
    ``ERRORS.log``, which ``main()`` creates before this is called, so an empty error log
    is not evidence that a run reached a volume.

    Parameters:
        args (argparse.Namespace): The parsed command line, after
            ``derive_options()``. Its ``volume`` list is the paths, and its derived test
            attributes are passed through to each volume.
        voltypes (list): The selected directory trees.
        tests (list): The names of the selected tests, for the log header.
        logger: The run's logger. Each path's holdings root is added to it, so the log
            abbreviates absolute paths.
        argv (list): The full command line, echoed as the top line of the log.

    Raises:
        SystemExit: from ``sys.exit()``, which is how this function returns when nothing
            raises. The status is 1 for an unusable path, and after that 1 if the run
            logged a fatal or an error and 0 if it did not. What a volume's own tests
            found is not consulted directly; the counts come from closing the run's log.
        ValueError: from ``from_abspath()``, before any of the above, for a path it
            cannot place in a holdings tree at all. That is a different failure from the
            "not a volume path" message, which is this function's own.
        KeyboardInterrupt: from ``validate_one_volume()``, which does not catch it. It
            is logged here and re-raised rather than turned into a status, so an
            interrupted run ends in a traceback with the run's log closed.
    """

    # Stop if a volume or volume set doesn't exist
    if not args.volume:
        print('Missing volume path')
        sys.exit(1)

    for volume in args.volume:
        if not os.path.exists(volume):
            print('Volume path not found: ' + volume)
            sys.exit(1)

    # Convert to PdsFile objects; expand volume sets; collect holdings paths
    pdsdirs = []
    for volume in args.volume:
        abspath = os.path.abspath(volume)
        pdsdir = pdsfile.Pds3File.from_abspath(abspath)
        if pdsdir.category_ != 'volumes/' or pdsdir.interior:
            print('Not a volume path: ', pdsdir.abspath)
            sys.exit(1)

        logger.add_root(pdsdir.root_)

        if pdsdir.volname:
            pdsdirs.append(pdsdir)
        else:
            for name in pdsdir.childnames:
                pdsdirs.append(pdsdir.child(name))

    # Main loop
    logger.open(' '.join(argv))
    try:
        # For each volume...
        for pdsdir in pdsdirs:
            _ = validate_one_volume(pdsdir, voltypes, tests, args, logger)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        (fatal, errors, _warnings, _tests) = logger.close()
        status = 1 if (fatal or errors) else 0

    sys.exit(status)

################################################################################
# Batch mode
################################################################################

def resolve_holdings_paths(paths):
    """Return the holdings roots the given command-line paths name, deduplicated.

    Each path is resolved through its symlinks and made absolute, and the result must
    end in ``holdings``. Resolving first is what makes two names for one tree collapse
    to one entry; it also means the paths returned are not the paths the user typed, and
    the rest of a batch run reads the raw arguments rather than these, so the two forms
    are both in play in one run.

    Parameters:
        paths (list): The command line's positional arguments, which in batch mode are
            holdings roots rather than volumes.

    Returns:
        list: One resolved absolute path per distinct holdings root, in the order first
        named.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1, if no path is given, if one does
            not exist, or if one does not resolve to a path ending in ``holdings``.
    """

    if not paths:
        print('No holdings path identified')
        sys.exit(1)

    holdings_abspaths = []
    for holdings in paths:
        if not os.path.exists(holdings):
            print('Holdings path not found: ' + holdings)
            sys.exit(1)

        holdings = holdings.rstrip('/')
        holdings = os.path.realpath(holdings)
        holdings = os.path.abspath(holdings)
        if not holdings.endswith('/holdings'):
            print('Not a holdings directory: ' + holdings)
            sys.exit(1)

        if holdings not in holdings_abspaths:
            holdings_abspaths.append(holdings)

    return holdings_abspaths


def report_missing_volumes(missing_keys, logs_for_volset_volname,
                           holdings_abspaths, logger):
    """Log an error for every volume that has a log but is no longer in holdings.

    A key is only worth reporting when one of the holdings trees being validated
    is the one its logs were written against; a key whose logs all came from some
    other tree is not this run's business.

    Which trees a key's logs were written against is recovered from the logs themselves,
    one open per log file, by taking the part of each recorded volume path before
    ``/volumes``. **The filter is applied once per key and the report is not filtered at
    all**: a key qualifies if any one of its trees is among the run's, and every tree its
    logs name is then reported, in sorted order. So a volume dropped from two trees, only
    one of which this run was asked about, produces a "Missing volume" error naming the
    other tree as well. Empty log files contribute nothing.

    Parameters:
        missing_keys (list): The keys found in the logs and not in holdings, from
            ``find_modified_volumes()``.
        logs_for_volset_volname (dict): Every log path found by the walk, keyed the same
            way, from ``get_all_log_info()``. Every key passed in must be present here.
        holdings_abspaths (set): The holdings roots this run is validating. It has to be
            a set rather than a list, because it is intersected.
        logger: The run's logger, which the errors are logged to. Nothing is printed
            and nothing is returned.

    Raises:
        OSError: from ``volume_abspath_from_log()``, if a log file the walk found has
            since been removed or cannot be read.
        UnicodeDecodeError: from ``volume_abspath_from_log()``, on a log that is not
            valid UTF-8. Nothing here catches it, so one such log ends the report with
            the remaining keys unexamined.
    """

    for key in missing_keys:
        # Determine if this volset has ever appeared in any of the
        # holdings directory trees
        holdings_for_key = set()
        for log_path in logs_for_volset_volname[key]:
            volume_abspath = volume_abspath_from_log(log_path)
            if volume_abspath == '':        # if log file is empty
                continue

            holdings_abspath = volume_abspath.split('/volumes')[0]
            holdings_for_key.add(holdings_abspath)

        # If not, ignore
        if not (holdings_abspaths & holdings_for_key):
            continue

        # Report error
        holdings_for_key = list(holdings_for_key)
        holdings_for_key.sort()
        for holdings_abspath in holdings_for_key:
            logger.error('Missing volume',
                         os.path.join(holdings_abspath + '/volumes', key))


def print_batch_status(modified_holdings, current_logs):
    """Print what a batch run would do now, then exit.

    One numbered line per volume, in the order a batch run would take them: the modified
    volumes first, then the rest. The two groups print different lines, because a
    modified volume has no previous validation to describe -- the second group's line
    carries the date of the last validation, how long it took, and a note where that run
    logged an error.

    Parameters:
        modified_holdings (list): The (path, date) pairs of the volumes with no
            validation at their current date.
        current_logs (list): The log summaries of the rest, oldest validation first.

    Raises:
        SystemExit: raised by ``sys.exit()`` with no argument. Its code is None and its
            process status is 0, which is not the same call as the ``sys.exit(0)`` at
            the end of a batch run.
        ValueError: from ``from_abspath()``, for a volume path that no holdings tree the
            current environment knows contains. A log written against a tree that has
            since moved holds exactly such a path.
    """

    fmt = '%4d %20s%-11s  modified %s, not previously validated'
    line_number = 0
    for (abspath, date) in modified_holdings:
        pdsdir = pdsfile.Pds3File.from_abspath(abspath)
        line_number += 1
        print(fmt % (line_number, pdsdir.volset_, pdsdir.volname,
                     date[:10]))

    fmt ='%4d  %20s%-11s  modified %s, last validated %s, duration %s%s'
    for info in current_logs:
        (start, elapsed, date, abspath, had_error, _had_fatal) = info
        pdsdir = pdsfile.Pds3File.from_abspath(abspath)
        error_text = ', error logged' if had_error else ''
        line_number += 1
        print(fmt % (line_number, pdsdir.volset_, pdsdir.volname,
                     date[:10], start[:10], elapsed[:-7], error_text))

    sys.exit()


def run_batch(args, voltypes, tests, logger, argv):
    """Validate the volumes whose logs are oldest, until the time limit is up.

    The schedule is built before any volume is validated: the logs are read, the current
    holdings are globbed, the two are compared, and volumes missing from holdings are
    reported. Under ``--batch-status`` the schedule is printed at that point and the run
    ends without validating anything.

    The time limit is checked after each volume rather than before, so a run that reaches
    the limit stops somewhere past it, by at most the length of the volume that carried
    it over. A run that exhausts its schedule first never tests the limit at all, and a
    run whose schedule is empty validates nothing and reports a timeout anyway. The
    elapsed time is read as the seconds component of the interval rather than its whole
    length, so a limit of 1,440 minutes or more is never reached.

    Once the main loop has been entered, the report is mailed from a ``finally``: a full
    report to each ``--email`` address, subject-lined according to whether anything
    failed, and an error-only report to each ``--error-email`` address if anything did.
    Nothing that goes wrong while the schedule is still being built reaches that block,
    and neither does ``--batch-status``, which exits before it. The summary line printed
    at the end says "Timeout" whether the run stopped on the limit or ran out of volumes.

    Parameters:
        args (argparse.Namespace): The parsed command line, after ``derive_options()``.
            Its ``volume`` list is the holdings roots, its ``log`` is the log tree to
            read the schedule from, and its ``minutes`` is the limit.
        voltypes (list): The selected directory trees.
        tests (list): The names of the selected tests, for each volume's log header.
        logger: The run's logger.
        argv (list): The full command line, echoed as the top line of the log.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 for an unusable path, 0 at the
            end of a batch run whatever it logged, and a code of None from the
            ``--batch-status`` path. **The status is 0 even for a run that logged
            errors**, because a nonzero status would cancel the launch daemon that
            schedules it; the errors are reported by mail instead.
        OSError: from ``send_email()``, if the relay cannot be reached or refuses the
            message; ``smtplib.SMTPException`` is a subclass of it, so the refusal cases
            arrive under this name too. It is raised from the ``finally`` that runs just
            before the ``sys.exit(0)`` below it, and nothing catches it, so it is the one
            way a run that got as far as validating something ends nonzero. The three
            entries around this one are the others, and all of them fire before any
            volume is validated.
        TypeError: from ``get_all_log_info()`` when no log root is configured, before
            any volume is validated.
        KeyboardInterrupt: from ``validate_one_volume()``, which does not catch it. It
            is logged here and re-raised, but only after the ``finally`` has closed the
            log and mailed the report, so an interrupted batch run still mails what it
            had done.
    """

    holdings_abspaths = resolve_holdings_paths(args.volume)

    logger.add_root(holdings_abspaths)
    holdings_abspaths = set(holdings_abspaths)

    # Read the existing logs
    (log_info, logs_for_volset_volname) = get_all_log_info(args.log)

    # Read the current holdings
    holdings_info = []
    for holdings in args.volume:
        holdings_info += get_volume_info(holdings)

    # Define an ordered list of tasks
    (modified_holdings,
     current_logs,
     missing_keys) = find_modified_volumes(holdings_info, log_info)

    # Report missing volumes
    report_missing_volumes(missing_keys, logs_for_volset_volname,
                           holdings_abspaths, logger)

    # Print info in trial run mode
    if args.batch_status:
        print_batch_status(modified_holdings, current_logs)

    # Start batch processing
    # info = (abspath, mod_date, prev_validation, had_errors)
    info = [(p[0], p[1], None, False) for p in modified_holdings] + \
           [(p[3], p[2], p[0], p[4]) for p in current_logs]
    start = datetime.datetime.now()

    batch_messages = []
    error_messages = []
    batch_prefix = ('Batch re-validate started at %s on %s\n' %
                    (start.strftime("%Y-%m-%d %H:%M:%S"),
                     ','.join(args.volume)))
    print(batch_prefix)

    # Main loop
    logger.open(' '.join(argv))
    try:

        # For each volume...
        for (abspath, mod_date, prev_validation, _had_errors) in info:
            pdsdir = pdsfile.Pds3File.from_abspath(abspath)
            if prev_validation is None:
                ps = 'not previously validated'
            else:
                ps = 'last validated %s' % prev_validation[:10]
            batch_message = '%20s%-11s  modified %s, %s' % \
                            (pdsdir.volset_, pdsdir.volname, mod_date[:10], ps)
            print(batch_message)

            (log_path,
             fatal, errors) = validate_one_volume(pdsdir, voltypes, tests,
                                                  args, logger)
            error_message = ''
            if fatal or errors:
                stringlist = ['***** ']
                if fatal:
                    stringlist += ['Fatal = ', str(fatal), '; ']
                if errors:
                    stringlist += ['Errors = ', str(errors), '; ']
                stringlist.append(log_path)
                error_message = ''.join(stringlist)

                print(error_message)

            batch_messages.append(batch_message)

            if error_message:
                batch_messages.append(error_message)

                error_messages.append(batch_message)
                error_messages.append(error_message)

            now = datetime.datetime.now()
            if (now - start).seconds > args.minutes*60:
                break

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

        now = datetime.datetime.now()
        batch_suffix = ('\nTimeout at %s after %d minutes' %
                         (now.strftime("%Y-%m-%d %H:%M:%S"),
                         int((now - start).seconds/60. + 0.5)))
        print(batch_suffix)

        if args.email:
            if error_messages:
                subj = REPORT_SUBJ_W_ERRORS
            else:
                subj = REPORT_SUBJ

            full_message = [batch_prefix] + batch_messages + [batch_suffix]
            send_email(args.email, subj, '\n'.join(full_message))

        if error_messages and args.error_email:
            full_message = [batch_prefix] + error_messages + [batch_suffix]
            send_email(args.error_email, ERROR_REPORT_SUBJ,
                                              '\n'.join(full_message))

    # Batch mode reports success even when the run logged errors, because a
    # nonzero status would cancel the launch daemon that schedules it.
    sys.exit(0)

################################################################################
# Executable program
################################################################################

def main(argv=None):
    """Parse the command line, set up logging, and run the mode it selects.

    The logger is built here and the two mode functions are handed it, so a run has one
    logger whatever mode it is in. Terminal output is attached unless ``--quiet``, and an
    error handler under the log root is attached when there is one. The log root is also
    set on the PdsFile class, which is what makes each volume's log path resolve under
    it.

    Batch mode is selected by ``--batch`` or by ``--batch-status``, so asking what a
    batch run would do does not also need ``--batch``.

    Parameters:
        argv (list): The full command line, its first element the program name.
            Defaults to sys.argv.

    Raises:
        SystemExit: from ``parse_args()``, with status 2 for a command line argparse
            cannot classify and 0 for ``--help``, before either mode is reached; and
            otherwise from ``run_interactive()`` or ``run_batch()``, each of which exits
            rather than returning. Their docstrings give the statuses they choose.
        ValueError: from ``run_interactive()`` on a path outside every holdings tree, and
            from ``run_batch()`` on a log whose recorded volume path is.
        TypeError: from ``run_batch()`` when no log root is configured.
        OSError: from ``run_batch()``, if its report cannot be mailed, and from either
            mode on a log file that cannot be read.
        KeyboardInterrupt: from ``run_interactive()`` or ``run_batch()``, each of which
            logs it and re-raises rather than turning it into a status.
    """

    if argv is None:
        argv = sys.argv

    # Parse and validate the command line
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    (voltypes, tests) = derive_options(args)

    # Define the logging directory
    _common.resolve_log_root(args)

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME, limits={'info':100, 'debug':10})

    # Place to search for existing logs in batch mode
    pdsfile.Pds3File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, PROGNAME)
        logger.add_handler(pdslogger.error_handler(path))

    if not args.batch and not args.batch_status:
        run_interactive(args, voltypes, tests, logger, argv)
    else:
        run_batch(args, voltypes, tests, logger, argv)

if __name__ == '__main__':
    main()
