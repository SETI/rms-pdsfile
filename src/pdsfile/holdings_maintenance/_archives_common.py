##########################################################################################
# pdsfile/holdings_maintenance/_archives_common.py
#
# What the two archive tools share.
#
# The generic driver the tools of every family run on is in _common.py; this is
# the part only pdsarchives and pds4archives use.
##########################################################################################

import os
import sys

import pdslogger

from pdsfile.holdings_maintenance._common import BACKUP_FILENAME


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
