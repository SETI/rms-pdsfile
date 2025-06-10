#!/usr/bin/env python3
################################################################################
# pdsinfoshelf.py library and main program
#
# Syntax:
#   pdsinfoshelf.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import argparse
import datetime
import glob
import os
from pathlib import Path
import pickle
import re
import shutil
import sys
from PIL import Image

import pdslogger
import pdsfile

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from holdings_maintenance.pds3 import pdschecksums

# Holds log file directories temporarily, used by move_old_info()
LOGDIRS = []

LOGNAME = 'pds.validation.fileinfo'
LOGROOT_ENV = 'PDS_LOG_ROOT'

PREVIEW_EXTS = set(['.jpg', '.png', '.gif', '.tif', '.tiff',
                    '.jpeg', '.jpeg_small'])

# Default limits
GENERATE_INFODICT_LIMITS = {}
LOAD_INFODICT_LIMITS = {}
WRITE_INFODICT_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################

def generate_infodict(pdsdir, selection, old_infodict={}, *, logger=None,
                     limits={}):
    """Generate a dictionary keyed by absolute file path for each file in the
    directory tree. Value returned is a tuple (nbytes, child_count, modtime,
    checksum, preview size).

    If a selection is specified, it is interpreted as the basename of a file,
    and only that file is processed.

    The optional old_infodict overrides information found in the directory.
    This dictionary is merged with the new information assembled. However, if
    a selection is specified, information about the selection is always updated.

    Also return the latest modification date among all the files checked.
    """

    ### Internal function

    def get_info_for_file(abspath):

        nbytes = os.path.getsize(abspath)
        children = 0
        mtime = os.path.getmtime(abspath)
        dt = datetime.datetime.fromtimestamp(mtime)
        modtime = dt.strftime('%Y-%m-%d %H:%M:%S.%f')
        try:
            checksum = checkdict[abspath]
        except KeyError:
            logger.error('Missing entry in checksum file', abspath)
            checksum = ''

        size = (0,0)
        ext = os.path.splitext(abspath)[1]
        if ext.lower() in PREVIEW_EXTS:
            try:
                im = Image.open(abspath)
                size = im.size
                im.close()
            except Exception:
                logger.error('Preview size not found', abspath)

        return (nbytes, children, modtime, checksum, size)

    def get_info(abspath, infodict, old_infodict, checkdict):
        """Info about the given abspath."""

        if os.path.isdir(abspath):
            nbytes = 0
            children = 0
            modtime = ''

            files = os.listdir(abspath)
            for file in files:
                absfile = os.path.join(abspath, file)

                if file == '.DS_Store':         # skip .DS_Store files
                    logger.ds_store('.DS_Store skipped', absfile)
                    continue

                if file.startswith('._'):       # skip dot-underscore files
                    logger.dot_underscore('._* file skipped', absfile)
                    continue

                if BACKUP_FILENAME.match(file) or ' copy' in file:
                    logger.error('Backup file skipped', absfile)
                    continue

                if '/.' in abspath:             # flag invisible files
                    logger.invisible('Invisible file', absfile)

                info = get_info(absfile, infodict, old_infodict, checkdict)
                nbytes += info[0]
                children += 1
                modtime = max(modtime, info[2])

            info = (nbytes, children, modtime, '', (0,0))

        elif abspath in old_infodict:
            info = old_infodict[abspath]

        else:
            info = get_info_for_file(abspath)
            logger.info('File info generated', abspath)

        infodict[abspath] = info
        return info

    ################################
    # Begin executable code
    ################################

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = GENERATE_INFODICT_LIMITS.copy()
    merged_limits.update(limits)
    if selection:
        logger.open('Generating file info for selection "%s"' % selection,
                    dirpath, limits=merged_limits)
    else:
        logger.open('Generating file info', dirpath, limits=merged_limits)

    try:
        # Load checksum dictionary
        checkdict = pdschecksums.checksum_dict(dirpath, logger=logger)
#         Removed... because we can't ignore empty directories
#         if not checkdict:
#             return ({}, 0.)

        # Generate info recursively
        infodict = {}
        if selection:
            root = os.path.join(dirpath, selection)
        else:
            root = pdsdir.abspath

        info = get_info(root, infodict, old_infodict, checkdict)
        latest_modtime = info[2]

        # Merge dictionaries
        merged = old_infodict.copy()

        if selection:
            merged[root] = infodict[root]

        else:
            for (key, value) in infodict.items():
                if key not in merged:
                    info = infodict[key]
                    merged[key] = info
                    latest_modtime = max(latest_modtime, info[2])

        if not merged:
            logger.info('No files found')
            latest_modtime = ''
        else:
            logger.info('Latest holdings file modification date = '
                        + latest_modtime[:19], force=True)

        # We also have to check the modtime of the checksum file!
        check_path = pdsdir.checksum_path_and_lskip()[0]
        timestamp = os.path.getmtime(check_path)
        check_datetime = datetime.datetime.fromtimestamp(timestamp)
        check_modtime = check_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')
        logger.info('Checksum file modification date = ' + check_modtime[:19],
                    check_path, force=True)
        if check_modtime > latest_modtime:
            latest_modtime = check_modtime

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    return (merged, latest_modtime)

################################################################################

def load_infodict(pdsdir, *, logger=None, limits={}):

    dirpath = pdsdir.abspath
    dirpath_ = dirpath.rstrip('/') + '/'

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = LOAD_INFODICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading info shelf file for', dirpath_[:-1],
                limits=merged_limits)

    try:
        (info_path, lskip) = pdsdir.shelf_path_and_lskip('info')
        logger.info('Info shelf file', info_path)

        if not os.path.exists(info_path):
            logger.error('Info shelf file not found', info_path)
            return {}

        # Read the shelf file and convert to a dictionary
        with open(info_path, 'rb') as f:
            shelf = pickle.load(f)

        infodict = {}
        for (key,info) in shelf.items():
            # Remove a 'null' checksum indicated by a string of dashes
            # (Directories do not have checksums.)
            if info[3] and info[3][0] == '-':
                info = info[:3] + ('',) + info[4:]

            if key == '':
                infodict[dirpath_[:-1]] = info
            else:
                infodict[dirpath_[:lskip] + key] = info

        return infodict

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def write_infodict(pdsdir, infodict, *, logger=None, limits={}):
    """Write a new info shelf file for a directory tree."""

    # Initialize
    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = WRITE_INFODICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing info file info for', dirpath, limits=merged_limits)

    try:
        (info_path, lskip) = pdsdir.shelf_path_and_lskip('info')
        logger.info('Info shelf file', info_path)

        # Create parent directory if necessary
        parent = os.path.split(info_path)[0]
        if not os.path.exists(parent):
            logger.info('Creating parent directory', parent)
            os.makedirs(parent)

        # Write the pickle file
        pickle_dict = {}
        for (key, values) in infodict.items():
            short_key = key[lskip:]
            pickle_dict[short_key] = values

        with open(info_path, 'wb') as f:
            pickle.dump(pickle_dict, f)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    logger.open('Writing Python dictionary', dirpath, limits=limits)
    try:
        # Determine the maximum length of the file path
        len_path = 0
        for (abspath, values) in infodict.items():
            len_path = max(len_path, len(abspath))

        len_path -= lskip

        # Write the python dictionary version
        python_path = info_path.rpartition('.')[0] + '.py'
        name = os.path.basename(python_path)
        parts = name.split('_')
        name = '_'.join(parts[:2]) + '_info'
        abspaths = list(infodict.keys())
        abspaths.sort()

        with open(python_path, 'w', encoding='latin-1') as f:
            f.write(name + ' = {\n')
            for abspath in abspaths:
                path = abspath[lskip:]
                (nbytes, children, modtime, checksum, size) = infodict[abspath]
                f.write('    "%s: ' % (path + '"' + (len_path-len(path)) * ' '))
                f.write('(%11d, %3d, ' % (nbytes, children))
                f.write('"%s", ' % modtime)
                f.write('"%-33s, ' % (checksum + '"'))
                f.write('(%4d,%4d)),\n' % size)

            f.write('}\n\n')

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_infodict(pdsdir, dirdict, shelfdict, selection, *, logger=None,
                      limits={}):

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    if selection:
        logger.open('Validating file info for selection %s' % selection,
                    pdsdir.abspath, limits=limits)
    else:
        logger.open('Validating file info for', pdsdir.abspath, limits=limits)

    # Prune the shelf dictionary if necessary
    if selection:
        keys = list(shelfdict.keys())
        full_path = os.path.join(pdsdir.abspath, selection)
        for key in keys:
            if key != full_path:
                del shelfdict[key]

    try:
        keys = list(dirdict.keys())
        for key in keys:
            if key in shelfdict:
                dirinfo = dirdict[key]
                shelfinfo = shelfdict[key]

                (bytes1, count1, modtime1, checksum1, size1) = dirinfo
                (bytes2, count2, modtime2, checksum2, size2) = shelfinfo

                # Truncate modtimes to seconds
                modtime1 = modtime1.rpartition('.')[0]
                modtime2 = modtime2.rpartition('.')[0]

                agreement = True
                if bytes1 != bytes2:
                    logger.error('File size mismatch %d %d' %
                                    (bytes1, bytes2), key)
                    agreement = False

                if count1 != count2:
                    logger.error('Child count mismatch %d %d' %
                                    (count1, count1), key)
                    agreement = False

                if abs(modtime1 != modtime2) > 1:
                    logger.error('Modification time mismatch "%s" "%s"' %
                        (modtime1, modtime2), key)
                    agreement = False

                if checksum1 != checksum1:
                    logger.error('Checksum mismatch', key)
                    agreement = False

                if size1 != size2:
                    logger.error('Display size mismatch', key)
                    agreement = False

                if agreement:
                    logger.info('File info matches', key)

                del shelfdict[key]
                del dirdict[key]

        keys = list(dirdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Missing shelf info for', key)

        keys = list(shelfdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Shelf info for missing file', key)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        return logger.close()

################################################################################

def move_old_info(shelf_file, logger=None):
    """Move a file to the /logs/ directory tree and append a time tag."""

    if not os.path.exists(shelf_file): return

    shelf_basename = os.path.basename(shelf_file)
    (shelf_prefix, shelf_ext) = os.path.splitext(shelf_basename)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

    from_logged = False
    for log_dir in LOGDIRS:
        dest_template = log_dir + '/' + shelf_prefix + '_v???' + shelf_ext
        version_paths = glob.glob(dest_template)

        max_version = 0
        lskip = len(shelf_ext)
        for version_path in version_paths:
            version = int(version_path[-lskip-3:-lskip])
            max_version = max(max_version, version)

        new_version = max_version + 1
        dest = dest_template.replace('???', '%03d' % new_version)
        shutil.copy(shelf_file, dest)

        if not from_logged:
            logger.info('Info shelf file moved from: ' + shelf_file)
            from_logged = True

        logger.info('Info shelf file moved to', dest)

        python_file = shelf_file.rpartition('.')[0] + '.py'
        dest = dest.rpartition('.')[0] + '.py'
        shutil.copy(python_file, dest)

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, selection=None, logger=None, limits={}):

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Make sure file does not exist
    if os.path.exists(info_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Info shelf file already exists', info_path)
        return

    # Check selection
    if selection:
        logger.error('File selection is disallowed for task "initialize"',
                     selection)
        return

    # Generate info
    (infodict, _) = generate_infodict(pdsdir, selection, logger=logger,
                                      limits=limits)

    # Save info file
    write_infodict(pdsdir, infodict, logger=logger, limits=limits)

def reinitialize(pdsdir, selection=None, logger=None, limits={}):

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Warn if shelf file does not exist
    if not os.path.exists(info_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Info shelf file does not exist', info_path)
        else:
            logger.warning('Info shelf file does not exist; initializing',
                           info_path)
            initialize(pdsdir, selection=selection, logger=logger,
                       limits=limits)
        return

    # Generate info
    (infodict, _) = generate_infodict(pdsdir, selection, logger=logger,
                                      limits=limits)
    if not infodict:
        return

    # Move old file if necessary
    if os.path.exists(info_path):
        move_old_info(info_path, logger=logger)

    # Save info file
    write_infodict(pdsdir, infodict, logger=logger, limits=limits)

def validate(pdsdir, selection=None, logger=None, limits={}):

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Make sure file exists
    if not os.path.exists(info_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Info shelf file does not exist', info_path)
        return

    # Read info shelf file
    shelf_infodict = load_infodict(pdsdir, logger=logger, limits=limits)

    # Generate info
    (dir_infodict, _) = generate_infodict(pdsdir, selection, logger=logger,
                                          limits=limits)

    # Validate
    validate_infodict(pdsdir, dir_infodict, shelf_infodict, selection=selection,
                      logger=logger, limits=limits)

def repair(pdsdir, selection=None, logger=None, limits={}):

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Make sure file exists
    if not os.path.exists(info_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Info shelf file does not exist', info_path)
        else:
            logger.warning('Info shelf file does not exist; initializing',
                           info_path)
            initialize(pdsdir, selection=selection, logger=logger,
                       limits=limits)
        return

    # Read info shelf file
    shelf_infodict = load_infodict(pdsdir, logger=logger, limits=limits)

    # Generate info
    (dir_infodict, latest_modtime) = generate_infodict(pdsdir, selection,
                                                       logger=logger,
                                                       limits=limits)
    latest_iso = latest_modtime.replace(' ', 'T')
    latest_datetime = datetime.datetime.fromisoformat(latest_iso)

    # For a single selection, use the old information
    if selection:
        key = list(dir_infodict.keys())[0]
        value = dir_infodict[key]
        dir_infodict = shelf_infodict.copy()
        dir_infodict[key] = value

    # Compare
    canceled = (dir_infodict == shelf_infodict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

        info_pypath = info_path.replace('.pickle', '.py')
        timestamp = min(os.path.getmtime(info_path),
                        os.path.getmtime(info_pypath))
        info_datetime = datetime.datetime.fromtimestamp(timestamp)
        info_iso = info_datetime.isoformat(timespec='microseconds')

        if latest_iso > info_iso:
            logger.info('!!! Info shelf file content is up to date',
                        info_path, force=True)
            logger.info('!!! Latest holdings file modification date',
                        latest_iso, force=True)
            logger.info('!!! Info shelf file modification date',
                        info_iso, force=True)

            delta = (latest_datetime - info_datetime).total_seconds()
            if delta >= 86400/10:
                logger.info('!!! Info shelf file is out of date %.1f days' %
                            (delta / 86400.), force=True)
            else:
                logger.info('!!! Info shelf file is out of date %.1f minutes' %
                            (delta / 60.), force=True)

            dt = datetime.datetime.now()
            os.utime(info_path)
            os.utime(info_pypath)
            logger.info('!!! Time tag on info shelf files set to',
                        dt.strftime('%Y-%m-%dT%H:%M:%S'), force=True)
        else:
            logger.info('!!! Info shelf file is up to date; repair canceled',
                        info_path, force=True)
        return

    # Move files and write new info
    move_old_info(info_path, logger=logger)
    write_infodict(pdsdir, dir_infodict, logger=logger, limits=limits)

def update(pdsdir, selection=None, logger=None, limits={}):

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Make sure info shelf file exists
    if not os.path.exists(info_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        if selection:
            logger.error('Info shelf file does not exist', info_path)
        else:
            logger.warning('Info shelf file does not exist; initializing',
                           info_path)
            initialize(pdsdir, selection=selection, logger=logger,
                       limits=limits)
        return

    # Read info shelf file
    shelf_infodict = load_infodict(pdsdir, logger=logger, limits=limits)

    # Generate info
    (dir_infodict, _) = generate_infodict(pdsdir, selection, shelf_infodict,
                                          logger=logger, limits=limits)

    # Compare
    canceled = (dir_infodict == shelf_infodict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Info shelf file content is complete; update canceled',
                    info_path, force=True)
        return

    # Write checksum file
    move_old_info(info_path, logger=logger)
    write_infodict(pdsdir, dir_infodict, logger=logger, limits=limits)

################################################################################
################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdsinfoshelf: Create, maintain and validate shelf files ' +
                    'containing basic information about each file.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create an infoshelf file for a volume. Abort '   +
                             'if the file already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create an infoshelf file for a volume. Replace ' +
                             'the file if it already exists. If a single '     +
                             'file is specified, such as one archive file in ' +
                             'a volume set, then only information about that ' +
                             'file is re-initialized.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume against the '    +
                             'contents of its infoshelf file. If a single '    +
                             'file is specified, such as an archive file in '  +
                             'a volume set, then only information about that ' +
                             'file is validated')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate every file in a volume against the '    +
                             'contents of its infoshelf file. If any file '    +
                             'has changed, the infoshelf file is replaced. '   +
                             'If a single file is specified, such as an '      +
                             'archive file in a volume set, then only '        +
                             'information about that file is repaired. If any '+
                             'of the files checked are newer than the shelf '  +
                             'file, update the shelf file\'s modification '    +
                             'date.')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a directory for any new files and add '   +
                             'their information to the infoshelf file. '       +
                             'Information about pre-existing files is not '    +
                             'updated. If any of the files checked are newer ' +
                             'than the shelf file, update the shelf file\'s '  +
                             'modification date.')

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
                             '"pdsinfoshelf" subdirectory of each log root '   +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    parser.add_argument('--archives', '-a', default=False, action='store_true',
                        help='Instead of referring to a volume, refer to the ' +
                             'the archive file for that volume.')


    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdsinfoshelf error: Missing task')
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
        path = os.path.join(args.log, 'pdsinfoshelf')
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
            print('No infoshelves for checksum files: ' + path)
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
            # Info about archive directories is stored by volset
            if pdsf.archives_:
                info.append((pdsf, None))

            # Others are checksumed by volume
            else:
                children = [pdsf.child(c) for c in pdsf.childnames]
                info += [(c, None) for c in children if c.isdir]
                        # "if c.isdir" is False for volset level readme files

        elif pdsf.is_volume_dir:
            # Shelve one volume
            info.append((pdsf, None))

        elif pdsf.isdir:
            print('Invalid directory for an infoshelf: ' + pdsf.logical_path)
            sys.exit(1)

        else:
            pdsdir = pdsf.parent()
            if pdsf.is_volume_file:
                # Shelve one archive file
                info.append((pdsdir, pdsf.basename))
            elif pdsdir.is_volume_dir:
                # Shelve one top-level file in volume
                info.append((pdsdir, pdsf.basename))
            else:
                print('Invalid file for an infoshelf: ' + pdsf.logical_path)
                sys.exit(1)

    # Open logger and loop through tuples...
    logger.open(' '.join(sys.argv))
    try:
        for (pdsdir, selection) in info:

            if selection:
                pdsf = pdsdir.child(os.path.basename(selection))
            else:
                pdsf = pdsdir

            # Save logs in up to two places
            if pdsf.volname:
                logfiles = set([pdsf.log_path_for_volume('_info',
                                                         task=args.task,
                                                         dir='pdsinfoshelf'),
                                pdsf.log_path_for_volume('_info',
                                                         task=args.task,
                                                         dir='pdsinfoshelf',
                                                         place='parallel')])
            else:
                logfiles = set([pdsf.log_path_for_volset('_info',
                                                         task=args.task,
                                                         dir='pdsinfoshelf'),
                                pdsf.log_path_for_volset('_info',
                                                         task=args.task,
                                                         dir='pdsinfoshelf',
                                                         place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            LOGDIRS = []            # used by move_old_info()
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
                            selection, pdsdir.abspath, handler=local_handlers)
            else:
                logger.open('Task "' + args.task + '" for', pdsdir.abspath,
                            handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    initialize(pdsdir, selection)

                elif args.task == 'reinitialize':
                    if selection:       # don't erase everything else!
                        update(pdsdir, selection)
                    else:
                        reinitialize(pdsdir, selection)

                elif args.task == 'validate':
                    validate(pdsdir, selection)

                elif args.task == 'repair':
                    repair(pdsdir, selection)

                else:   # update
                    update(pdsdir, selection)

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
        if fatal or errors:
            status = 1

    sys.exit(status)

if __name__ == '__main__':
    main()
