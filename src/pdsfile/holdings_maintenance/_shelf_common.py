##########################################################################################
# pdsfile/holdings_maintenance/_shelf_common.py
#
# What the checksum and shelf file tools share.
#
# The generic driver the tools of every family run on is in _common.py; this is
# the part only the checksums, infoshelf and linkshelf tools use.
##########################################################################################

import argparse
import datetime
import glob
import hashlib
import os
import shutil
import sys
from dataclasses import dataclass

import pdslogger

from pdsfile.holdings_maintenance import _common

# The PdsLogger name each tool kind logs under. Both flavors of a kind share one.
CHECKSUMS_LOGNAME = 'pds.validation.checksums'
INFOSHELF_LOGNAME = 'pds.validation.fileinfo'
LINKSHELF_LOGNAME = 'pds.validation.links'


# The two log-path methods one of these tools picks between for each target: a
# target that names a unit logs under that unit, one that names only a unit set logs
# under the set. Both are defined on the shared PdsFile base, so the same pair of
# names serves the PDS3 and the PDS4 tools; Pds3File's log_path_for_volume and
# log_path_for_volset are aliases of these two.
UNIT_LOG_PATH_METHOD = 'log_path_for_bundle'
UNITSET_LOG_PATH_METHOD = 'log_path_for_bundleset'

# How far apart two modification times may be and still count as the same time.
# Seconds, exclusive: a difference of one second is a difference. Both times here
# come from the same generator at microsecond precision, so the only discrepancy to
# forgive is a sub-second one; on a filesystem that stores whole seconds, one second
# is the smallest change there is rather than an edge case, and reporting it is the
# point. validate_tuples() compares a tarfile's whole-second time against a
# filesystem time and so allows a full second inclusively; that difference between
# the two is deliberate, and follows from what each pair of operands is.
MODTIME_TOLERANCE = 1


def modtimes_agree(modtime1, modtime2, tolerance=MODTIME_TOLERANCE):
    """Return whether two modification times are the same time.

    The two are strings as generate_infodict() builds them,
    '%Y-%m-%d %H:%M:%S.%f'. They agree when they are less than the tolerance apart,
    which makes the comparison symmetric and monotone in the real difference between
    them: two times a millisecond apart agree wherever they fall, and two times a
    second or more apart never do.

    An empty string is the sentinel for a directory with nothing in it, and no
    sentinel parses as a time. Anything the two cannot be compared as times --
    a sentinel, a value that is not a time at all, or a pair that cannot be
    subtracted because only one of them carries a time zone -- falls back to
    comparing the two strings, so two sentinels agree and a sentinel never agrees
    with a real time.

    Args:
        modtime1: One modification time.
        modtime2: The other.
        tolerance: How many seconds apart they must stay within, exclusive.
            Default MODTIME_TOLERANCE.

    Returns:
        bool: True if they are the same time.
    """

    try:
        time1 = datetime.datetime.fromisoformat(modtime1)
        time2 = datetime.datetime.fromisoformat(modtime2)
        difference = abs((time1 - time2).total_seconds())
    except (TypeError, ValueError):
        return modtime1 == modtime2

    return difference < tolerance


@dataclass(kw_only=True)
class VersionedFile:
    """What move_old() needs to know about one kind of file it versions.

    Attributes:
        noun: How the file is named in the two log lines, e.g. 'Checksum file'.
        logname: The PdsLogger name to fall back on when no logger is given.
        companions: The extensions of the files that travel with it. Each is copied
            beside the versioned file under the same name and its own extension. A
            link shelf lists '.pickle', which names the shelf file itself, so that
            file is copied twice to the one destination.
    """

    noun: str
    logname: str
    companions: tuple = ()


CHECKSUM_FILE = VersionedFile(noun='Checksum file', logname=CHECKSUMS_LOGNAME)
INFO_SHELF = VersionedFile(noun='Info shelf file', logname=INFOSHELF_LOGNAME,
                           companions=('.py',))
LINK_SHELF = VersionedFile(noun='Link shelf file', logname=LINKSHELF_LOGNAME,
                           companions=('.py', '.pickle'))

# The log directories a superseded checksum or shelf file is versioned into. A run
# fills this in for each target it is about to work on -- run_selection_main() for
# the tools on that driver, each tool's own main() for the rest; a process that
# never calls set_log_dirs leaves it empty, and then move_old() versions nothing.
LOGDIRS = []


def set_log_dirs(logfiles):
    """Record the log directories move_old() versions a superseded file into.

    Args:
        logfiles: The log file paths of the target about to be worked on. The
            directory of each is what a superseded file is copied into.
    """

    global LOGDIRS
    LOGDIRS = [os.path.split(logfile)[0] for logfile in logfiles]


def next_version_dest(log_dir, prefix, ext):
    """Return the unused <prefix>_v###<ext> path in one log directory.

    ### is one past the highest version already there, and 001 when there is none.

    Args:
        log_dir: The directory the versioned copy goes in.
        prefix: The superseded file's basename without its extension.
        ext: That extension, including the dot.

    Returns:
        str: The path to copy to.
    """

    dest_template = log_dir + '/' + prefix + '_v???' + ext

    max_version = 0
    lskip = len(ext)
    for version_path in glob.glob(dest_template):
        max_version = max(max_version, int(version_path[-lskip-3:-lskip]))

    return dest_template.replace('???', f'{max_version + 1:03d}')


def move_old(path, kind, *, logger=None):
    """Version the file a task is about to replace, into every recorded log directory.

    The file is copied rather than moved, despite what the log lines say: the
    original stays where it is and the task then overwrites it.

    Args:
        path: The file about to be replaced. Nothing happens if it does not exist,
            or if no log directory has been recorded.
        kind: The VersionedFile describing it.
        logger: The logger to report through. Defaults to the kind's own.
    """

    if not os.path.exists(path):
        return

    logger = logger or pdslogger.PdsLogger.get_logger(kind.logname)

    (prefix, ext) = os.path.splitext(os.path.basename(path))
    stem = path.rpartition('.')[0]

    from_logged = False
    for log_dir in LOGDIRS:
        dest = next_version_dest(log_dir, prefix, ext)
        shutil.copy(path, dest)

        # Both lines pass the path as the second argument, so PdsLogger renders the
        # colon and applies the logger's root replacement to it. force=True keeps a
        # limits cap from dropping the report of a change to the filesystem.
        if not from_logged:
            logger.info(kind.noun + ' moved from', path, force=True)
            from_logged = True

        logger.info(kind.noun + ' moved to', dest, force=True)

        dest_stem = dest.rpartition('.')[0]
        for companion in kind.companions:
            shutil.copy(stem + companion, dest_stem + companion)


# From http://stackoverflow.com/questions/3431825/-
#       generating-an-md5-checksum-of-a-file

def hashfile(fname, blocksize=65536):
    hasher = hashlib.md5()

    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


##########################################################################################
# Command line for the checksum and shelf file tools
#
# These tools take a target that can name one file inside a unit rather than the
# whole unit, so a command-line path expands to (unit, selection) pairs and the
# driver below is not the one run_main provides.
##########################################################################################

ARCHIVES_ARGUMENT = (('--archives', '-a'),
                     {'default': False, 'action': 'store_true',
                      'help': 'Instead of referring to a {unit}, refer to the the '
                              'archive file for that {unit}.'})

INFOSHELF_ARGUMENT = (('--infoshelf', '-i'),
                      {'dest': 'infoshelf', 'default': False, 'action': 'store_true',
                       'help': 'After a successful run, also execute the equivalent '
                               'pdsinfoshelf command.'})

CHECKSUMS_DESCRIPTION = ('{progname}: Create, maintain and validate MD5 checksum files '
                         'for PDS {units} and {unit} sets.')

CHECKSUMS_TASK_HELP = {
    'initialize': 'Create an MD5 checksum file for a {unit} or {unit} set. Abort if '
                  'the checksum file already exists.',
    'reinitialize': 'Create an MD5 checksum file for a {unit} or {unit} set. Replace '
                    'the checksum file if it already exists. If a single file is '
                    'specified, such as one archive file in a {unit} set, only single '
                    'checksum is re-initialized.',
    'validate': 'Validate every file in a {unit} directory tree against its MD5 '
                'checksum. If a single file is specified, such as one archive file in '
                'a {unit} set, only that single checksum is validated.',
    'repair': 'Validate every file in a {unit} directory tree against its MD5 '
              'checksum. If any disagreement is found, the checksum file is replaced; '
              'otherwise it is unchanged. If a single file is specified, such as one '
              'archive file of a {unit} set, then only that single checksum is '
              "repaired. If any of the files checked are newerthan the checksum file, "
              "update shelf file's modification date",
    'update': 'Search a directory for any new files and add their MD5 checksums to the '
              'checksum file. Checksums of pre-existing files are not checked.',
}

CHECKSUMS_POSITIONAL_HELP = ('The path to the root directory of a {unit} or {unit} '
                             'set. For a {unit} set, all the {unit} directories inside '
                             'it are handled in sequence. Note that, for archive '
                             'directories, checksums are grouped into one file for the '
                             'entire {unit} set.')

INFOSHELF_DESCRIPTION = ('{progname}: Create, maintain and validate shelf files '
                         'containing basic information about each file.')

INFOSHELF_TASK_HELP = {
    'initialize': 'Create an infoshelf file for a {unit}. Abort if the file already '
                  'exists.',
    'reinitialize': 'Create an infoshelf file for a {unit}. Replace the file if it '
                    'already exists. If a single file is specified, such as one '
                    'archive file in a {unit} set, then only information about that '
                    'file is re-initialized.',
    'validate': 'Validate every file in a {unit} against the contents of its infoshelf '
                'file. If a single file is specified, such as an archive file in a '
                '{unit} set, then only information about that file is validated',
    'repair': 'Validate every file in a {unit} against the contents of its infoshelf '
              'file. If any file has changed, the infoshelf file is replaced. If a '
              'single file is specified, such as an archive file in a {unit} set, then '
              'only information about that file is repaired. If any of the files '
              "checked are newer than the shelf file, update the shelf file's "
              'modification date.',
    'update': 'Search a directory for any new files and add their information to the '
              'infoshelf file. Information about pre-existing files is not updated. If '
              'any of the files checked are newer than the shelf file, update the '
              "shelf file's modification date.",
}

INFOSHELF_POSITIONAL_HELP = ('The path to the root of the {unit} or {unit} set. For a '
                             '{unit} set, all the {unit} directories inside it are '
                             'handled in sequence.')


def resolve_holdings_paths(spec, paths, *, archives):
    """Return the absolute paths one of these tools was asked to work on.

    Each command-line path must fall inside a holdings tree and must not name
    checksum files. With archives set, a path that does not already name archive
    files is redirected to the archive files of the same unit. A path that does not
    resolve to anything gets one more chance, as a unit name standing in for that
    unit's .tar.gz archive.

    Args:
        spec: The tool's ToolSpec.
        paths: The command-line paths.
        archives: True if --archives was given.

    Returns:
        list[str]: The absolute paths, in command-line order.

    Raises:
        SystemExit: With status 1 if a path is outside the holdings tree or names
            checksum files.
    """

    sentinel = spec.holdings_sentinel
    abspaths = []
    for path in paths:

        # Make sure path makes sense
        path = os.path.abspath(path)
        parts = path.partition(sentinel)
        if not parts[1]:
            print('Not a holdings subdirectory: ' + path)
            sys.exit(1)

        if parts[2].startswith('checksums-'):
            print(spec.checksum_path_message + path)
            sys.exit(1)

        # Convert to an archives path if necessary
        if archives and not parts[2].startswith('archives-'):
            path = parts[0] + sentinel + 'archives-' + parts[2]

        # Convert to a list of absolute paths that exist (unit sets or units)
        try:
            pdsf = spec.pdsfile_cls.from_abspath(path, must_exist=True)
            abspaths.append(pdsf.abspath)

        except (ValueError, OSError):
            # Allow a unit name to stand in for a .tar.gz archive
            (dirname, basename) = os.path.split(path)
            pdsdir = spec.pdsfile_cls.from_abspath(dirname)
            if pdsdir.archives_ and '.' not in basename:
                if pdsdir.bundletype_ == spec.unit + 's/':
                    basename += '.tar.gz'
                else:
                    basename += f'_{pdsdir.bundletype_[:-1]}.tar.gz'

                newpaths = glob.glob(os.path.join(dirname, basename))
                if len(newpaths) == 0:
                    raise

                abspaths += newpaths
                continue
            else:
                raise

    return abspaths


def expand_selection_targets(spec, abspaths):
    """Return the (unit, selection) pairs those absolute paths name.

    A unit set expands to its unit directories, except an archive unit set, whose
    files are handled as one group. A file expands to its own unit paired with its
    basename, which is the selection the task functions narrow their work to.

    Args:
        spec: The tool's ToolSpec.
        abspaths: The absolute paths, as resolve_holdings_paths() returned them.

    Returns:
        list: (PdsFile, selection) pairs, where selection is None for a whole unit.

    Raises:
        SystemExit: With status 1 for a directory or a file this tool cannot work on.
    """

    info = []
    for path in abspaths:
        pdsf = spec.pdsfile_cls.from_abspath(path)

        if pdsf.is_bundleset_dir:
            # Archive directories are handled by unit set
            if pdsf.archives_:
                info.append((pdsf, None))

            # Others are handled by unit
            else:
                children = [pdsf.child(c) for c in pdsf.childnames]
                info += [(c, None) for c in children if c.isdir]
                        # "if c.isdir" is False for unit set level readme files

        elif pdsf.is_bundle_dir:
            # Handle one unit
            info.append((pdsf, None))

        elif pdsf.isdir:
            print(spec.invalid_dir_message + pdsf.logical_path)
            sys.exit(1)

        else:
            pdsdir = pdsf.parent()
            if pdsf.is_bundle_file:
                # Handle one archive file
                info.append((pdsdir, pdsf.basename))
            elif pdsdir.is_bundle_dir:
                # Handle one top-level file in a unit
                info.append((pdsdir, pdsf.basename))
            else:
                print(spec.invalid_file_message + pdsf.logical_path)
                sys.exit(1)

    return info


@dataclass
class RunResult:
    """What run_selection_main() finished with, for a tool that has more to do.

    Attributes:
        args: The parsed command line.
        status: 1 if the run logged a fatal or an error, 0 otherwise.
        proceed: What the last task returned, or None if no task ran; forced to
            False when the run logged a fatal or an error.
    """

    args: argparse.Namespace
    status: int
    proceed: object


def run_selection_main(spec, tasks, argv):
    """Run one checksum or shelf tool: parse the command line, log, perform the task.

    Args:
        spec: The tool's ToolSpec.
        tasks: The tool's task functions, keyed by task name. Each is called with
            one target and its selection.
        argv: The full command line, sys.argv.

    Returns:
        RunResult: What the run finished with. The caller decides the exit status,
        because these tools do not all report one the same way.

    Raises:
        SystemExit: With status 1 if no task was given, or from the command-line
            paths. A task that raises is logged and re-raised.
    """

    parser = _common.build_arg_parser(spec)

    # Parse and validate the command line
    args = parser.parse_args(argv[1:])

    if not args.task:
        print(spec.progname + ' error: Missing task')
        sys.exit(1)

    status = 0

    # Define the logging directory
    _common.resolve_log_root(args)

    # Initialize the logger
    logger = pdslogger.PdsLogger(spec.logname)
    spec.pdsfile_cls.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, spec.progname)
        for make_handler in spec.handler_factories:
            logger.add_handler(make_handler(path))

    # Prepare the list of paths, then the list of tuples (pdsfile, selection)
    abspaths = resolve_holdings_paths(spec, getattr(args, spec.unit),
                                      archives=args.archives)
    info = expand_selection_targets(spec, abspaths)

    # Begin logging and loop through tuples...
    logger.open(' '.join(argv))
    proceed = None
    try:
        for (pdsdir, selection) in info:

            if selection:
                pdsf = pdsdir.child(os.path.basename(selection))
            else:
                pdsf = pdsdir

            # Save logs in up to two places
            method = (UNIT_LOG_PATH_METHOD if pdsf.bundlename
                      else UNITSET_LOG_PATH_METHOD)
            logfiles = _common.log_paths_for(pdsf, method, spec.log_suffix,
                                     task=args.task, dir=spec.progname)

            # Create all the handlers for this level in the logger
            local_handlers = []
            set_log_dirs(logfiles)
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                local_handlers += [make_handler(logdir)
                                   for make_handler in spec.handler_factories]

            # Open the next level of the log
            if len(info) > 1:
                logger.blankline()

            if selection:
                logger.open('Task "' + args.task + '" for selection ' +
                            selection, pdsdir.abspath, handler=local_handlers)
            else:
                logger.open('Task "' + args.task + '" for', pdsdir.abspath,
                            handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                task = args.task
                if task == 'reinitialize' and selection:
                    task = 'update'         # don't erase everything else!

                proceed = tasks[task](pdsdir, selection)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                proceed = False
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        proceed = False
        status = 1
        raise

    finally:
        (fatal, errors, _warnings, _tests) = logger.close()
        if fatal or errors:
            proceed = False
            status = 1

    return RunResult(args=args, status=status, proceed=proceed)
