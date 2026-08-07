##########################################################################################
# pdsfile/holdings_maintenance/_common.py
#
# The skeleton the pds3 and pds4 halves of a maintenance-tool pair share.
#
# Each pair is two modules that drive a different PdsFile class over a different
# vocabulary -- a PDS3 volume or a PDS4 bundle -- and otherwise do the same work.
# Everything the two halves would say twice lives here; a ToolSpec carries what
# differs, as data.
#
# This module holds what every family shares: the specification, the command line,
# and the driver. What one family shares lives beside it, in _archives_common.py
# and _shelf_common.py.
##########################################################################################

import argparse
import os
import re
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

    index_ext and holdings_sentinel are properties of the PDS3/PDS4 flavor rather
    than of one tool, so every spec of that flavor carries the same value whether or
    not its own tool reads it.

    Attributes:
        progname: The tool's name, as it appears in the --help description, in the
            "Missing task" error, and as the subdirectory of each log root. It is
            what the tool calls itself, which for the pds4 index and link shelf
            tools is the pds3 name.
        logname: The PdsLogger name, e.g. 'pds.validation.archives'.
        pdsfile_cls: Pds3File or Pds4File.
        unit: What one command-line target names: 'volume', 'bundle' or 'table'.
            Names the command-line positional, and is substituted into the help
            text.
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
            tool reaches log_paths_for() the same way. Read by run_main; the
            checksum and shelf tools pick between two methods per target instead,
            so they leave it empty.
        log_suffix: The suffix in a log file's basename, e.g. '_archives'.
        expand_target: Callable (pdsf, path) returning the list of PdsFile objects
            one command-line path resolves to. `path` is the absolute path the
            command line resolved to, for messages. Read by run_main; the checksum
            and shelf tools expand a path into targets that carry a file selection,
            so they leave it unset.
        handler_factories: The pdslogger handler factories to attach at each log
            root, in the order they are added.
        lskip_for: Callable (pdsdir) returning the number of leading characters
            trimmed from an absolute path to form the archive-relative path. Used
            by the archive tools.
        generate_links: Callable (dirpath, old_links=None, *, logger, limits)
            returning the links found in one unit and the latest modification time
            among the files read. Used by the link shelf tools, whose shared tasks
            call it: what a link looks like is the one thing the two flavors of
            that tool do differently, so each keeps its own.
        link_target_regex: The compiled pattern that recognizes a label's reference
            to the file it describes. Used by the link shelf tools.
        extra_arguments: Command-line arguments beyond the ones every tool takes,
            as (args, kwargs) pairs passed straight to add_argument. Each help
            string is formatted with {unit} and {units} like the rest.
        checksum_path_message: What the checksum and shelf tools print when a
            command-line path names checksum files, which they cannot work on.
        invalid_dir_message: What they print for a directory that is neither a unit
            nor a unit set.
        invalid_file_message: What they print for a file that is neither an archive
            file nor a top-level file of a unit.
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
    log_suffix: str
    handler_factories: tuple
    log_path_method: str = ''
    expand_target: Callable | None = None
    lskip_for: Callable | None = None
    generate_links: Callable | None = None
    link_target_regex: re.Pattern | None = None
    extra_arguments: tuple = ()
    checksum_path_message: str = ''
    invalid_dir_message: str = ''
    invalid_file_message: str = ''


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
        description=spec.description.format(progname=spec.progname, unit=unit,
                                            units=units))

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
        kwargs = dict(kwargs)
        kwargs['help'] = kwargs['help'].format(unit=unit, units=units)
        parser.add_argument(*args, **kwargs)

    return parser


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


# The log directories a superseded checksum or shelf file is versioned into. A run
# fills this in for each target it is about to work on -- either driver below for a
# tool on one of them, each remaining tool's own main() for the rest; a process that
# never calls set_log_dirs leaves it empty, and then _shelf_common.move_old()
# versions nothing. It lives here, beside the function that builds the paths, so
# that every driver can record them.
LOGDIRS = []


def set_log_dirs(logfiles):
    """Record the log directories a superseded file is versioned into.

    Args:
        logfiles: The log file paths of the target about to be worked on. The
            directory of each is what a superseded file is copied into.
    """

    global LOGDIRS
    LOGDIRS = [os.path.split(logfile)[0] for logfile in logfiles]


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
            set_log_dirs(logfiles)
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
