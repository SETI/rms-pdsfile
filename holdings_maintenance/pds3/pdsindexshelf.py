#!/usr/bin/env python3
################################################################################
# pdsindexshelf.py library and main program
#
# Syntax:
#   pdsindexshelf.py --task index_path.tab [index_path.tab ...]
#
# Enter the --help option to see more information.
################################################################################

import argparse
import datetime
import glob
import os
import pickle
import re
import sys

import pdslogger
import pdsfile
import pdstable

LOGNAME = 'pds.validation.indexshelf'
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Default limits
GENERATE_INDEXDICT_LIMITS = {}
WRITE_INDEXDICT_LIMITS = {}
LOAD_INDEXDICT_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################

def generate_indexdict(pdsf, *, logger=None, limits={}):
    """Generate a dictionary keyed by row key for each row in the given table.
    The value returned is a list containing all the associated row indices.
    """

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsf.root_)

    merged_limits = GENERATE_INDEXDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Tabulating index rows for', pdsf.abspath, limits=merged_limits)

    try:
        table = pdstable.PdsTable(pdsf.label_abspath,
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

################################################################################

def write_indexdict(pdsf, index_dict, *, logger=None, limits={}):
    """Write a new shelf file for the rows of this index."""

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsf.root_)

    merged_limits = WRITE_INDEXDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing index shelf file info for', pdsf.abspath,
                limits=merged_limits)

    try:
        pdsfile.Pds3File.close_all_shelves() # prevents using a cached shelf file

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
                    f.write('%d,\n' % rows[0])
                else:
                    f.write('(')
                    for row in rows[:-1]:
                        f.write('%d, ' % row)
                    f.write('%d),\n' % rows[-1])

            f.write('}\n\n')

        logger.info('Two files written')

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def load_indexdict(pdsf, *, logger=None, limits={}):

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
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

################################################################################

def validate_infodict(pdsf, tabdict, shelfdict, *, logger=None):

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsf.root_)
    logger.info('Validating index file for', pdsf.abspath)

    if tabdict == shelfdict:
        logger.info('Validation complete')
    else:
        for key, value in tabdict.items():
            if key not in shelfdict:
                logger.error(f'not in shelf: {key}')
            elif (shelfval := shelfdict[key]) != value:
                logger.error(f'key mismatch: {key}\n'
                             f'    table: {value}\n'
                             f'    shelf: {shelfval}')
        for key in shelfdict:
            if key not in tabdict:
                logger.error(f'not in table: {key}')

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsf, logger=None, limits={}):

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file does not exist
    if os.path.exists(pdsf.indexshelf_abspath):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Index shelf file already exists', shelf_path)
        return

    # Generate info
    (index_dict, _) = generate_indexdict(pdsf, logger=logger, limits=limits)
    if index_dict is None:
        return

    # Save info file
    write_indexdict(pdsf, index_dict, logger=logger, limits=limits)

def reinitialize(pdsf, logger=None, limits={}):

    shelf_path = pdsf.indexshelf_abspath

    # ing if shelf file does not exist
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Index shelf file does not exist; initializing',
                       shelf_path)
        initialize(pdsf, logger=logger)
        return

    # Generate info
    (index_dict, _) = generate_indexdict(pdsf, logger=logger, limits=limits)
    if not index_dict:
        return

    # Save info file
    write_indexdict(pdsf, index_dict, logger=logger, limits=limits)

def validate(pdsf, logger=None, limits={}):

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file exists
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Index shelf file does not exist', shelf_path)
        return

    (table_indexdict, _) = generate_indexdict(pdsf, logger=logger,
                                              limits=limits)
    if table_indexdict is None:
        return

    shelf_indexdict = load_indexdict(pdsf, logger=logger, limits=limits)
    if not shelf_indexdict:
        return

    # Validate
    validate_infodict(pdsf, table_indexdict, shelf_indexdict,
                      logger=logger)

def repair(pdsf, logger=None, op='repair', limits={}):

    shelf_path = pdsf.indexshelf_abspath

    # Make sure file exists
    if not os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Index shelf file does not exist; initializing',
                       shelf_path)
        initialize(pdsf, logger=logger)
        return

    (table_indexdict, latest_mtime) = generate_indexdict(pdsf, logger=logger,
                                                         limits=limits)
    if not table_indexdict:
        return

    shelf_indexdict = load_indexdict(pdsf, logger=logger, limits=limits)
    if not shelf_indexdict:
        return

    # Compare
    canceled = (table_indexdict == shelf_indexdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

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
    write_indexdict(pdsf, table_indexdict, logger=logger, limits=limits)

def update(pdsf, selection=None, logger=None, limits={}):

    shelf_path = pdsf.indexshelf_abspath
    if os.path.exists(shelf_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Index shelf file exists; not updated', pdsf.abspath)

    else:
        initialize(pdsf, logger, limits=limits)

################################################################################
################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdsindexshelf: Create, maintain and validate shelf files ' +
                    'containing row lookup information for index files.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create an indexshelf file for an index or for '  +
                             'an entire metadata directory. Abort if the file '+
                             'already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create an indexshelf file for an index or for '  +
                             'an entire metadata directory. Replace any files '+
                             'that already exists.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate an indexshelf file or metadata '        +
                             'directory.')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate an index shelf file; replace only if '  +
                             'necessary. If the shelf file content is correct '+
                             'but it is older than either the file or the '    +
                             'label, update the shelf file\'s modification '   +
                             'date.')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a metadata directory for any new index '  +
                             'files and add create an index shelf file for '   +
                             'each one. Existing index shelf files are not '   +
                             'checked.')

    parser.add_argument('table', nargs='+', type=str,
                        help='Path to an index file or metadata directory.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the "index" '+
                             'subdirectory of each log root directory.')

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdsindexshelf error: Missing task')
        sys.exit(1)

    status = 0

    # Define the logging directory
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.Pds3File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdsindexshelf')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of Pds3File objects before logging
    pdsfiles = []
    for path in args.table:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.Pds3File.from_abspath(path)

        if pdsf.isdir:
            if not '/metadata/' in path:
                print('Not a metadata directory: ' + path)
                sys.exit(1)

            tables = glob.glob(os.path.join(path, '*.tab'))
            if not tables:
                tables = glob.glob(os.path.join(path, '*/*.tab'))

            if not tables:
                print('No .tab files in directory: ' + path)
                sys.exit(1)

            pdsfiles += pdsfile.Pds3File.pdsfiles_for_abspaths(tables)

        else:
            if not '/metadata/' in path:
                print('Not a metadata file: ' + path)
                sys.exit(1)
            if not path.endswith('.tab'):
                print('Not a table file: ' + path)
                sys.exit(1)

            pdsfiles.append(pdsf)

    # Open logger and loop through tables...
    logger.open(' '.join(sys.argv))
    try:
        for pdsf in pdsfiles:

            if BACKUP_FILENAME.match(pdsf.abspath) or ' copy' in pdsf.abspath:
                logger.error('Backup file skipped', pdsf.abspath)
                continue

            # Save logs in up to two places
            logfiles = [pdsf.log_path_for_index(task=args.task,
                                                dir='pdsindexshelf'),
                        pdsf.log_path_for_index(task=args.task,
                                                dir='pdsindexshelf',
                                                place='parallel')]
            if logfiles[0] == logfiles[1]:
                logfiles = logfiles[:-1]

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = (logfile.rpartition('/pdsindexshelf/')[0] +
                          '/pdsindexshelf')

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            # Open the next level of the log
            logger.open('Task "' + args.task + '" for', pdsf.abspath,
                        handler=local_handlers, blankline=True)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    initialize(pdsf)

                elif args.task == 'reinitialize':
                    reinitialize(pdsf)

                elif args.task == 'validate':
                    validate(pdsf)

                elif args.task == 'repair':
                    repair(pdsf)

                else:   # update
                    update(pdsf)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        print(sys.exc_info()[2])
        status = 1
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors: status = 1

    sys.exit(status)

if __name__ == '__main__':
    main()
