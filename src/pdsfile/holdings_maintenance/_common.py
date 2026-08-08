##########################################################################################
# pdsfile/holdings_maintenance/_common.py
##########################################################################################

"""The skeleton the pds3 and pds4 halves of a maintenance-tool pair share.

Each pair is two modules that drive a different PdsFile class over a different
vocabulary -- a PDS3 volume or a PDS4 bundle -- and otherwise do the same work.
Everything the two halves would say twice lives here; a ``ToolSpec`` carries what
differs, as data.

This module holds what every family shares: the specification, the command line, and
one of the three drivers. What one family shares lives beside it, in
``_archives_common.py``, ``_shelf_common.py``, ``_indexshelf_common.py`` and
``_linkshelf_common.py``.

**Ten tools are built this way**, five kinds in two flavors: archives, checksums, info
shelves, index shelves and link shelves, each with a ``pds3`` module and a ``pds4``
module. Each of the ten declares a module-level ``SPEC`` and a ``TASKS`` table and hands
both to a driver from its own ``main()``. The four other modules under ``pds3/`` --
``crlf.py``, ``pdsdependency.py``, ``re_validate.py`` and
``shelf_consistency_check.py`` -- parse their own command lines and use nothing here.

**Three drivers serve the ten**, and which one a tool reaches is a property of what its
command line names rather than a choice:

  * ``run_main()``, below, drives the two archive tools and the two link shelf tools.
    A command-line path names a unit or a unit set, ``ToolSpec.expand_target`` turns it
    into a list of units, and each task function is called with one unit.
  * ``_shelf_common.run_selection_main()`` drives the two checksum tools and the two
    info shelf tools, whose command line can also name a single file inside a unit.
    Each task function is called with a unit and a selection.
  * ``_indexshelf_common.run_index_main()`` drives the two index shelf tools, whose
    target is a metadata table rather than a unit.

All three begin at ``setup_run()``, which is the whole of what they share: the parsed
command line and a logger wired to the tool's log roots. The exit status is not part of
that, because the three differ on it -- two of them call ``sys.exit()`` themselves and
``run_selection_main()`` returns a result for its caller to act on.
"""

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

    Nothing here reads a field. A spec is passed down to the shared modules, and every
    read of every field named below happens in one of them; no tool module reads its own
    spec. The reader is named for each field, because "the spec carries it" and "this
    tool acts on it" are different claims: all ten specs set all twelve required fields,
    and a field a tool's own driver and helpers never read has no effect on that tool.

    holdings_sentinel, index_ext and file_log_level are the three where that gap is
    widest. Each is a property of the PDS3/PDS4 flavor rather than of one tool, so all
    five specs of a flavor carry the same value, and each is read for some of them only:
    holdings_sentinel for the checksum, info shelf and link shelf tools, index_ext for
    the index shelf tools alone, file_log_level for the archive and link shelf tools.

    Attributes:
        progname: The tool's name, as it appears in the --help description, in the
            "Missing task" error, and as the subdirectory of each log root. It is
            what the tool calls itself, which for all five pds4 tools is the pds3
            tool's name. Read by build_arg_parser(), setup_run() and all three
            drivers, which pass it as the log path method's dir argument.
        logname: The PdsLogger name, e.g. 'pds.validation.archives'. setup_run()
            constructs the logger with it, and every helper that takes an optional
            logger falls back to PdsLogger.get_logger() on it.
        pdsfile_cls: Pds3File or Pds4File. Every construction of a PdsFile in these
            shared modules goes through it, as do set_log_root() in setup_run() and
            close_all_shelves() in _indexshelf_common.write_indexdict().
        unit: What one command-line target names: 'volume', 'bundle' or 'table'. It
            names the command-line positional, so each driver reads that positional
            back with getattr(args, spec.unit), and it is substituted into the help
            text. _shelf_common.resolve_holdings_paths() also compares it against a
            directory's bundletype_.
        holdings_sentinel: The directory component that separates the holdings root
            from the rest of a path, '/holdings/' or '/pds4-holdings/'. Read by
            _shelf_common.resolve_holdings_paths(), which splits a command-line path
            on it, and by _linkshelf_common.locate_nonlocal_link(), which stops its
            search up the tree at the path component of the same name.
        index_ext: The extension of an index table, '.tab' or '.csv'. Read by
            _indexshelf_common.index_targets() and nowhere else, so it acts on the
            two index shelf tools alone.
        file_log_level: The name of the PdsLogger method the tool writes its
            per-file lines through, 'info' or 'normal'. The two are not
            interchangeable: they render different level names, produce different
            closing summaries, and only 'info' is constrained by an {'info': N}
            limits entry. Read by _archives_common.load_directory_info(),
            make_archive_filter() and validate_tuples(), and by
            _linkshelf_common.write_linkdict().
        description: The parser description, with {progname} and {unit} fields.
        task_help: Help text for each of the five tasks, keyed by task name, with
            {unit} and {units} fields. build_arg_parser() subscripts it once per
            task flag, so a spec that omits one of the five raises rather than
            producing a parser without it.
        positional_help: Help text for the positional argument, with {unit} and
            {units} fields.
        log_path_method: The name of the PdsFile method that builds this tool's log
            path, e.g. 'log_path_for_volume'. Named rather than bound so that every
            tool reaches log_paths_for() the same way. Read by run_main() and by
            _indexshelf_common.run_index_main(). The checksum and info shelf tools
            pick between two methods per target instead, so they leave it at its
            empty default, which their driver never reads.
        log_suffix: The suffix in a log file's basename, e.g. '_archives'. Read by
            all three drivers. An empty string is what a spec whose log path method
            takes no suffix argument carries, which is the index shelf tools' case;
            run_index_main() passes the suffix only when there is one.
        expand_target: Callable (pdsf, path) returning the list of PdsFile objects
            one command-line path resolves to. `path` is the absolute path the
            command line resolved to, for messages. Read by run_main() alone. The
            checksum and info shelf tools expand a path into targets that carry a
            file selection, and the index shelf tools expand it into tables, so
            those six leave it unset and their two drivers never reach for it.
        handler_factories: The pdslogger handler factories to attach at each log
            root, in the order they are added. Read twice per run: setup_run()
            attaches them at the log root, and each driver attaches them again in
            the log directory of every target.
        lskip_for: Callable (pdsdir) returning the number of leading characters
            trimmed from an absolute path to form the archive-relative path. Read
            by _archives_common.load_directory_info(), so it is set by the archive
            tools alone.
        generate_links: Callable (dirpath, old_links=None, *, logger, limits)
            returning the links found in one unit and the latest modification time
            among the files read. Read by the five task functions of
            _linkshelf_common: what a link looks like is the one thing the two
            flavors of that tool do differently, so each keeps its own.
        link_target_regex: The compiled pattern that recognizes a label's reference
            to the file it describes. Read by _linkshelf_common.read_links().
        extra_arguments: Command-line arguments beyond the ones every tool takes,
            as (args, kwargs) pairs passed straight to add_argument. Each help
            string is formatted with {unit} and {units} like the rest. The default
            is empty, which is what the archive, index shelf and link shelf tools
            carry.
        checksum_path_message: What the checksum and info shelf tools print when a
            command-line path names checksum files, which they cannot work on. It
            and the two messages below are read by _shelf_common only, so they stay
            at their empty defaults on the six specs whose tools do not go through
            it.
        invalid_dir_message: What those tools print for a directory that is neither
            a unit nor a unit set.
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
    defaults to never survives this call, and that matters downstream: PdsFile's
    set_log_root() treats None as "no root" but stores an empty string as "/", which
    would build every log path at the filesystem root.

    Parameters:
        args (argparse.Namespace): The parsed command line. Its log attribute is
            overwritten.
    """

    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None


def build_arg_parser(spec):
    """Return the argument parser for one tool.

    The five task flags all write into one 'task' destination, so more than one is
    accepted and the last one given wins; the destination defaults to the empty string,
    which is how setup_run() recognizes a command line that named no task at all.

    The positional argument is named for the spec's unit, so a tool's targets come back
    as args.volume, args.bundle or args.table, and each driver reads it with getattr().

    Parameters:
        spec (ToolSpec): The tool's specification.

    Returns:
        argparse.ArgumentParser: The parser, holding the five task flags, the
        unit positional, --log, --quiet, and any argument the spec adds.

    Raises:
        KeyError: raised by ``__getitem__()`` on the spec's task_help if it does not
            carry an entry for every one of the five task names.
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


def setup_run(spec, argv):
    """Turn a command line into parsed arguments and a logger ready to write.

    Every driver begins here, so the log root, the console handler and the root
    handlers are wired the same way whichever driver a tool reaches. What is left for
    the caller is everything about the targets: this resolves no path, opens no log
    level and touches no holdings tree.

    Two things are done to the class rather than to the logger, and outlive the call:
    the parsed args.log is written onto the spec's PdsFile class as its log root, and
    the console handler is added unless --quiet was given.

    Parameters:
        spec (ToolSpec): The tool's specification.
        argv (list): The full command line, sys.argv.

    Returns:
        tuple: The parsed command line, and the PdsLogger with the tool's log root
        set and its root handlers attached. The exit status is not among them: each
        driver owns its own status variable, and the three do not agree on what to
        do with it, so it belongs to the run the caller is about to make rather than
        to this setup. No log level is open on the returned logger either; the
        caller opens the first one.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 when the command line names no
            task, so a caller that returns from here has one to run; and from
            ``parse_args()``, with status 0 for --help and 2 for a command line it
            cannot classify.
    """

    parser = build_arg_parser(spec)

    # Parse and validate the command line
    args = parser.parse_args(argv[1:])

    if not args.task:
        print(spec.progname + ' error: Missing task')
        sys.exit(1)

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

    return (args, logger)


def log_paths_for(pdsf, method, *args, **kwargs):
    """Return the paths one target's run writes its log to, in order.

    A run logs to its default place and, when a log root is configured, to a
    parallel place as well. The two are the same path when no log root is
    configured, so the result is one path or two, the default place first.

    Both are built under one pinned time tag. The tag has one-second resolution and
    every caller builds the pair with two calls, so without the pin a pair whose
    calls straddle a second boundary is dated a second apart -- which also defeats
    the equality test that spots the duplicate, and writes one run's log twice.

    Parameters:
        pdsf: The PdsFile the log is about. Its class carries the pin.
        method (str): The name of its log_path_for_* method, which builds each path.
        *args: Positional arguments for that method, e.g. the log file suffix.
        **kwargs: Keyword arguments for it, e.g. task= and dir=.

    Returns:
        list[str]: One or two log file paths, the default place first.

    Raises:
        AttributeError: from the ``getattr()`` that looks the method up, if the object
            has no method of that name.
        ValueError: from either call to the looked-up method, written ``build()`` here,
            for a place option it does not recognize, and, where the method is
            log_path_for_index, for a PdsFile that is not an index file.
    """

    build = getattr(pdsf, method)
    with type(pdsf)._pinned_log_timetag():
        paths = [build(*args, place='default', **kwargs),
                 build(*args, place='parallel', **kwargs)]

    if paths[0] == paths[1]:
        return paths[:1]

    return paths


# The log directories a superseded checksum or shelf file is versioned into. A run
# fills this in for each target it is about to work on: run_main below, and
# _shelf_common.run_selection_main, do it for the eight tools between them, and
# any other tool that versions a file does it in its own main(). A process that
# never calls set_log_dirs leaves this empty, and then _shelf_common.move_old()
# versions nothing. It lives here, beside the function that builds the paths, so
# that a driver in any of these modules can record them.
LOGDIRS = []


def set_log_dirs(logfiles):
    """Record the log directories a superseded file is versioned into.

    LOGDIRS is replaced outright rather than added to, so each target's call discards
    the previous target's directories and only the current target's are in effect.

    Parameters:
        logfiles (list): The log file paths of the target about to be worked on. The
            directory of each is what a superseded file is copied into.
    """

    global LOGDIRS
    LOGDIRS = [os.path.split(logfile)[0] for logfile in logfiles]


def run_main(spec, tasks, argv):
    """Run one tool: parse the command line, set up logging, perform the task.

    This is the driver the two archive tools and the two link shelf tools reach. It
    expands every command-line path through the spec's expand_target, so a tool on this
    driver has to set that field, and it calls each task with one PdsFile and nothing
    else.

    Every path is resolved and expanded before the run's first log level is opened, so
    a command line naming a path that does not exist exits before any per-target log
    file is created. From then on each target gets its own log level, its own file
    handlers, and its own LOGDIRS entries.

    This function does not return. Every path out of it is an exception or an exit.

    Parameters:
        spec (ToolSpec): The tool's specification.
        tasks (dict): The tool's task functions, keyed by task name. Each is called
            with one target PdsFile.
        argv (list): The full command line, sys.argv.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 for a command-line path that
            does not exist, and on a normal return with status 1 if the run logged a
            fatal or an error and 0 otherwise. A task that raises is logged and
            re-raised instead, so the original exception propagates and the closing
            ``sys.exit()`` is not reached; the status the finally clause sets in that
            case is discarded with the frame.
    """

    (args, logger) = setup_run(spec, argv)

    status = 0

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
