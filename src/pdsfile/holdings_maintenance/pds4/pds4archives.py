#!/usr/bin/env python3
################################################################################
# pdsarchives.py library and main program
#
# Syntax:
#   pds4archives.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import os
import sys
import tarfile
import zlib

import pdslogger

import pdsfile
from pdsfile.holdings_maintenance import _common

LOGNAME = 'pds.validation.archives'

################################################################################
# General tarfile functions
################################################################################

def read_archive_info(tarpath, *, logger=None, limits=None):
    """Return a list of tuples (abspath, dirpath, nbytes, modtime) from a .tar.gz
    file."""

    if limits is None:
        limits = {}

    tarpath = os.path.abspath(tarpath)
    pdstar = pdsfile.Pds4File.from_abspath(tarpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdstar.root_)

    merged_limits = _common.READ_ARCHIVE_INFO_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading archive file', tarpath, limits=merged_limits)

    try:
        (_, prefix) = pdstar.dirpath_and_prefix_for_archive()

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

                logger.normal('Info read', abspath)

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
    archive_filter = _common.make_archive_filter(SPEC, logger, archive_invisibles)

    merged_limits = _common.WRITE_ARCHIVE_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing .tar.gz file for', dirpath, limits=merged_limits)

    try:
        archive_paths = pdsdir.archive_paths()
        archive_dirs = pdsdir.archive_dirs()

        if not archive_paths:
            logger.error('No archive paths resolved for', pdsdir.logical_path)
            raise

        # Create parent directory if necessary
        tarpath = archive_paths[0]
        parent = os.path.split(tarpath)[0]
        if not os.path.exists(parent):
            logger.normal('Creating directory', parent)
            os.makedirs(parent)

        for tarpath in archive_paths:
            if not clobber and os.path.exists(tarpath):
                logger.error('Archive file already exists', tarpath)
                # keep checking and creating archive files that are missing
                continue

            current_archive_dirs = archive_dirs[tarpath]

            logger.normal('Open for gzip compressed writing', tarpath)
            with tarfile.open(tarpath, mode='w:gz') as tar:
                for dir_path in current_archive_dirs:
                    _, _, fname = dir_path.rpartition('/')
                    tar.add(dir_path, arcname=fname, recursive=True,
                            filter=archive_filter)


    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, logger=None):
    write_archive(pdsdir, clobber=False, logger=logger)
    return True

def reinitialize(pdsdir, logger=None):
    write_archive(pdsdir, clobber=True, logger=logger)
    return True

def validate(pdsdir, logger=None):

    dir_tuples = _common.load_directory_info(SPEC, pdsdir, logger=logger)

    archive_paths = pdsdir.archive_paths()
    archive_dirs = pdsdir.archive_dirs()

    for tarpath in archive_paths:
        tar_tuples = read_archive_info(tarpath, logger=logger)

        roots = archive_dirs[tarpath]
        actual_dir_tuples = [
            t for t in dir_tuples
            if any(t[0] == root or t[0].startswith(root + '/') for root in roots)
        ]

        valid = _common.validate_tuples(SPEC, actual_dir_tuples, tar_tuples,
                                        logger=logger)

        if not valid:
            return False

    return True

def repair(pdsdir, logger=None):

    archive_paths = pdsdir.archive_paths()
    archive_dirs = pdsdir.archive_dirs()
    dir_tuples = _common.load_directory_info(SPEC, pdsdir, logger=logger)

    for tarpath in archive_paths:
        if not os.path.exists(tarpath):
            logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
            logger.warning('Archive file does not exist; initializing', tarpath)
            initialize(pdsdir, logger=logger)
            return True

        tar_tuples = read_archive_info(tarpath, logger=logger)

        roots = archive_dirs[tarpath]
        actual_dir_tuples = [
            t for t in dir_tuples
            if any(t[0] == root or t[0].startswith(root + '/') for root in roots)
        ]

        # Compare
        actual_dir_tuples.sort()
        tar_tuples.sort()
        canceled = (actual_dir_tuples == tar_tuples)
        if canceled:
            logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
            logger.info('!!! Files match; repair canceled', tarpath)
            continue

        # Overwrite tar file if necessary
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('Discrepancies found; writing new file', tarpath)
        write_archive(pdsdir, clobber=True, logger=logger)
        return True

    # no repair is performed
    return False

def update(pdsdir, logger=None):

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    archive_paths = pdsdir.archive_paths()
    wrote_any = False

    for tarpath in archive_paths:
        if os.path.exists(tarpath):
            logger.info('Archive file exists; skipping', tarpath)
            continue
        # write only missing ones in write_archive
        write_archive(pdsdir, clobber=False, logger=logger)
        wrote_any = True
        # All missing archive files are created in write_archive
        break

    return wrote_any

################################################################################
# Executable program
################################################################################

def archive_lskip(pdsdir):
    """Return the length of the path prefix that archive-relative paths drop."""

    return len(pdsdir.root_) + len(pdsdir.category_) + len(pdsdir.bundleset_)

def archive_log_path(pdsdir, task, place='default'):
    """Return the path of the log file for one bundle and task."""

    return pdsdir.log_path_for_bundle('_archives', task=task, dir='pdsarchives',
                                      place=place)

def archive_targets(pdsf, path):
    """Return the bundle directories one command-line path names."""

    _common.reject_checksum_and_archive_paths(pdsf, path)

    # pdsdirs: a list, each element is the path of a bundle set, bundle, or a bundle
    # collection
    return [pdsf]

SPEC = _common.ToolSpec(
    progname='pdsarchives',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds4File,
    unit='bundle',
    file_log_level='normal',
    description=_common.ARCHIVE_DESCRIPTION,
    task_help=_common.ARCHIVE_TASK_HELP,
    positional_help=_common.ARCHIVE_POSITIONAL_HELP,
    log_path_for=archive_log_path,
    expand_target=archive_targets,
    handler_factories=(pdslogger.warning_handler, pdslogger.error_handler),
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
