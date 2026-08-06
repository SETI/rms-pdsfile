##########################################################################################
# pdsfile/holdings_maintenance/_common.py
#
# The skeleton the pds3 and pds4 halves of a maintenance-tool pair share.
#
# Each pair is two modules that drive a different PdsFile class over a different
# vocabulary -- a PDS3 volume or a PDS4 bundle -- and otherwise do the same work.
# Everything the two halves would say twice lives here; a ToolSpec carries what
# differs, as data.
##########################################################################################

import argparse
import glob
import hashlib
import os
import re
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass

import pdslogger

# The environment variable naming the root of the duplicate log tree.
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Names of files kept alongside the originals, which no tool treats as content.
BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')


##########################################################################################
# Tool specification
##########################################################################################

@dataclass(kw_only=True)
class ToolSpec:
    """Everything that differs between the two halves of a maintenance-tool pair.

    A field belongs here only if it is data: a class, a string, a tuple of logger
    handler factories, or a callable that computes a path or a list of targets.
    Where the two halves differ in what they *do* -- how an archive is written, how
    a missing archive file is reported -- the code stays in the tool module and the
    spec says nothing about it.

    Two fields are declared for tools that are not on this core yet and are read
    nowhere today: holdings_sentinel, which the checksums and infoshelf tools use to
    split a command-line path, and index_ext, which the indexshelf tools use to
    find and to recognize an index table. Both are properties of the PDS3/PDS4
    flavor rather than of one tool, so every spec of that flavor carries the same
    value, whether or not its own tool reads it.

    Attributes:
        progname: The tool's name, as it appears in the --help description, in the
            "Missing task" error, and as the subdirectory of each log root.
        logname: The PdsLogger name, e.g. 'pds.validation.archives'.
        pdsfile_cls: Pds3File or Pds4File.
        unit: 'volume' or 'bundle'. Names the command-line positional, and is
            substituted into the help text.
        holdings_sentinel: The directory component that separates the holdings root
            from the rest of a path, '/holdings/' or '/pds4-holdings/'.
        index_ext: The extension of an index table, '.tab' or '.csv'.
        file_log_level: The name of the PdsLogger method the tool writes its
            per-file lines through, 'info' or 'normal'. The two are not
            interchangeable: they render different level names, produce different
            closing summaries, and only 'info' is constrained by an {'info': N}
            limits entry.
        description: The parser description, with {progname} and {unit} fields.
        task_help: Help text for each of the five tasks, keyed by task name, with
            {unit} and {units} fields.
        positional_help: Help text for the positional argument, with {unit} and
            {units} fields.
        log_path_method: The name of the PdsFile method that builds this tool's log
            path, e.g. 'log_path_for_volume'. Named rather than bound so that every
            tool reaches log_paths_for() the same way.
        log_suffix: The suffix in a log file's basename, e.g. '_archives'.
        expand_target: Callable (pdsf, path) returning the list of PdsFile objects
            one command-line path resolves to. `path` is the absolute path the
            command line resolved to, for messages.
        handler_factories: The pdslogger handler factories to attach at each log
            root, in the order they are added.
        lskip_for: Callable (pdsdir) returning the number of leading characters
            trimmed from an absolute path to form the archive-relative path. Used
            by the archive tools.
        extra_arguments: Command-line arguments beyond the ones every tool takes,
            as (args, kwargs) pairs passed straight to add_argument.
    """

    progname: str
    logname: str
    pdsfile_cls: type
    unit: str
    holdings_sentinel: str
    index_ext: str
    file_log_level: str
    description: str
    task_help: dict
    positional_help: str
    log_path_method: str
    log_suffix: str
    expand_target: Callable
    handler_factories: tuple
    lskip_for: Callable | None = None
    extra_arguments: tuple = ()


##########################################################################################
# Command line
##########################################################################################

# The task flags, in the order they are declared and so in the order --help lists
# them. Each is an independent store_const action writing into the same 'task'
# destination, which is why more than one of them is accepted and the last one on
# the command line wins.
TASK_FLAGS = ((('--initialize', '--init'), 'initialize'),
              (('--reinitialize', '--reinit'), 'reinitialize'),
              (('--validate',), 'validate'),
              (('--repair',), 'repair'),
              (('--update',), 'update'))

LOG_HELP = ('Optional root directory for a duplicate of the log files. If not '
            'specified, the value of environment variable "{env}" is used. In '
            'addition, individual logs are written into the "logs" directory '
            'parallel to "holdings". Logs are created inside the "{progname}" '
            'subdirectory of each log root directory.')

QUIET_HELP = 'Do not also log to the terminal.'


def resolve_log_root(args):
    """Settle where the duplicate log tree goes, in place on the parsed command line.

    An unset --log falls back to the environment variable, and an unset variable
    leaves no log root at all. Either way the rest of a tool reads one of two
    states: a path, or None for "no duplicate tree". The empty string the parser
    defaults to never survives this call.

    Args:
        args: The parsed command line. Its log attribute is overwritten.
    """

    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None


def build_arg_parser(spec):
    """Return the argument parser for one tool.

    Args:
        spec: The tool's ToolSpec.

    Returns:
        argparse.ArgumentParser: The parser, holding the five task flags, the
        volume/bundle positional, --log, --quiet, and any argument the spec adds.
    """

    unit = spec.unit
    units = unit + 's'

    parser = argparse.ArgumentParser(
        description=spec.description.format(progname=spec.progname, unit=unit))

    for flags, task in TASK_FLAGS:
        parser.add_argument(*flags, const=task,
                            default='', action='store_const', dest='task',
                            help=spec.task_help[task].format(unit=unit, units=units))

    parser.add_argument(unit, nargs='+', type=str,
                        help=spec.positional_help.format(unit=unit, units=units))

    parser.add_argument('--log', '-l', type=str, default='',
                        help=LOG_HELP.format(env=LOGROOT_ENV, progname=spec.progname))

    parser.add_argument('--quiet', '-q', action='store_true', help=QUIET_HELP)

    for args, kwargs in spec.extra_arguments:
        parser.add_argument(*args, **kwargs)

    return parser


def reject_checksum_and_archive_paths(pdsf, path):
    """Exit when a command-line path names checksum files or archive files.

    Args:
        pdsf: The PdsFile the path resolved to.
        path: The absolute path the command line resolved to, for the message.
    """

    if pdsf.checksums_:
        print('No archives for checksum files: ' + path)
        sys.exit(1)

    if pdsf.archives_:
        print('No archives for archive files: ' + path)
        sys.exit(1)


def log_paths_for(pdsf, method, *args, **kwargs):
    """Return the paths one target's run writes its log to, in order.

    A run logs to its default place and, when a log root is configured, to a
    parallel place as well. The two are the same path when no log root is
    configured, so the result is one path or two, the default place first.

    Both are built under one pinned time tag. The tag has one-second resolution and
    every caller builds the pair with two calls, so without the pin a pair whose
    calls straddle a second boundary is dated a second apart -- which also defeats
    the equality test that spots the duplicate, and writes one run's log twice.

    Args:
        pdsf: The PdsFile the log is about. Its class carries the pin.
        method: The name of its log_path_for_* method, which builds each path.
        *args: Positional arguments for that method, e.g. the log file suffix.
        **kwargs: Keyword arguments for it, e.g. task= and dir=.

    Returns:
        list[str]: One or two log file paths, the default place first.
    """

    build = getattr(pdsf, method)
    with type(pdsf)._pinned_log_timetag():
        paths = [build(*args, place='default', **kwargs),
                 build(*args, place='parallel', **kwargs)]

    if paths[0] == paths[1]:
        return paths[:1]

    return paths


def run_main(spec, tasks, argv):
    """Run one tool: parse the command line, set up logging, perform the task.

    Args:
        spec: The tool's ToolSpec.
        tasks: The tool's task functions, keyed by task name. Each is called with
            one target PdsFile.
        argv: The full command line, sys.argv.

    Raises:
        SystemExit: On a normal return, with status 1 if the run logged a fatal or
            an error and 0 otherwise. A task that raises is logged and re-raised
            instead, so the original exception propagates and sys.exit is not
            reached.
    """

    parser = build_arg_parser(spec)

    # Parse and validate the command line
    args = parser.parse_args(argv[1:])

    if not args.task:
        print(spec.progname + ' error: Missing task')
        sys.exit(1)

    status = 0

    # Define the logging directory
    resolve_log_root(args)

    # Initialize the logger
    logger = pdslogger.PdsLogger(spec.logname)
    spec.pdsfile_cls.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, spec.progname)
        for make_handler in spec.handler_factories:
            logger.add_handler(make_handler(path))

    # Generate a list of pdsfiles for the target directories
    pdsdirs = []
    for path in getattr(args, spec.unit):

        path = os.path.abspath(path)
        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        pdsf = spec.pdsfile_cls.from_abspath(path)
        pdsdirs += spec.expand_target(pdsf, path)

    # Begin logging and loop through pdsdirs...
    logger.open(' '.join(argv))
    try:
        for pdsdir in pdsdirs:

            # Save logs in up to two places
            logfiles = log_paths_for(pdsdir, spec.log_path_method, spec.log_suffix,
                                     task=args.task, dir=spec.progname)

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                local_handlers += [make_handler(logdir)
                                   for make_handler in spec.handler_factories]

            # Open the next level of the log
            if len(pdsdirs) > 1:
                logger.blankline()

            logger.open('Task ' + args.task + ' for', pdsdir.abspath,
                                                      handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                tasks[args.task](pdsdir)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, _warnings, _tests) = logger.close()
        if fatal or errors:
            status = 1

    sys.exit(status)


##########################################################################################
# Archive tools
##########################################################################################

# Default limits
LOAD_DIRECTORY_INFO_LIMITS = {'info': 100}
READ_ARCHIVE_INFO_LIMITS = {'info': 100}
WRITE_ARCHIVE_LIMITS = {'info': -1, 'dot_': 100}
VALIDATE_TUPLES_LIMITS = {'info': 100}

ARCHIVE_DESCRIPTION = ('{progname}: Create, maintain and validate .tar.gz archives of '
                       'PDS {unit} directory trees.')

ARCHIVE_TASK_HELP = {
    'initialize': 'Create a .tar.gz archive for a {unit}. Abort if the archive '
                  'already exists.',
    'reinitialize': 'Create a .tar.gz archive for a {unit}. Replace the archive if '
                    'it already exists.',
    'validate': 'Validate every file in a {unit} against the contents of its .tar.gz '
                'archive. Files match if they have identical byte counts and '
                'modification dates; file contents are not compared.',
    'repair': 'Validate every file in a {unit} against the contents of its .tar.gz '
              'archive. If any file has changed, write a new archive.',
    'update': 'Search a {unit} set directory for any new {units} and create a new '
              'archive file for each of them; do not update any pre-existing archive '
              'files.',
}

ARCHIVE_POSITIONAL_HELP = ('The path to the root of the {unit} or {unit} set. For a '
                           '{unit} set, all the {unit} directories inside it are '
                           'handled in sequence.')


def load_directory_info(spec, pdsdir, *, logger=None, limits=None):
    """Generate a list of tuples (abspath, dirpath, nbytes, mod time)
    recursively for the given directory tree.
    """

    if limits is None:
        limits = {}

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsdir.root_)
    file_log = getattr(logger, spec.file_log_level)

    merged_limits = LOAD_DIRECTORY_INFO_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Generating file info', dirpath, limits=merged_limits)

    try:
        lskip = spec.lskip_for(pdsdir)

        tuples = [(dirpath, dirpath[lskip:], 0, 0)]
        for (path, dirs, files) in os.walk(dirpath):

            # Load files
            for file in files:
                abspath = os.path.join(path, file)

                if file == '.DS_Store':         # skip .DS_Store files
                    logger.ds_store('.DS_Store skipped', abspath)
                    continue

                if file.startswith('._'):       # skip dot-underscore files
                    logger.dot_underscore('._* file skipped', abspath)
                    continue

                if BACKUP_FILENAME.match(file) or ' copy' in file:
                    logger.error('Backup file skipped', abspath)
                    continue

                if '/.' in abspath:             # flag invisible files
                    logger.invisible('Invisible file', abspath)

                nbytes = os.path.getsize(abspath)
                modtime = os.path.getmtime(abspath)
                file_log('File info generated', abspath)

                tuples.append((abspath, abspath[lskip:], nbytes, modtime))

            # Load directories
            for dirname in dirs:
                abspath = os.path.join(path, dirname)

                if dirname.startswith('._'):    # skip dot-underscore files
                    logger.dot_underscore('._* directory skipped', abspath)
                    continue

                if '/.' in abspath:             # flag invisible files
                    logger.invisible('Invisible directory', abspath)

                file_log('Directory info generated', abspath)

                tuples.append((abspath, abspath[lskip:], 0, 0))

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return tuples


def make_archive_filter(spec, logger, archive_invisibles):
    """Return the tarfile member filter the archive writers add members through.

    Args:
        spec: The tool's ToolSpec.
        logger: The logger the filter reports to.
        archive_invisibles: True to archive invisible files, False to skip them.

    Returns:
        callable: A tarfile filter, returning the member to archive it and None to
        skip it.
    """

    file_log = getattr(logger, spec.file_log_level)

    def archive_filter(member):
        """Internal function to filter filenames"""

        # Erase user info
        member.uid = member.gid = 0
        member.uname = member.gname = "root"

        # Check for valid file names
        basename = os.path.basename(member.name)
        if basename == '.DS_Store':
            logger.ds_store('.DS_Store file skipped', member.name)
            return None

        if basename.startswith('._') or '/._' in member.name:
            logger.dot_underscore('._* file skipped', member.name)
            return None

        if basename.startswith('.') or '/.' in member.name:
            if archive_invisibles:
                logger.invisible('Invisible file archived', member.name)
                return member
            else:
                logger.invisible('Invisible file skipped', member.name)
                return None

        file_log('File archived', member.name)
        return member

    return archive_filter


def validate_tuples(spec, dir_tuples, tar_tuples, *, logger=None, limits=None):
    """Validate the directory list of tuples against the list from the tarfile.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    file_log = getattr(logger, spec.file_log_level)

    merged_limits = VALIDATE_TUPLES_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Validating file information', limits=merged_limits)

    valid = True
    try:
        tardict = {}
        for (abspath, dirpath, nbytes, modtime) in tar_tuples:
            tardict[abspath] = (dirpath, nbytes, modtime)

        for (abspath, dirpath, nbytes, modtime) in dir_tuples:
            if abspath not in tardict:
                logger.error('Missing from tar file', abspath)
                valid = False

            elif (dirpath, nbytes, modtime) != tardict[abspath]:

                if nbytes != tardict[abspath][1]:
                    logger.error('Byte count mismatch: ' +
                                 str(nbytes) + ' (filesystem) vs. ' +
                                 str(tardict[abspath][1]) + ' (tarfile)', abspath)
                    valid = False

                if abs(modtime - tardict[abspath][2]) > 1:
                    logger.error('Modification time mismatch: ' +
                                 str(modtime) + ' (filesystem) vs. ' +
                                 str(tardict[abspath][2]) + ' (tarfile)', abspath)
                    valid = False

                del tardict[abspath]

            else:
                file_log('Validated', dirpath)
                del tardict[abspath]

        keys = list(tardict.keys())
        keys.sort()
        for abspath in keys:
            logger.error('Missing from directory', abspath)
            valid = False

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        logger.close()

    return valid


##########################################################################################
# Checksum and shelf file tools
##########################################################################################

# The PdsLogger name each tool kind logs under. Both flavors of a kind share one.
CHECKSUMS_LOGNAME = 'pds.validation.checksums'
INFOSHELF_LOGNAME = 'pds.validation.fileinfo'
LINKSHELF_LOGNAME = 'pds.validation.links'


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

# The log directories a superseded checksum or shelf file is versioned into. A tool's
# main() fills this in for each target it is about to work on; a process that never
# calls set_log_dirs leaves it empty, and then move_old() versions nothing.
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
