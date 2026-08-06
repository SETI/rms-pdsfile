#!/usr/bin/env python3
################################################################################
# pdsarchives.py library and main program
#
# Syntax:
#   pdsarchives.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import os
import sys
import tarfile
import zlib

import pdslogger

import pdsfile
from pdsfile.holdings_maintenance import _archives_common, _common

LOGNAME = 'pds.validation.archives'

################################################################################
# General tarfile functions
################################################################################

def read_archive_info(tarpath, *, logger=None, limits=None):
    """Return a list of tuples (abspath, dirpath, nbytes, modtime) from a
    .tar.gz file.
    """

    if limits is None:
        limits = {}

    tarpath = os.path.abspath(tarpath)
    pdstar = pdsfile.Pds3File.from_abspath(tarpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdstar.root_)

    if not os.path.exists(tarpath):
        logger.critical('File does not exist', tarpath)
        return []

    merged_limits = _archives_common.READ_ARCHIVE_INFO_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading archive file', tarpath, limits=merged_limits)

    try:
        (_dirpath, prefix) = pdstar.dirpath_and_prefix_for_archive()

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
                  logger=None, limits=None):
    """Write an archive file containing all the files in the directory."""

    if limits is None:
        limits = {}

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    archive_filter = _archives_common.make_archive_filter(SPEC, logger, archive_invisibles)

    merged_limits = _archives_common.WRITE_ARCHIVE_LIMITS.copy()
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
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, *, logger=None, limits=None):
    if limits is None:
        limits = {}
    write_archive(pdsdir, clobber=False, logger=logger, limits=limits)
    return True

def reinitialize(pdsdir, *, logger=None, limits=None):
    if limits is None:
        limits = {}
    write_archive(pdsdir, clobber=True, logger=logger, limits=limits)
    return True

def validate(pdsdir, *, logger=None, limits=None):
    if limits is None:
        limits = {}
    dir_tuples = _archives_common.load_directory_info(SPEC, pdsdir, logger=logger,
                                             limits=limits)

    tarpath = pdsdir.archive_path_and_lskip()[0]
    tar_tuples = read_archive_info(tarpath, logger=logger, limits=limits)

    return _archives_common.validate_tuples(SPEC, dir_tuples, tar_tuples, logger=logger,
                                   limits=limits)

def repair(pdsdir, *, logger=None, limits=None):

    if limits is None:
        limits = {}

    tarpath = pdsdir.archive_path_and_lskip()[0]
    if not os.path.exists(tarpath):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warning('Archive file does not exist; initializing', tarpath)
        initialize(pdsdir, logger=logger, limits=limits)
        return True

    tar_tuples = read_archive_info(tarpath, logger=logger, limits=limits)
    dir_tuples = _archives_common.load_directory_info(SPEC, pdsdir, logger=logger,
                                             limits=limits)

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

def update(pdsdir, *, logger=None, limits=None):

    if limits is None:
        limits = {}

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

def archive_lskip(pdsdir):
    """Return the length of the path prefix that archive-relative paths drop."""

    return pdsdir.archive_path_and_lskip()[1]

def archive_targets(pdsf, path):
    """Return the volume directories one command-line path names."""

    _archives_common.reject_checksum_and_archive_paths(pdsf, path)

    pdsdir = pdsf.volume_pdsfile()
    if pdsdir and pdsdir.isdir:
        return [pdsdir]

    pdsdir = pdsf.volset_pdsfile()
    children = [pdsdir.child(c) for c in pdsdir.childnames]
    return [c for c in children if c.isdir]
            # "if c.isdir" is False for volset level readme files

SPEC = _common.ToolSpec(
    progname='pdsarchives',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds3File,
    unit='volume',
    holdings_sentinel='/holdings/',
    index_ext='.tab',
    file_log_level='info',
    description=_archives_common.ARCHIVE_DESCRIPTION,
    task_help=_archives_common.ARCHIVE_TASK_HELP,
    positional_help=_archives_common.ARCHIVE_POSITIONAL_HELP,
    log_path_method='log_path_for_volume',
    log_suffix='_links',
    expand_target=archive_targets,
    handler_factories=(pdslogger.error_handler,),
    lskip_for=archive_lskip)

TASKS = {'initialize': initialize,
         'reinitialize': reinitialize,
         'validate': validate,
         'repair': repair,
         'update': update}

def main():
    _common.run_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
