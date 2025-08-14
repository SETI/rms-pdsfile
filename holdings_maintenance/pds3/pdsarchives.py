#!/usr/bin/env python3
################################################################################
# pdsarchives.py library and main program
#
# Syntax:
#   pdsarchives.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import sys
import os
import re
import tarfile
import zlib
import argparse

import pdslogger
import pdsfile

LOGNAME = 'pds.validation.archives'
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Default limits
LOAD_DIRECTORY_INFO_LIMITS = {'info': 100}
READ_ARCHIVE_INFO_LIMITS = {'info': 100}
WRITE_ARCHIVE_LIMITS = {'info': -1, 'dot_': 100}
VALIDATE_TUPLES_LIMITS = {'info': 100}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################
# General tarfile functions
################################################################################

def load_directory_info(pdsdir, *, logger=None, limits={}):
    """Generate a list of tuples (abspath, dirpath, nbytes, mod time)
    recursively for the given directory tree.
    """

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = LOAD_DIRECTORY_INFO_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Generating file info', dirpath, limits=merged_limits)

    try:
        (tarpath, lskip) = pdsdir.archive_path_and_lskip()

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
                logger.info('File info generated', abspath)

                tuples.append((abspath, abspath[lskip:], nbytes, modtime))

            # Load directories
            for dir in dirs:
                abspath = os.path.join(path, dir)

                if dir.startswith('._'):       # skip dot-underscore files
                    logger.dot_underscore('._* directory skipped', abspath)
                    continue

                if '/.' in abspath:             # flag invisible files
                    logger.invisible('Invisible directory', abspath)

                logger.info('Directory info generated', abspath)

                tuples.append((abspath, abspath[lskip:], 0, 0))

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return tuples

################################################################################

def read_archive_info(tarpath, *, logger=None, limits={}):
    """Return a list of tuples (abspath, dirpath, nbytes, modtime) from a
    .tar.gz file.
    """

    tarpath = os.path.abspath(tarpath)
    pdstar = pdsfile.Pds3File.from_abspath(tarpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdstar.root_)

    if not os.path.exists(tarpath):
        logger.critical('File does not exist', tarpath)
        return []

    merged_limits = READ_ARCHIVE_INFO_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading archive file', tarpath, limits=merged_limits)

    try:
        (dirpath, prefix) = pdstar.dirpath_and_prefix_for_archive()

        tuples = []
        with tarfile.open(tarpath, 'r:gz') as f:

            members = f.getmembers()
            for member in members:
                abspath = os.path.join(prefix, member.name)

                if abspath.endswith('/.DS_Store'):  # skip .DS_Store files
                    logger.error('.DS_Store in tarfile', abspath)

                if '/._' in abspath:                # skip dot-underscore files
                    logger.error('._* file in tarfile', abspath)

                if '/.' in abspath:                 # flag invisible files
                    logger.invisible('Invisible file found', abspath)

                if member.isdir():
                    tuples.append((abspath, member.name, 0, 0))
                else:
                    tuples.append((abspath, member.name, member.size,
                                            member.mtime))

                logger.info('Info read', abspath)

    except (zlib.error, Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return tuples

################################################################################

def write_archive(pdsdir, *, clobber=True, archive_invisibles=True,
                  logger=None, limits={}):
    """Write an archive file containing all the files in the directory."""

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

        logger.info('File archived', member.name)
        return member

    #### Begin active code

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = WRITE_ARCHIVE_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing .tar.gz file for', dirpath, limits=merged_limits)

    try:
        (tarpath, lskip) = pdsdir.archive_path_and_lskip()

        # Create parent directory if necessary
        parent = os.path.split(tarpath)[0]
        if not os.path.exists(parent):
            logger.info('Creating directory', parent)
            os.makedirs(parent)

        if not clobber and os.path.exists(tarpath):
            logger.error('Archive file already exists', tarpath)
            return

        f = tarfile.open(tarpath, mode='w:gz')
        f.add(dirpath, arcname=dirpath[lskip:], recursive=True,
                      filter=archive_filter)
        logger.info('Written', tarpath)
        f.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_tuples(dir_tuples, tar_tuples, *, logger=None,
                    limits={}):
    """Validate the directory list of tuples against the list from the tarfile.
    """

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

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
                                 '%d (filesystem) vs. %d (tarfile)' %
                                 (nbytes, tardict[abspath][1]), abspath)
                    valid = False

                if abs(modtime - tardict[abspath][2]) > 1:
                    logger.error('Modification time mismatch: ' +
                                 '%s (filesystem) vs. %s (tarfile)' %
                                 (modtime, tardict[abspath][2]), abspath)
                    valid = False

                del tardict[abspath]

            else:
                logger.info('Validated', dirpath)
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

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, *, logger=None, limits={}):
    write_archive(pdsdir, clobber=False, logger=logger, limits=limits)
    return True

def reinitialize(pdsdir, *, logger=None, limits={}):
    write_archive(pdsdir, clobber=True, logger=logger, limits=limits)
    return True

def validate(pdsdir, *, logger=None, limits={}):
    dir_tuples = load_directory_info(pdsdir, logger=logger, limits=limits)

    tarpath = pdsdir.archive_path_and_lskip()[0]
    tar_tuples = read_archive_info(tarpath, logger=logger, limits=limits)

    return validate_tuples(dir_tuples, tar_tuples, logger=logger,
                           limits=limits)

def repair(pdsdir, *, logger=None, limits={}):

    tarpath = pdsdir.archive_path_and_lskip()[0]
    if not os.path.exists(tarpath):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Archive file does not exist; initializing', tarpath)
        initialize(pdsdir, logger=logger, limits=limits)
        return True

    tar_tuples = read_archive_info(tarpath, logger=logger, limits=limits)
    dir_tuples = load_directory_info(pdsdir, logger=logger, limits=limits)

    # Compare
    dir_tuples.sort()
    tar_tuples.sort()
    canceled = (dir_tuples == tar_tuples)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Files match; repair canceled', tarpath, force=True)
        return False

    # Overwrite tar file if necessary
    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.info('Discrepancies found; writing new file', tarpath, force=True)

    write_archive(pdsdir, clobber=True, logger=logger, limits=limits)
    return True

def update(pdsdir, *, logger=None, limits={}):

    tarpath = pdsdir.archive_path_and_lskip()[0]
    if os.path.exists(tarpath):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('Archive file exists; skipping', tarpath, force=True)
        return False

    # Write tar file if necessary
    write_archive(pdsdir, clobber=True, logger=logger, limits=limits)
    return True

################################################################################
# Executable program
################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdsarchives: Create, maintain and validate .tar.gz '      +
                    'archives of PDS volume directory trees.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create a .tar.gz archive for a volume. Abort '   +
                             'if the archive already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create a .tar.gz archive for a volume. Replace ' +
                             'the archive if it already exists.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume against the '    +
                             'contents of its .tar.gz archive. Files match '   +
                             'if they have identical byte counts and '         +
                             'modification dates; file contents are not '      +
                             'compared.')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume against the '    +
                             'contents of its .tar.gz archive. If any file '   +
                             'has changed, write a new archive.')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a volume set directory for any new '      +
                             'volumes and create a new archive file for each ' +
                             'of them; do not update any pre-existing archive '+
                             'files.')

    parser.add_argument('volume', nargs='+', type=str,
                        help='The path to the root of the volume or volume '   +
                             'set. For a volume set, all the volume '          +
                             'directories inside it are handled in sequence.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdsarchives" subdirectory of each log root '    +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdsarchives error: Missing task')
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
        path = os.path.join(args.log, 'pdsarchives')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of pdsfiles for volume directories
    pdsdirs = []
    for path in args.volume:

        path = os.path.abspath(path)
        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        pdsf = pdsfile.Pds3File.from_abspath(path)
        if pdsf.checksums_:
            print('No archives for checksum files: ' + path)
            sys.exit(1)

        if pdsf.archives_:
            print('No archives for archive files: ' + path)
            sys.exit(1)

        pdsdir = pdsf.volume_pdsfile()
        if pdsdir and pdsdir.isdir:
            pdsdirs.append(pdsdir)
        else:
            pdsdir = pdsf.volset_pdsfile()
            children = [pdsdir.child(c) for c in pdsdir.childnames]
            pdsdirs += [c for c in children if c.isdir]
                    # "if c.isdir" is False for volset level readme files

    # Begin logging and loop through pdsdirs...
    logger.open(' '.join(sys.argv))
    try:
        for pdsdir in pdsdirs:

            # Save logs in up to two places
            logfiles = set([pdsdir.log_path_for_volume('_links',
                                                       task=args.task,
                                                       dir='pdsarchives'),
                            pdsdir.log_path_for_volume('_links',
                                                       task=args.task,
                                                       dir='pdsarchives',
                                                       place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            # Open the next level of the log
            if len(pdsdirs) > 1:
                logger.blankline()

            logger.open('Task %s for' % args.task, pdsdir.abspath,
                                                   handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    proceed = initialize(pdsdir)

                elif args.task == 'reinitialize':
                    proceed = reinitialize(pdsdir)

                elif args.task == 'validate':
                    proceed = validate(pdsdir)

                elif args.task == 'repair':
                    proceed = repair(pdsdir)

                else:       # update
                    proceed = update(pdsdir)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        proceed = False
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors:
            status = 1

    sys.exit(status)

if __name__ == '__main__':
    main()
