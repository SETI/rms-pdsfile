#!/usr/bin/env python3
################################################################################
# pdschecksums.py library and main program
#
# Syntax:
#   pdschecksums.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import argparse
import datetime
import glob
import hashlib
import os
import re
import shutil
import sys

import pdslogger
import pdsfile

# Holds log file directories temporarily, used by move_old_checksums()
LOGDIRS = []

LOGNAME = 'pds.validation.checksums'
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Default limits
GENERATE_CHECKSUMS_LIMITS = {'info': -1}
READ_CHECKSUMS_LIMITS = {'debug': 0}
WRITE_CHECKSUMS_LIMITS = {'dot_': -1, 'ds_store': -1, 'invisible': 100}
VALIDATE_PAIRS_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################

# From http://stackoverflow.com/questions/3431825/-
#       generating-an-md5-checksum-of-a-file

def hashfile(fname, blocksize=65536):
    f = open(fname, 'rb')
    hasher = hashlib.md5()
    buf = f.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = f.read(blocksize)
    return hasher.hexdigest()

################################################################################

def generate_checksums(pdsdir, selection=None, oldpairs=[], *, regardless=True,
                       logger=None, limits={}):
    """Generate a list of tuples (abspath, checksum) recursively from the given
    directory tree.

    If a selection is specified, it is interpreted as the basename of a file,
    and only that file is processed.

    The optional oldpairs is a list of (abspath, checksum) pairs. For any file
    that already has a checksum in the shortcut list, the checksum is copied
    from this list rather than re-calculated. This list is merged with the
    selection if a selection is identified.

    If regardless is True, then the checksum of a selection is calculated
    regardless of whether it is already in abspairs.

    Also return the latest modification date among all the files checked.
    """

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = GENERATE_CHECKSUMS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Generating MD5 checksums', dirpath, limits=merged_limits)

    latest_mtime = 0.
    try:
        md5_dict = {}
        for (abspath, hex) in oldpairs:
            md5_dict[abspath] = hex

        newtuples = []
        for (path, dirs, files) in os.walk(dirpath):
            for file in files:
                abspath = os.path.join(path, file)
                latest_mtime = max(latest_mtime, os.path.getmtime(abspath))

                if selection and file != selection:
                    continue

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

                if regardless and selection:
                    md5 = hashfile(abspath)
                    newtuples.append((abspath, md5, file))
                    logger.info('Selected MD5=%s' % md5, abspath)

                elif abspath in md5_dict:
                    newtuples.append((abspath, md5_dict[abspath], file))
                    logger.debug('MD5 copied', abspath)

                else:
                    md5 = hashfile(abspath)
                    newtuples.append((abspath, md5, file))
                    logger.info('MD5=%s' % md5, abspath)

        if selection:
            if len(newtuples) == 0:
                logger.error('File selection not found', selection)
                return ({}, latest_mtime)

            if len(newtuples) > 1:
                logger.error('Multiple copies of file selection found',
                             selection)
                return ({}, latest_mtime)

        # Add new values to dictionary
        for (abspath, md5, _) in newtuples:
            md5_dict[abspath] = md5

        # Restore original order, old keys then new
        old_keys = [p[0] for p in oldpairs]

        newpairs = []
        for key in old_keys:
            newpairs.append((key, md5_dict[key]))
            del md5_dict[key]

        for (key, new_md5, new_file) in newtuples:
            if key in md5_dict:     # if not already copied to list of pairs
                newpairs.append((key, md5_dict[key]))

        dt = datetime.datetime.fromtimestamp(latest_mtime)
        logger.info('Lastest holdings file modification date',
                    dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return (newpairs, latest_mtime)

################################################################################

def read_checksums(check_path, selection=None, *, logger=None, limits={}):
    """Return a list of tuples (abspath, checksum) from a checksum file.

    If a selection is specified, then only the checksum with this file name
    is returned."""

    check_path = os.path.abspath(check_path)
    pdscheck = pdsfile.Pds3File.from_abspath(check_path)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdscheck.root_)

    merged_limits = READ_CHECKSUMS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading MD5 checksums', check_path, limits=merged_limits)

    try:
        logger.info('MD5 checksum file', check_path)

        if not os.path.exists(check_path):
            logger.error('MD5 checksum file not found', check_path)
            return []

        prefix_ = pdscheck.dirpath_and_prefix_for_checksum()[1]

        # Read the pairs
        abspairs = []
        with open(check_path, 'r') as f:
            for rec in f:
                hexval = rec[:32]
                filepath = rec[34:].rstrip()

                if selection and os.path.basename(filepath) != selection:
                    continue

                basename = os.path.basename(filepath)
                if basename == '.DS_Store':
                    logger.error('.DS_Store found in checksum file', filepath)
                    continue

                if basename.startswith('._'):
                    logger.error('._* file found in checksum file', filepath)
                    continue

                if basename[0] == '.':
                    logger.invisible('Checksum for invisible file', filepath)

                abspairs.append((prefix_ + filepath, hexval))
                logger.debug('Read', filepath)

        if selection and len(abspairs) == 0:
            logger.error('File selection not found', selection)
            return []

    except Exception as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return abspairs

################################################################################

def checksum_dict(dirpath, *, logger=None, limits={}):

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    logger.info('Loading checksums for', dirpath, force=True)

    check_path = pdsdir.checksum_path_and_lskip()[0]
    abspairs = read_checksums(check_path, logger=logger, limits=limits)

    pair_dict = {}
    for (abspath, checksum) in abspairs:
        pair_dict[abspath] = checksum

    logger.info('Checksum load completed', dirpath, force=True)
    return pair_dict

################################################################################

def write_checksums(check_path, abspairs, *, logger=None, limits={}):
    """Write a checksum table containing the given pairs (abspath, checksum)."""

    check_path = os.path.abspath(check_path)
    pdscheck = pdsfile.Pds3File.from_abspath(check_path)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdscheck.root_)

    merged_limits = WRITE_CHECKSUMS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing MD5 checksums', check_path, limits=merged_limits)

    try:
        # Create parent directory if necessary
        parent = os.path.split(check_path)[0]
        if not os.path.exists(parent):
            logger.info('Creating directory', parent)
            os.makedirs(parent)

        prefix_ = pdscheck.dirpath_and_prefix_for_checksum()[1]
        lskip = len(prefix_)

        # Write file
        f = open(check_path, 'w')
        for pair in abspairs:
            (abspath, hex) = pair

            if abspath.endswith('/.DS_Store'):      # skip .DS_Store files
                logger.ds_store('.DS_Store skipped', abspath)
                continue

            if '/._' in abspath:                    # skip dot-underscore files
                logger.dot_underscore('._* file skipped', abspath)
                continue

            if '/.' in abspath:                     # flag invisible files
                logger.invisible('Invisible file', abspath)

            f.write('%s  %s\n' % (hex, abspath[lskip:]))
            logger.debug('Written', abspath)

        f.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_pairs(pairs1, pairs2, selection=None, *, logger=None,
                   limits={}):
    """Validate the first checksum list against the second.

    If a selection is specified, only a file with that basename is checked."""

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

    merged_limits = VALIDATE_PAIRS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Validating checksums', limits=limits)

    success = True
    try:
        md5_dict = {}
        for (abspath, hex) in pairs2:
            md5_dict[abspath] = hex

        for (abspath, hex) in pairs1:
            if selection and selection != os.path.basename(abspath):
                continue

            if abspath not in md5_dict:
                logger.error('Missing checksum', abspath)
                success = False

            elif hex != md5_dict[abspath]:
                del md5_dict[abspath]
                logger.error('Checksum mismatch', abspath)
                success = False

            else:
                del md5_dict[abspath]
                logger.info('Validated', abspath)

        if not selection:
            abspaths = list(md5_dict.keys())
            abspaths.sort()
            for abspath in abspaths:
                logger.error('Extra file', abspath)
                success = False

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        logger.close()
        return success

################################################################################

def move_old_checksums(check_path, *, logger=None):
    """Appends a version number to an existing checksum file and moves it to
    the associated log directory."""

    if not os.path.exists(check_path):
        return

    check_basename = os.path.basename(check_path)
    (check_prefix, check_ext) = os.path.splitext(check_basename)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

    from_logged = False
    for log_dir in LOGDIRS:
        dest_template = log_dir + '/' + check_prefix + '_v???' + check_ext
        version_paths = glob.glob(dest_template)

        max_version = 0
        lskip = len(check_ext)
        for version_path in version_paths:
            version = int(version_path[-lskip-3:-lskip])
            max_version = max(max_version, version)

        new_version = max_version + 1
        dest = dest_template.replace('???', '%03d' % new_version)
        shutil.copy(check_path, dest)

        if not from_logged:
            logger.info('Checksum file moved from: ' + check_path, force=True)
            from_logged = True

        logger.info('Checksum file moved to', dest, force=True)

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, selection=None, *, logger=None, limits={}):

    check_path = pdsdir.checksum_path_and_lskip()[0]

    # Make sure checksum file does not exist
    if os.path.exists(check_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Checksum file already exists', check_path, force=True)
        return False

    # Check selection
    if selection:
        raise ValueError('File selection is disallowed for task ' +
                         '"initialize": ' + selection)

    # Generate checksums
    (pairs, _) = generate_checksums(pdsdir, logger=logger, limits=limits)
    if not pairs:
        return False

    # Write new checksum file
    write_checksums(check_path, pairs, logger=logger, limits=limits)
    return True

def reinitialize(pdsdir, selection=None, *, logger=None, limits={}):

    check_path = pdsdir.checksum_path_and_lskip()[0]

    # Warn if checksum file does not exist
    if not os.path.exists(check_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Checksum file does not exist', check_path, force=True)
            return False
        else:
            logger.warning('Checksum file does not exist; initializing',
                          check_path)
            return initialize(pdsdir, selection=selection, logger=logger,
                              limits=limits)

    # Re-initialize just the selection; preserve others
    if selection:
        oldpairs = read_checksums(check_path, logger=logger, limits=limits)
        if not oldpairs:
            return False
    else:
        oldpairs = []

    # Generate new checksums
    (pairs, _) = generate_checksums(pdsdir, selection, oldpairs,
                                    regardless=True, logger=logger,
                                    limits=limits)
    if not pairs:
        return False

    # Write new checksum file
    move_old_checksums(check_path, logger=logger)

    new_limits = WRITE_CHECKSUMS_LIMITS.copy()
    new_limits.update(limits)
    write_checksums(check_path, pairs, logger=logger, limits=new_limits)
    return True

def validate(pdsdir, selection=None, *, logger=None, limits={}):

    check_path = pdsdir.checksum_path_and_lskip()[0]

    # Make sure checksum file exists
    if not os.path.exists(check_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Checksum file does not exist', check_path)
        return False

    # Read checksum file
    md5pairs = read_checksums(check_path, selection, logger=logger,
                              limits=limits)
    if not md5pairs:
        return False

    # Generate checksums
    (dirpairs, _) = generate_checksums(pdsdir, selection, logger=logger,
                                       limits=limits)
    if not dirpairs:
        return False

    # Validate
    return validate_pairs(dirpairs, md5pairs, selection, logger=logger,
                          limits=limits)

def repair(pdsdir, selection=None, *, logger=None, limits={}):

    check_path = pdsdir.checksum_path_and_lskip()[0]

    # Make sure checksum file exists
    if not os.path.exists(check_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Checksum file does not exist', check_path, force=True)
            return False
        else:
            logger.warning('Checksum file does not exist; initializing',
                           check_path)
            return initialize(pdsdir, selection=selection, logger=logger,
                              limits=limits)

    # Read checksums file
    md5pairs = read_checksums(check_path, logger=logger, limits=limits)
    if not md5pairs:
        return False

    # Generate new checksums
    if selection:
        (dirpairs,
         latest_mtime) = generate_checksums(pdsdir, selection, md5pairs,
                                            regardless=True, logger=logger,
                                            limits=limits)
    else:
        (dirpairs,
         latest_mtime) = generate_checksums(pdsdir, logger=logger,
                                            limits=limits)

    if not dirpairs:
        return False

    # Compare checksums
    md5pairs.sort()
    dirpairs.sort()
    canceled = (dirpairs == md5pairs)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

        check_mtime = os.path.getmtime(check_path)
        if latest_mtime > check_mtime:
            logger.info('!!! Checksum file content is up to date',
                        check_path, force=True)

            dt = datetime.datetime.fromtimestamp(latest_mtime)
            logger.info('!!! Latest holdings file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            check_mtime = os.path.getmtime(check_path)
            dt = datetime.datetime.fromtimestamp(check_mtime)
            logger.info('!!! Checksum file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            delta = latest_mtime - check_mtime
            if delta >= 86400/10:
                logger.info('!!! Checksum file is out of date %.1f days' %
                            (delta / 86400.), force=True)
            else:
                logger.info('!!! Checksum file is out of date %.1f minutes' %
                            (delta / 60.), force=True)

            dt = datetime.datetime.now()
            os.utime(check_path)
            logger.info('!!! Time tag on checksum file set to',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

        else:
            logger.info('!!! Checksum file is up to date; repair canceled',
                        check_path, force=True)
        return True

    # Write checksum file
    move_old_checksums(check_path, logger=logger)
    write_checksums(check_path, dirpairs, logger=logger)
    return True

def update(pdsdir, selection=None, *, logger=None, limits={}):

    check_path = pdsdir.checksum_path_and_lskip()[0]

    # Make sure file exists
    if not os.path.exists(check_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Checksum file does not exist', check_path)
            return False
        else:
            logger.warning('Checksum file does not exist; initializing',
                           check_path)
            return initialize(pdsdir, selection=selection, logger=logger)

    # Read checksums file
    md5pairs = read_checksums(check_path, logger=logger)
    if not md5pairs:
        return False

    # Generate new checksums if necessary
    (dirpairs,
     latest_mtime) = generate_checksums(pdsdir, selection, md5pairs,
                                        regardless=False, logger=logger)
    if not dirpairs:
        return False

    # Compare checksums
    md5pairs.sort()
    dirpairs.sort()
    canceled = (dirpairs == md5pairs)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Checksum file content is complete; update canceled',
                    check_path)
        return True

    # Write checksum file
    move_old_checksums(check_path, logger=logger)
    write_checksums(check_path, dirpairs, logger=logger)
    return True

################################################################################
# Executable program
################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdschecksums: Create, maintain and validate MD5 '         +
                    'checksum files for PDS volumes and volume sets.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create an MD5 checksum file for a volume or '    +
                             'volume set. Abort if the checksum file '         +
                             'already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create an MD5 checksum file for a volume or '    +
                             'volume set. Replace the checksum file if it '    +
                             'already exists. If a single file is specified, ' +
                             'such as one archive file in a volume set, only ' +
                             'single checksum is re-initialized.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume directory tree ' +
                             'against its MD5 checksum. If a single file '     +
                             'is specified, such as one archive file in a '    +
                             'volume set, only that single checksum is '       +
                             'validated.')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume directory tree ' +
                             'against its MD5 checksum. If any disagreement '  +
                             'is found, the checksum file is replaced; '       +
                             'otherwise it is unchanged. If a single file is ' +
                             'specified, such as one archive file of a '       +
                             'volume set, then only that single checksum is '  +
                             'repaired. If any of the files checked are newer' +
                             'than the checksum file, update shelf file\'s '   +
                             'modification date')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a directory for any new files and add '   +
                             'their MD5 checksums to the checksum file. '      +
                             'Checksums of pre-existing files are not checked.')

    parser.add_argument('volume', nargs='+', type=str,
                        help='The path to the root directory of a volume or '  +
                             'volume set. For a volume set, all the volume '   +
                             'directories inside it are handled in sequence. ' +
                             'Note that, for archive directories, checksums '  +
                             'are grouped into one file for the entire '       +
                             'volume set.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdschecksums" subdirectory of each log root '   +
                             'directory.')

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    parser.add_argument('--archives', '-a', default=False, action='store_true',
                        help='Instead of referring to a volume, refer to the ' +
                             'the archive file for that volume.')

    parser.add_argument('--infoshelf', '-i', dest='infoshelf',
                        default=False, action='store_true',
                        help='After a successful run, also execute the '       +
                             'equivalent pdsinfoshelf command.')


    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdschecksums error: Missing task')
        sys.exit(1)

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
        path = os.path.join(args.log, 'pdschecksums')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Prepare the list of paths
    abspaths = []
    for path in args.volume:

        # Make sure path makes sense
        path = os.path.abspath(path)
        parts = path.partition('/holdings/')
        if not parts[1]:
            print('Not a holdings subdirectory: ' + path)
            sys.exit(1)

        if parts[2].startswith('checksums-'):
            print('No checksums for checksum files: ' + path)
            sys.exit(1)

        # Convert to an archives path if necessary
        if args.archives and not parts[2].startswith('archives-'):
            path = parts[0] + '/holdings/archives-' + parts[2]

        # Convert to a list of absolute paths that exist (volsets or volumes)
        try:
            pdsf = pdsfile.Pds3File.from_abspath(path, must_exist=True)
            abspaths.append(pdsf.abspath)

        except (ValueError, IOError):
            # Allow a volume name to stand in for a .tar.gz archive
            (dir, basename) = os.path.split(path)
            pdsdir = pdsfile.Pds3File.from_abspath(dir)
            if pdsdir.archives_ and '.' not in basename:
                if pdsdir.voltype_ == 'volumes/':
                    basename += '.tar.gz'
                else:
                    basename += '_%s.tar.gz' % pdsdir.voltype_[:-1]

                newpaths = glob.glob(os.path.join(dir, basename))
                if len(newpaths) == 0:
                    raise

                abspaths += newpaths
                continue
            else:
                raise

    # Generate a list of tuples (pdsfile, selection)
    info = []
    for path in abspaths:
        pdsf = pdsfile.Pds3File.from_abspath(path)

        if pdsf.is_volset_dir:
            # Archive directories are checksumed by volset
            if pdsf.archives_:
                info.append((pdsf, None))

            # Others are checksumed by volume
            else:
                children = [pdsf.child(c) for c in pdsf.childnames]
                info += [(c, None) for c in children if c.isdir]
                        # "if c.isdir" is False for volset level readme files

        elif pdsf.is_volume_dir:
            # Checksum one volume
            info.append((pdsf, None))

        elif pdsf.isdir:
            print('Invalid directory for checksumming: ' + pdsf.logical_path)
            sys.exit(1)

        else:
            pdsdir = pdsf.parent()
            if pdsf.is_volume_file:
                # Checksum one archive file
                info.append((pdsdir, pdsf.basename))
            elif pdsdir.is_volume_dir:
                # Checksum one top-level file in volume
                info.append((pdsdir, pdsf.basename))
            else:
                print('Invalid file for checksumming: ' + pdsf.logical_path)
                sys.exit(1)

    # Begin logging and loop through tuples...
    logger.open(' '.join(sys.argv))
    try:
        for (pdsdir, selection) in info:
            path = pdsdir.abspath

            if selection:
                pdsf = pdsdir.child(os.path.basename(selection))
            else:
                pdsf = pdsdir

            # Save logs in up to two places
            if pdsf.volname:
                logfiles = set([pdsf.log_path_for_volume('_md5',
                                                         task=args.task,
                                                         dir='pdschecksums'),
                                pdsf.log_path_for_volume('_md5',
                                                         task=args.task,
                                                         dir='pdschecksums',
                                                         place='parallel')])
            else:
                logfiles = set([pdsf.log_path_for_volset('_md5',
                                                         task=args.task,
                                                         dir='pdschecksums'),
                                pdsf.log_path_for_volset('_md5',
                                                         task=args.task,
                                                         dir='pdschecksums',
                                                         place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            LOGDIRS = []            # used by move_old_checksums()
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]
                LOGDIRS.append(os.path.split(logfile)[0])

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            # Open the next level of the log
            if len(info) > 1:
                logger.blankline()

            if selection:
                logger.open('Task "' + args.task + '" for selection ' +
                            selection, path, handler=local_handlers)
            else:
                logger.open('Task "' + args.task + '" for', path,
                            handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    proceed = initialize(pdsdir, selection)

                elif args.task == 'reinitialize':
                    if selection:           # don't erase everything else!
                        proceed = update(pdsdir, selection)
                    else:
                        proceed = reinitialize(pdsdir, selection)

                elif args.task == 'validate':
                    proceed = validate(pdsdir, selection)

                elif args.task == 'repair':
                    proceed = repair(pdsdir, selection)

                else:   # update
                   proceed = update(pdsdir, selection)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                proceed = False
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        proceed = False
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors:
            proceed = False

    # If everything went well, execute pdsinfoshelf too
    if proceed and args.infoshelf:
        new_list = [a.replace('pdschecksums', 'pdsinfoshelf') for a in sys.argv]
        new_list = [a for a in new_list if a not in ('--infoshelf', '-i')]
        status = os.system(' '.join(new_list))
        sys.exit(status)

if __name__ == '__main__':
    main()
