##########################################################################################
# pdsfile/holdings_maintenance/_shelf_common.py
#
# What the checksum and shelf file tools share.
#
# The generic driver the tools of every family run on is in _common.py; this is
# the part only the checksums, infoshelf, linkshelf and indexshelf tools use.
##########################################################################################

import glob
import hashlib
import os
import shutil
from dataclasses import dataclass

import pdslogger

# The PdsLogger name each tool kind logs under. Both flavors of a kind share one.
CHECKSUMS_LOGNAME = 'pds.validation.checksums'
INFOSHELF_LOGNAME = 'pds.validation.fileinfo'
LINKSHELF_LOGNAME = 'pds.validation.links'


@dataclass(kw_only=True)
class VersionedFile:
    """What move_old() needs to know about one kind of file it versions.

    Attributes:
        noun: How the file is named in the two log lines, e.g. 'Checksum file'.
        logname: The PdsLogger name to fall back on when no logger is given.
        companions: The extensions of the files that travel with it. Each is copied
            beside the versioned file under the same name and its own extension. A
            link shelf lists '.pickle', which names the shelf file itself, so that
            file is copied twice to the one destination.
    """

    noun: str
    logname: str
    companions: tuple = ()


CHECKSUM_FILE = VersionedFile(noun='Checksum file', logname=CHECKSUMS_LOGNAME)
INFO_SHELF = VersionedFile(noun='Info shelf file', logname=INFOSHELF_LOGNAME,
                           companions=('.py',))
LINK_SHELF = VersionedFile(noun='Link shelf file', logname=LINKSHELF_LOGNAME,
                           companions=('.py', '.pickle'))

# The log directories a superseded checksum or shelf file is versioned into. A tool's
# main() fills this in for each target it is about to work on; a process that never
# calls set_log_dirs leaves it empty, and then move_old() versions nothing.
LOGDIRS = []


def set_log_dirs(logfiles):
    """Record the log directories move_old() versions a superseded file into.

    Args:
        logfiles: The log file paths of the target about to be worked on. The
            directory of each is what a superseded file is copied into.
    """

    global LOGDIRS
    LOGDIRS = [os.path.split(logfile)[0] for logfile in logfiles]


def next_version_dest(log_dir, prefix, ext):
    """Return the unused <prefix>_v###<ext> path in one log directory.

    ### is one past the highest version already there, and 001 when there is none.

    Args:
        log_dir: The directory the versioned copy goes in.
        prefix: The superseded file's basename without its extension.
        ext: That extension, including the dot.

    Returns:
        str: The path to copy to.
    """

    dest_template = log_dir + '/' + prefix + '_v???' + ext

    max_version = 0
    lskip = len(ext)
    for version_path in glob.glob(dest_template):
        max_version = max(max_version, int(version_path[-lskip-3:-lskip]))

    return dest_template.replace('???', f'{max_version + 1:03d}')


def move_old(path, kind, *, logger=None):
    """Version the file a task is about to replace, into every recorded log directory.

    The file is copied rather than moved, despite what the log lines say: the
    original stays where it is and the task then overwrites it.

    Args:
        path: The file about to be replaced. Nothing happens if it does not exist,
            or if no log directory has been recorded.
        kind: The VersionedFile describing it.
        logger: The logger to report through. Defaults to the kind's own.
    """

    if not os.path.exists(path):
        return

    logger = logger or pdslogger.PdsLogger.get_logger(kind.logname)

    (prefix, ext) = os.path.splitext(os.path.basename(path))
    stem = path.rpartition('.')[0]

    from_logged = False
    for log_dir in LOGDIRS:
        dest = next_version_dest(log_dir, prefix, ext)
        shutil.copy(path, dest)

        # Both lines pass the path as the second argument, so PdsLogger renders the
        # colon and applies the logger's root replacement to it. force=True keeps a
        # limits cap from dropping the report of a change to the filesystem.
        if not from_logged:
            logger.info(kind.noun + ' moved from', path, force=True)
            from_logged = True

        logger.info(kind.noun + ' moved to', dest, force=True)

        dest_stem = dest.rpartition('.')[0]
        for companion in kind.companions:
            shutil.copy(stem + companion, dest_stem + companion)


# From http://stackoverflow.com/questions/3431825/-
#       generating-an-md5-checksum-of-a-file

def hashfile(fname, blocksize=65536):
    hasher = hashlib.md5()

    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), b''):
            hasher.update(chunk)

    return hasher.hexdigest()
