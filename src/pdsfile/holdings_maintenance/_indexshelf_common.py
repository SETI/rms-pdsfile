##########################################################################################
# pdsfile/holdings_maintenance/_indexshelf_common.py
#
# What the two index shelf tools share.
#
# These shelve the row numbers of each product in a metadata index table. Their
# target is a table file or a metadata directory rather than a unit, and their log
# path is built from the table's own logical path, so they run on the driver at the
# end of this module rather than on either of the two in _common.py and
# _shelf_common.py.
##########################################################################################

import datetime
import functools
import glob
import os
import pickle
import sys

import pdslogger
import pdstable

from pdsfile.holdings_maintenance import _common

# The PdsLogger name both flavors of this tool log under.
INDEXSHELF_LOGNAME = 'pds.validation.indexshelf'

INDEXSHELF_DESCRIPTION = ('{progname}: Create, maintain and validate shelf files '
                          'containing row lookup information for index files.')

INDEXSHELF_TASK_HELP = {
    'initialize': 'Create an indexshelf file for an index or for an entire metadata '
                  'directory. Abort if the file already exists.',
    'reinitialize': 'Create an indexshelf file for an index or for an entire metadata '
                    'directory. Replace any files that already exists.',
    'validate': 'Validate an indexshelf file or metadata directory.',
    'repair': 'Validate an index shelf file; replace only if necessary. If the shelf '
              "file content is correct but it is older than either the file or the "
              "label, update the shelf file's modification date.",
    'update': 'Search a metadata directory for any new index files and add create an '
              'index shelf file for each one. Existing index shelf files are not '
              'checked.',
}

INDEXSHELF_POSITIONAL_HELP = 'Path to an index file or metadata directory.'

# Default limits
GENERATE_INDEXDICT_LIMITS = {}
WRITE_INDEXDICT_LIMITS = {}
LOAD_INDEXDICT_LIMITS = {}


def generate_indexdict(spec, pdsf, *, logger=None, limits=None):
    """Return the row numbers of every product in one index table, and its date.

    Args:
        spec: The tool's ToolSpec.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits: Message limits for this scope, merged over the defaults.

    Returns:
        tuple: The {filename key: list of row numbers} dictionary, and the later of
        the table's and its label's modification times.

    Raises:
        OSError: If the table or its label cannot be read.
        ValueError: If the table disagrees with its label.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsf.root_)

    merged_limits = GENERATE_INDEXDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Tabulating index rows for', pdsf.abspath, limits=merged_limits)

    try:
        table = pdstable.PdsTable(label_file=pdsf.label_abspath,
                                  filename_keylen=pdsf.filename_keylen)

        table.index_rows_by_filename_key()      # fills in table.filename_keys
        childnames = table.filename_keys
        index_dict = {c:table.row_indices_by_filename_key(c)
                      for c in childnames}

        logger.info('Rows tabulated', str(len(index_dict)), force=True)

        latest_mtime = max(os.path.getmtime(pdsf.abspath),
                           os.path.getmtime(pdsf.label_abspath))
        dt = datetime.datetime.fromtimestamp(latest_mtime)
        logger.info('Latest index file modification date',
                    dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

    except (OSError, ValueError) as e:
        logger.error(str(e))
        raise e

    finally:
        _ = logger.close()

    return (index_dict, latest_mtime)


def write_indexdict(spec, pdsf, index_dict, *, logger=None, limits=None):
    """Write a new shelf file, and its Python sidecar, for the rows of one index.

    Args:
        spec: The tool's ToolSpec.
        pdsf: The index table.
        index_dict: The row numbers, as generate_indexdict() returned them.
        logger: The logger to report through. Defaults to the tool's own.
        limits: Message limits for this scope, merged over the defaults.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsf.root_)

    merged_limits = WRITE_INDEXDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing index shelf file info for', pdsf.abspath,
                limits=merged_limits)

    try:
        spec.pdsfile_cls.close_all_shelves() # prevents using a cached shelf file

        shelf_path = pdsf.indexshelf_abspath
        logger.info('Index shelf file', shelf_path)

        # Create parent directory if necessary
        parent = os.path.split(shelf_path)[0]
        if not os.path.exists(parent):
            logger.info('Creating parent directory', parent)
            os.makedirs(parent)

        # Write the pickle file
        with open(shelf_path, 'wb') as f:
            pickle.dump(index_dict, f)

        # Write the Python file
        python_path = shelf_path.rpartition('.')[0] + '.py'
        logger.info('Writing Python file', python_path)

        # Determine the maximum length of the keys
        len_path = 0
        for key in index_dict:
            len_path = max(len_path, len(key))

        name = os.path.basename(shelf_path).rpartition('.')[0]
        with open(python_path, 'w', encoding='latin-1') as f:
            f.write(name + ' = {\n')
            for key in index_dict:
                f.write('    "%s: ' % (key + '"' + (len_path-len(key)) * ' '))

                rows = index_dict[key]
                if len(rows) == 1:
                    f.write(f'{rows[0]:d},\n')
                else:
                    f.write('(')
                    for row in rows[:-1]:
                        f.write(f'{row:d}, ')
                    f.write(f'{rows[-1]:d}),\n')

            f.write('}\n\n')

        logger.info('Two files written')

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()


def load_indexdict(spec, pdsf, *, logger=None, limits=None):
    """Return the row numbers an index shelf file already holds.

    Args:
        spec: The tool's ToolSpec.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits: Message limits for this scope, merged over the defaults.

    Returns:
        dict: The shelved row numbers, empty if there is no shelf file.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsf.root_)

    merged_limits = LOAD_INDEXDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading index shelf file for', pdsf.abspath,
                limits=merged_limits)

    try:
        shelf_path = pdsf.indexshelf_abspath
        logger.info('Index shelf file', shelf_path)

        if not os.path.exists(shelf_path):
            logger.error('Index shelf file not found', shelf_path)
            return {}

        with open(shelf_path, 'rb') as f:
            index_dict = pickle.load(f)

        logger.info('Shelf records loaded', str(len(index_dict)))

    except pickle.PickleError as e:
        logger.exception(e)
        raise

    finally:
        logger.close()

    return index_dict


def validate_indexdict(spec, pdsf, tabdict, shelfdict, *, logger=None):
    """Report every way the table and its shelf disagree.

    Args:
        spec: The tool's ToolSpec.
        pdsf: The index table.
        tabdict: The row numbers read from the table.
        shelfdict: The row numbers read from the shelf.
        logger: The logger to report through. Defaults to the tool's own.
    """

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsf.root_)
    logger.info('Validating index file for', pdsf.abspath)

    if tabdict == shelfdict:
        logger.info('Validation complete')
        return

    logger.error('Validation failed for', pdsf.abspath)
    for key, value in tabdict.items():
        if key not in shelfdict:
            logger.error('not in shelf: %s', key)
        elif (shelfval := shelfdict[key]) != value:
            logger.error('key mismatch: %s\n'
                         '    table: %s\n'
                         '    shelf: %s', key, value, shelfval)
    for key in shelfdict:
        if key not in tabdict:
            logger.error('not in table: %s', key)


##########################################################################################
# Index shelf tasks
##########################################################################################

def index_initialize(spec, pdsf, *, logger=None, limits=None):
    """Shelve one index table, refusing to replace a shelf that is already there."""

    if limits is None:
        limits = {}

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file does not exist
    if os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.error('Index shelf file already exists', shelf_path)
        return

    # Generate info
    (index_dict, _) = generate_indexdict(spec, pdsf, logger=logger, limits=limits)
    if index_dict is None:
        return

    # Save info file
    write_indexdict(spec, pdsf, index_dict, logger=logger, limits=limits)


def index_reinitialize(spec, pdsf, *, logger=None, limits=None):
    """Shelve one index table, replacing whatever shelf is there."""

    if limits is None:
        limits = {}

    shelf_path = pdsf.indexshelf_abspath

    # Warn if shelf file does not exist
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.warning('Index shelf file does not exist; initializing', shelf_path)
        index_initialize(spec, pdsf, logger=logger, limits=limits)
        return

    # Generate info
    (index_dict, _) = generate_indexdict(spec, pdsf, logger=logger, limits=limits)
    if not index_dict:
        return

    # Save info file
    write_indexdict(spec, pdsf, index_dict, logger=logger, limits=limits)


def index_validate(spec, pdsf, *, logger=None, limits=None):
    """Report every way one index table and its shelf disagree."""

    if limits is None:
        limits = {}

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file exists
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.error('Index shelf file does not exist', shelf_path)
        return

    (table_indexdict, _) = generate_indexdict(spec, pdsf, logger=logger, limits=limits)
    if table_indexdict is None:
        return

    shelf_indexdict = load_indexdict(spec, pdsf, logger=logger, limits=limits)
    if not shelf_indexdict:
        return

    # Validate
    validate_indexdict(spec, pdsf, table_indexdict, shelf_indexdict, logger=logger)


def index_repair(spec, pdsf, *, logger=None, limits=None):
    """Rewrite one index shelf if it disagrees with its table, or re-date it if not."""

    if limits is None:
        limits = {}

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file exists
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.warning('Index shelf file does not exist; initializing', shelf_path)
        index_initialize(spec, pdsf, logger=logger, limits=limits)
        return

    (table_indexdict, latest_mtime) = generate_indexdict(spec, pdsf, logger=logger,
                                                         limits=limits)
    if not table_indexdict:
        return

    shelf_indexdict = load_indexdict(spec, pdsf, logger=logger, limits=limits)
    if not shelf_indexdict:
        return

    # Compare
    canceled = (table_indexdict == shelf_indexdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)

        shelf_pypath = shelf_path.replace('.pickle', '.py')
        shelf_mtime = min(os.path.getmtime(shelf_path),
                          os.path.getmtime(shelf_pypath))
        if latest_mtime > shelf_mtime:
            logger.info('!!! Index shelf file content is up to date',
                        shelf_path, force=True)

            dt = datetime.datetime.fromtimestamp(latest_mtime)
            logger.info('!!! Index file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            dt = datetime.datetime.fromtimestamp(shelf_mtime)
            logger.info('!!! Index shelf file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            delta = latest_mtime - shelf_mtime
            if delta >= 86400/10:
                logger.info('!!! Index shelf file is out of date %.1f days' %
                            (delta / 86400.), force=True)
            else:
                logger.info('!!! Index shelf file is out of date %.1f minutes' %
                        (delta / 60.), force=True)

            dt = datetime.datetime.now()
            os.utime(shelf_path)
            os.utime(shelf_pypath)
            logger.info('!!! Time tag on index shelf files set to',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

        else:
            logger.info('!!! Index shelf file is up to date; repair canceled',
                        shelf_path, force=True)

        return

    # Write new info
    write_indexdict(spec, pdsf, table_indexdict, logger=logger, limits=limits)


def index_update(spec, pdsf, *, logger=None, limits=None):
    """Shelve one index table if it has no shelf, and leave any existing shelf alone."""

    if limits is None:
        limits = {}

    shelf_path = pdsf.indexshelf_abspath
    if os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.info('!!! Index shelf file exists; not updated', pdsf.abspath)

    else:
        index_initialize(spec, pdsf, logger=logger, limits=limits)


_INDEX_TASKS = {'initialize': index_initialize,
                'reinitialize': index_reinitialize,
                'validate': index_validate,
                'repair': index_repair,
                'update': index_update}


def index_tasks(spec):
    """Return one tool's index shelf task table, with its spec bound into each task.

    Args:
        spec: The tool's ToolSpec.

    Returns:
        dict: The task functions, keyed by task name, each taking one index table.
    """

    return {name: functools.partial(task, spec) for name, task in _INDEX_TASKS.items()}


##########################################################################################
# Command line for the index shelf tools
##########################################################################################

def index_targets(spec, paths):
    """Return the index tables the command line named, in command-line order.

    A directory must be a metadata directory, and expands to the index tables
    directly inside it, or failing that to the index tables one level down. A file
    must be an index table inside a metadata directory.

    Args:
        spec: The tool's ToolSpec.
        paths: The command-line paths.

    Returns:
        list: The PdsFile objects, in command-line order.

    Raises:
        SystemExit: With status 1 for a path that does not exist, is outside
            metadata/, or is not an index table.
    """

    ext = spec.index_ext
    pdsfiles = []
    for path in paths:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = spec.pdsfile_cls.from_abspath(path)

        if pdsf.isdir:
            if '/metadata/' not in path:
                print('Not a metadata directory: ' + path)
                sys.exit(1)

            tables = glob.glob(os.path.join(path, '*' + ext))
            if not tables:
                tables = glob.glob(os.path.join(path, '*/*' + ext))

            if not tables:
                print(f'No {ext} files in directory: ' + path)
                sys.exit(1)

            pdsfiles += spec.pdsfile_cls.pdsfiles_for_abspaths(tables)

        else:
            if '/metadata/' not in path:
                print('Not a metadata file: ' + path)
                sys.exit(1)
            if not path.endswith(ext):
                print('Not a table file: ' + path)
                sys.exit(1)

            pdsfiles.append(pdsf)

    return pdsfiles


def run_index_main(spec, tasks, argv):
    """Run one index shelf tool: parse the command line, set up logging, do the task.

    A third driver, rather than _common.run_main or _shelf_common.
    run_selection_main, for three reasons that are properties of these tools rather
    than options: their target is a table file, so a command-line path expands to
    tables and their log path is built from the table's own logical path with no
    suffix; they skip backup copies of a table one at a time, inside the log
    hierarchy, so that the report of the skip is part of the run and reaches the
    exit status; and their per-target handlers are created in the tool's own log
    directory rather than in the target's.

    Args:
        spec: The tool's ToolSpec.
        tasks: The tool's task functions, keyed by task name, as index_tasks()
            builds them. Each is called with one index table.
        argv: The full command line, sys.argv.

    Raises:
        SystemExit: On a normal return, with status 1 if the run logged a fatal or
            an error and 0 otherwise. A task that raises is logged and re-raised
            instead, so the original exception propagates and sys.exit is not
            reached.
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

    # Generate a list of index tables before logging
    pdsfiles = index_targets(spec, getattr(args, spec.unit))

    # Open logger and loop through tables...
    logger.open(' '.join(argv))
    try:
        for pdsf in pdsfiles:

            if (_common.BACKUP_FILENAME.match(pdsf.abspath)
                    or ' copy' in pdsf.abspath):
                logger.error('Backup file skipped', pdsf.abspath)
                continue

            # Save logs in up to two places. The suffix is passed only when there
            # is one: log_path_for_index has no suffix argument, and an empty
            # log_suffix is how a spec says its log path takes none.
            suffix = (spec.log_suffix,) if spec.log_suffix else ()
            logfiles = _common.log_paths_for(pdsf, spec.log_path_method, *suffix,
                                             task=args.task, dir=spec.progname)

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))

                # The tool's own directory in this log root, not the table's inside
                # it: a table's log path carries its whole logical path, so the
                # per-table directories would each get their own copy otherwise
                subdir = '/' + spec.progname
                logdir = logfile.rpartition(subdir + '/')[0] + subdir

                # These handlers are only used if they don't already exist
                local_handlers += [make_handler(logdir)
                                   for make_handler in spec.handler_factories]

            # Open the next level of the log
            if len(pdsfiles) > 1:
                logger.blankline()

            logger.open('Task "' + args.task + '" for', pdsf.abspath,
                        handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                tasks[args.task](pdsf, logger=logger)

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

