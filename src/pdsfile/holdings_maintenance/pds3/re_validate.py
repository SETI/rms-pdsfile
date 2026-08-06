#!/usr/bin/env python3
################################################################################
# re_validate.py library and main program
#
# Syntax:
#   python -m pdsfile.holdings_maintenance.pds3.re_validate path [path ...]
#
# Enter the --help option to see more information.
################################################################################

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
    """Validates one volume."""

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
    """Return the absolute path within the holdings directory of the PDS volume
    described by this validation log.
    """

    with open(log_path) as f:
        rec = f.readline()

    parts = rec.split('|')
    return parts[-1].strip().split(' ')[-1]


def key_from_volume_abspath(abspath):
    """Return 'volset/bundlename' from this absolute path.
    """

    parts = abspath.split('/')
    return '/'.join(parts[-2:])


def key_from_log_path(log_path):
    """Return 'volset/bundlename' from this log path.
    """

    parts = log_path.split('/')
    bundlename = parts[-1].split('_re-validate_')[0]

    return parts[-2] + '/' + bundlename


def get_log_info(log_path):
    """Return info from the log:
        (start, elapsed, modtime, abspath, had_error, had_fatal).
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
    """Return a list of info about the latest version of every log file,
    skipping those that recorded a FATAL error. Each log file is described by
    the tuple:
      (start, elapsed, modtime, abspath, had_error, had_fatal).
    Also return a dictionary that provides the complete list of existing log
    files, in chronological order, keyed by volset/bundlename.
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
    """Return a list of tuples (volume abspath, modtime) for every volume in
    the given holdings directory."""

    path = os.path.join(holdings, 'volumes/*_*/*_*')
    abspaths = glob.glob(path)

    info_list = []
    for abspath in abspaths:
        pdsdir = pdsfile.Pds3File.from_abspath(abspath)
        info_list.append((abspath, pdsdir.date))

    return info_list


def find_modified_volumes(holdings_info, log_info):
    """Compare the information in the holdings info and log info; return a tuple
    (modified_holdings, current_log_info, missing_keys)."""

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
    """Return the (recipient list, message text) an email report is sent as.

    Args:
        to_addr: One address as a string, or a list of addresses.
        subject: The subject line.
        message: The body.
        date: The value of the Date header. Defaults to now.

    Returns:
        tuple: (list[str], str), the recipients and the complete message text.
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
    """Return the argument parser for this tool."""

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

    Args:
        args: The parsed command line. The five test attributes and the timeless
            attribute are overwritten with the derived values, because
            validate_one_volume reads the tests back off it.

    Returns:
        tuple: (voltypes, tests), the selected directory trees and the names of
        the selected tests, each in a fixed order.
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

    Args:
        args: The parsed command line, after derive_options.
        voltypes: The selected directory trees.
        tests: The names of the selected tests.
        logger: The run's logger.
        argv: The full command line, echoed into the top of the log.

    Raises:
        SystemExit: Always, with status 1 if a path is unusable or if the run
            logged a fatal or an error, and 0 otherwise.
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

    Args:
        paths: The command line's positional arguments.

    Returns:
        list[str]: One absolute path per distinct holdings root, in the order
        first named.

    Raises:
        SystemExit: With status 1 if no path is given, if one does not exist, or
            if one is not a holdings directory.
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

    Args:
        missing_keys: The volset/volname keys found in the logs and not in
            holdings.
        logs_for_volset_volname: Every log path, keyed by volset/volname.
        holdings_abspaths: The holdings roots this run is validating, as a set.
        logger: The run's logger.
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

    Raises:
        SystemExit: Always, raised by sys.exit() with no argument. Its code is None
            and its process status is 0, which is not the same call as sys.exit(0)
            at the end of a batch run.
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

    Args:
        args: The parsed command line, after derive_options.
        voltypes: The selected directory trees.
        tests: The names of the selected tests.
        logger: The run's logger.
        argv: The full command line, echoed into the top of the log.

    Raises:
        SystemExit: Always, with status 1 if a path is unusable and 0 otherwise --
            including when the run logged errors, because a nonzero status would
            cancel the launch daemon that schedules it.
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

    Args:
        argv: The full command line, defaulting to sys.argv.

    Raises:
        SystemExit: Always. See run_interactive and run_batch for the statuses.
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
