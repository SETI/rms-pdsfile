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
import os
import re
import sys

import pdslogger

# The environment variable naming the root of the duplicate log tree.
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Names of files kept alongside the originals, which no tool treats as content.
BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')


##########################################################################################
# Tool specification
##########################################################################################

class ToolSpec:
    """Everything that differs between the two halves of a maintenance-tool pair.

    A field belongs here only if it is data: a class, a string, a tuple of logger
    handler factories, or a callable that computes a path or a list of targets.
    Where the two halves differ in what they *do* -- how an archive is written, how
    a missing archive file is reported -- the code stays in the tool module and the
    spec says nothing about it.

    Attributes:
        progname: The tool's name, as it appears in the --help description, in the
            "Missing task" error, and as the subdirectory of each log root.
        logname: The PdsLogger name, e.g. 'pds.validation.archives'.
        pdsfile_cls: Pds3File or Pds4File.
        unit: 'volume' or 'bundle'. Names the command-line positional, and is
            substituted into the help text.
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
        log_path_for: Callable (pdsdir, task, place='default') returning the path of
            the log file for one target.
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

    def __init__(self, *, progname, logname, pdsfile_cls, unit, file_log_level,
                 description, task_help, positional_help, log_path_for, expand_target,
                 handler_factories, lskip_for=None, extra_arguments=()):
        self.progname = progname
        self.logname = logname
        self.pdsfile_cls = pdsfile_cls
        self.unit = unit
        self.file_log_level = file_log_level
        self.description = description
        self.task_help = task_help
        self.positional_help = positional_help
        self.log_path_for = log_path_for
        self.expand_target = expand_target
        self.handler_factories = handler_factories
        self.lskip_for = lskip_for
        self.extra_arguments = extra_arguments


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
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

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
            logfiles = {spec.log_path_for(pdsdir, args.task),
                        spec.log_path_for(pdsdir, args.task, place='parallel')}

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
