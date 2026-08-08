##########################################################################################
# pdsfile/holdings_maintenance/_indexshelf_common.py
##########################################################################################

"""What the two index shelf tools share.

These shelve the row numbers of each product in a metadata index table. Their target is
a table file or a metadata directory rather than a unit, and their log path is built
from the table's own logical path, so they run on ``run_index_main()`` at the end of
this module rather than on either of the two drivers in ``_common.py`` and
``_shelf_common.py``. They import nothing from ``_shelf_common.py``.

An index shelf is a pickled ``{filename key: list of row numbers}`` dictionary written
beside a readable ``.py`` file holding the same mapping as Python source. Both are
written together and both are re-dated together, so a caller reading either gets the
same answer, and the repair task takes the older of the two as the pair's age.

The five tasks are here rather than in the two tool modules, because nothing in them
differs between PDS3 and PDS4: what a row is, how a key is formed and how a shelf is
compared to its table are properties of ``pdstable``. ``index_tasks()`` binds a spec
into each of the five and returns the table a driver takes. The two tools differ only in
their spec, and among the fields that reach this module only ``index_ext`` differs in
value, '.tab' against '.csv'.

The tools do not all agree about an empty result. ``index_initialize()`` and
``index_validate()`` test the fresh table dictionary against None, which
``generate_indexdict()`` never returns, while ``index_reinitialize()`` and
``index_repair()`` test it for emptiness; a table with no rows therefore stops the
latter two and is written by the former two.
"""

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

    The table is read through its label rather than directly, and the keys are the
    filename keys ``pdstable`` builds, truncated to the PdsFile's own
    ``filename_keylen``. A key covering more than one row maps to all of them, which is
    what makes the value a list rather than a number.

    The date returned is the later of the table's and the label's modification times, so
    editing either one dates the pair. It is a POSIX timestamp; the same value is also
    logged, formatted.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its logname is read here, as
            the fallback logger's name.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Returns:
        tuple: The {filename key: list of row numbers} dictionary, and the later of
        the table's and its label's modification times. The dictionary is empty for a
        table with no rows and is never None.

    Raises:
        OSError: from ``PdsTable()`` if the table or its label cannot be read, and from
            ``getmtime()`` on either of them. It is logged as an error and re-raised.
        ValueError: from ``PdsTable()`` if the table disagrees with its label. It is
            logged and re-raised the same way.
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

    Two files are written for one call: the pickled dictionary at the PdsFile's
    ``indexshelf_abspath``, and a readable ``.py`` beside it under the same basename,
    holding the same mapping as a Python dictionary literal named after the file. Keys
    in the sidecar are padded to a common width so the values line up, a key covering
    one row is written as a bare number and one covering several as a tuple, and the
    sidecar is encoded latin-1. The parent directory is created if it is not there.

    **An existing shelf is overwritten, not versioned.** Unlike the checksum, info shelf
    and link shelf tools, nothing here copies the old file into the log directories
    first, and ``run_index_main()`` records no log directories for it to copy into.

    Every open shelf of the spec's class is closed before anything is written, so a
    shelf already in the class's cache cannot be handed back in place of the file this
    call replaces.

    Parameters:
        spec (ToolSpec): The tool's specification. Its pdsfile_cls is what the shelf
            cache is cleared on, and its logname is the fallback logger's name.
        pdsf: The index table.
        index_dict (dict): The row numbers, as generate_indexdict() returned them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Raises:
        OSError: raised by ``open()`` or ``makedirs()`` if either file cannot be
            written. It is logged through ``exception()`` and re-raised, as is anything
            else the write raises.
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

    The pickle is read straight from disk rather than through the PdsFile shelf cache,
    so what comes back is what the file holds now.

    A missing shelf file is logged as an **error**, which gives the run a nonzero exit
    status, and reported as an empty dictionary. An empty dictionary is therefore two
    situations at once here, a shelf that is absent and a shelf that covers nothing, and
    the callers in this module treat both as a reason to stop.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its logname is read here, as
            the fallback logger's name.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Returns:
        dict: The shelved row numbers, empty if there is no shelf file.

    Raises:
        pickle.PickleError: from ``load()`` on a shelf file that is not readable as a
            pickle. It is logged through ``exception()`` and re-raised.
        OSError: raised by ``open()`` if the file goes away between the existence test
            and the read. This one is not caught, so it is not logged.
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

    Equal dictionaries are reported as a success and nothing further is examined.
    Otherwise each difference is its own error line: a key the shelf lacks, a key whose
    row numbers differ, and a key the table lacks. A row list that differs only in order
    counts as a difference, because the comparison is between lists.

    Neither dictionary is modified, unlike ``_linkshelf_common.validate_links()``, which
    empties both as it goes.

    This takes no limits argument and opens no log level of its own, so its lines land
    in whatever level the caller has open and are capped by that level's limits.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its logname is read here, as
            the fallback logger's name.
        pdsf: The index table.
        tabdict (dict): The row numbers read from the table.
        shelfdict (dict): The row numbers read from the shelf.
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
    """Shelve one index table, refusing to replace a shelf that is already there.

    A shelf file already in place is logged as an error and nothing is read or written,
    so this is the one task that never overwrites. A table with no rows is shelved as an
    empty dictionary rather than skipped, which is where this differs from
    index_reinitialize().

    Parameters:
        spec (ToolSpec): The tool's specification.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the two functions that open a log
            level.
    """

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
    """Shelve one index table, replacing whatever shelf is there.

    A table with no shelf is a warning rather than an error, and is handed to
    index_initialize() instead. A table whose rows come back empty stops here without
    writing, so a shelf that is already in place is left as it was.

    Parameters:
        spec (ToolSpec): The tool's specification.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the functions that open a log
            level.
    """

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
    """Report every way one index table and its shelf disagree.

    A missing shelf file is an error and stops the task; so does a shelf that reads back
    empty, which is what a shelf covering nothing and a shelf that has just gone missing
    both look like. Only when both dictionaries are in hand is the comparison made.

    Nothing is written whatever the answer; the disagreements are reported and that is
    all.

    Parameters:
        spec (ToolSpec): The tool's specification.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the two functions that open a log
            level. The comparison itself takes none.
    """

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
    """Rewrite one index shelf if it disagrees with its table, or re-date it if not.

    Where the two dictionaries differ, the shelf and its sidecar are rewritten and the
    repair is done. Where they agree, the content is right and only the dates can be
    wrong, so the pair is compared against the table's:

      * The pair's age is the **older** of the pickle's and the sidecar's modification
        times, so a pair with one stale half is treated as stale.
      * If the table is newer, both files are touched to now and the run reports how far
        behind they were. The report is in days at or above a tenth of a day, which is
        8,640 seconds, and in minutes below that.
      * If the table is not newer, the repair is canceled and nothing is touched. Equal
        times take this branch, since the test is strict.

    A missing shelf file is a warning and is handed to index_initialize(). A table whose
    rows come back empty, or a shelf that reads back empty, stops the task before the
    comparison.

    Parameters:
        spec (ToolSpec): The tool's specification.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the functions that open a log
            level.
    """

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
    """Shelve one index table if it has no shelf, and leave any existing shelf alone.

    An existing shelf is reported and nothing else happens: its contents are not read,
    not compared and not re-dated, which is what the task's help text means by "existing
    index shelf files are not checked". A table with no shelf is handed to
    index_initialize().

    This is the one task of the five that reports an existing shelf at info level rather
    than as a warning or an error, so a run over a directory of already-shelved tables
    finishes with a zero exit status.

    Parameters:
        spec (ToolSpec): The tool's specification.
        pdsf: The index table.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to index_initialize().
    """

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

    Each entry is a partial over the shared task with the spec already supplied, so what
    a driver calls takes the index table and the keyword arguments and nothing more.
    That is what lets both tools share one set of five task functions.

    A fresh dictionary is built on every call, so a tool that alters its own table
    afterwards does not alter the other's.

    Parameters:
        spec (ToolSpec): The tool's specification, bound into each task.

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

    The directory search is two globs and stops at the first that matches: the tables
    directly inside the directory, and failing that the tables one level below it, which
    is how a metadata bundle-set directory expands to the tables of every bundle in it.
    A directory holding tables at both depths contributes only the shallower ones.

    Everything is decided on the text of the path and its extension. The metadata test
    looks for "/metadata/" anywhere in the absolute path, and the extension is the
    spec's index_ext, which is the one place that field is read.

    Parameters:
        spec (ToolSpec): The tool's specification. Its index_ext is the extension a
            table must carry, and its pdsfile_cls builds the objects.
        paths (list): The command-line paths.

    Returns:
        list: The PdsFile objects, in command-line order. A directory contributes its
        tables in glob order.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 for a path that does not exist,
            is outside metadata/, is a directory holding no tables, or is a file whose
            extension is not the spec's.
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

    Two consequences of the third reason are worth naming. This driver records no log
    directories, so a superseded index shelf is not versioned anywhere; and each task is
    called with the logger as a keyword, which the other two drivers do not do, so the
    task's lines land inside the level this opens for the target.

    Every command-line path is resolved and expanded before the run's first log level is
    opened, so a path this rejects exits before any per-target log file is created.

    This function does not return. Every path out of it is an exception or an exit.

    Parameters:
        spec (ToolSpec): The tool's specification.
        tasks (dict): The tool's task functions, keyed by task name, as index_tasks()
            builds them. Each is called with one index table.
        argv (list): The full command line, sys.argv.

    Raises:
        SystemExit: from ``sys.exit()``, on a normal return with status 1 if the run
            logged a fatal or an error and 0 otherwise, and earlier with status 1 from
            index_targets() on a path it rejects. A task that raises is logged and
            re-raised instead, so the original exception propagates and the closing
            ``sys.exit()`` is not reached.
    """

    (args, logger) = _common.setup_run(spec, argv)

    status = 0

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

