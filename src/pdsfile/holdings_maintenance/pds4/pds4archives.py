#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds4/pds4archives.py
################################################################################

"""pds4archives: pack PDS4 bundle directories into .tar.gz files, and check they agree.

**How many archives cover one target, and what goes in each, is looked up rather than
derived.** A bundle set's rule module installs an ``ARCHIVE_PATHS`` table saying which
archive files cover a logical path and an ``ARCHIVE_DIRS`` table saying which directories
each of those packages, and every task here loops over what those two answer. That is the
whole of the difference between this tool and the PDS3 one, and it runs through all five
tasks. A target that no rule matches resolves to no archive paths at all, and the five do
not agree about that: ``validate()``, ``repair()`` and ``update()`` iterate over an empty
list and report nothing, while ``initialize()`` and ``reinitialize()`` reach
``write_archive()``, which logs an error and then raises.

Validation compares an archive against the directories it packages by metadata alone --
absolute path, byte count and modification time -- and never reads a file's contents,
which is what the ``--help`` text says and what makes checking a whole bundle set
affordable. The directory inventory is taken once for the whole target and then narrowed,
per archive, to the entries at or below one of that archive's own directories.

What both flavors do alike is in ``_archives_common``: the walk that inventories a
directory tree, the tarfile member filter, the rejection of a command-line path naming
checksum or archive files, and the comparison of the two inventories. What is here is
reading a ``.tar.gz`` file back, writing the set of them, and the five tasks.

The driver is ``_common.run_main()``, and this tool's ``archive_targets()`` expands
nothing: a command-line path becomes one target, whatever level it names, because the
tables decide the granularity. A bundle set therefore reaches the tasks as a single target
rather than as one target per bundle.

Two fields of the specification are set here and read nowhere a run of this tool reaches:
``index_ext``, which only the index shelf tools' target expansion reads, and
``holdings_sentinel``, which only the other two families read. ``file_log_level`` is
'normal', so the ``{'info': N}`` entries in the shared default limits do not cap this
tool's per-file lines, and ``handler_factories`` adds a warning handler ahead of the error
handler, so a run leaves a warning file in each log directory that a PDS3 run does not.

``progname`` is 'pdsarchives', not this module's name, which is the convention all five
PDS4 tools follow: it is what the ``--help`` description and the "Missing task" error call
the tool, and it names the subdirectory of every log root, so both flavors write into one
directory.
"""

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
    """Return what one archive file holds, as the tuples a directory tree is compared to.

    This is the other half of the pair ``_archives_common.validate_tuples()`` compares:
    that function's first argument comes from a walk of the filesystem and its second from
    a call to this. The two are built to the same shape, so a member's absolute path is
    reconstructed by joining the prefix the archive was written under to the member's own
    interior name, and a directory member contributes a byte count and a modification time
    of zero exactly as a directory on disk does.

    **Three kinds of member are logged and then inventoried anyway.** A ``.DS_Store`` and
    a dot-underscore file are each reported as an error, and an invisible file under a
    level of its own, but none of the three is left out of the result. Since the walk this
    is compared against does leave the first two out, such a member is reported twice:
    once here, and again as "Missing from directory".

    **An archive file that is not there is an exception rather than a report.** Nothing
    checks for it, so the open raises, the failure is logged through ``exception()`` and
    re-raised, and the run ends there instead of recording that the bundle has never been
    archived. The PDS3 tool checks first and returns an empty list.

    Parameters:
        tarpath (str): The archive file to read. A relative path is made absolute.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the shared defaults.

    Returns:
        list: (absolute path, interior path, nbytes, modtime) tuples, in the order the
        tarfile lists its members.

    Raises:
        ValueError: raised by ``from_abspath()``, before any log line is written, for a
            path outside every holdings tree.
        OSError: raised by ``tarfile.open()`` for a file that is not there or cannot be
            read.
        tarfile.ReadError: raised by the same ``tarfile.open()`` call for a file that is
            not a gzipped tar. Both it and the OSError above are logged through
            ``exception()`` and re-raised, as is anything else the read raises.
    """

    if limits is None:
        limits = {}

    tarpath = os.path.abspath(tarpath)
    pdstar = pdsfile.Pds4File.from_abspath(tarpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdstar.root_)

    merged_limits = _archives_common.READ_ARCHIVE_INFO_LIMITS.copy()
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
    """Write every .tar.gz file that covers one target, as the archive tables define them.

    One call writes as many archives as ``archive_paths()`` returns, and each is filled
    with the directories ``archive_dirs()`` maps it to, added one at a time under the
    shared member filter. **A member's interior name is the basename of the directory it
    came from and the path below it**, so an archive holds its directories side by side
    with nothing above them, however deep in the holdings tree they sat.

    The parent directory is created if it is not there, and it is taken from the first
    archive path alone: a target whose archives span more than one directory has only the
    first of them created here.

    With ``clobber`` false, an archive already in place is reported as an error and the
    loop **continues** to the next one, so the missing archives of a partly archived
    target are still written. That is what makes it usable by ``update()``.

    Parameters:
        pdsdir: The target to archive. Its ``archive_paths()`` and ``archive_dirs()`` say
            what is written, and its ``root_`` is what the logger reports paths relative
            to.
        clobber (bool): True to replace archives that are already there, False to report
            each and write only the ones that are missing.
        archive_invisibles (bool): True to archive files with a dot component in their
            path, False to skip them. Every call in this package leaves it True.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the shared defaults.

    Raises:
        RuntimeError: from the bare ``raise`` below the "No archive paths resolved"
            report, which has no exception to re-raise, so what a target with no archives
            gets is not the error it just logged. It is caught by this function's own
            ``exception()`` handler like any other, logged, and re-raised.
        OSError: raised by ``makedirs()`` if the archives tree cannot be created, and by
            ``tarfile.open()`` or ``add()`` if an archive cannot be written. Each is
            logged through ``exception()`` and re-raised, as is anything else the write
            raises, and the archives written before it are left in place.
    """

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
    """Write the archives for one target, refusing to replace any already there.

    The refusal is ``write_archive()``'s, which reports each archive already in place and
    writes the rest. **This returns True whether it wrote anything or refused
    everything**, so the return value reports that the task ran rather than that anything
    was written; what distinguishes the two is the error line, and through it the run's
    exit status.

    Parameters:
        pdsdir: The target to archive.
        logger: The logger to report through. Defaults to the tool's own.

    Returns:
        bool: True, always.
    """

    write_archive(pdsdir, clobber=False, logger=logger)
    return True

def reinitialize(pdsdir, logger=None):
    """Write the archives for one target, replacing whatever is there.

    This is ``initialize()`` with the refusal turned off. Nothing is versioned first: each
    old archive is overwritten in place, and the log-directory versioning the checksum and
    shelf tools do through ``_shelf_common.move_old()`` has no counterpart for archives.

    Parameters:
        pdsdir: The target to archive.
        logger: The logger to report through. Defaults to the tool's own.

    Returns:
        bool: True, always.
    """

    write_archive(pdsdir, clobber=True, logger=logger)
    return True

def validate(pdsdir, logger=None):
    """Report every way one target's directories and its archives disagree.

    The directory tree is walked once, and each archive is then compared against the part
    of that inventory belonging to the directories that archive packages: an entry counts
    for an archive if its absolute path is one of those directories or lies below it.
    **An entry belonging to no archive's directories is compared against nothing and is
    not reported**, so a file the tables leave out of every archive passes.

    Nothing is written whatever the answer. The first archive that disagrees ends the
    task, so a target with several archives reports the disagreements of one of them and
    says nothing about the rest.

    Parameters:
        pdsdir: The target to check.
        logger: The logger to report through. Defaults to the tool's own.

    Returns:
        bool: True if every archive agrees with the directories it packages, False at the
        first one that does not. A target that resolves to no archives is True.
    """

    dir_tuples = _archives_common.load_directory_info(SPEC, pdsdir, logger=logger)

    archive_paths = pdsdir.archive_paths()
    archive_dirs = pdsdir.archive_dirs()

    for tarpath in archive_paths:
        tar_tuples = read_archive_info(tarpath, logger=logger)

        roots = archive_dirs[tarpath]
        actual_dir_tuples = [
            t for t in dir_tuples
            if any(t[0] == root or t[0].startswith(root + '/') for root in roots)
        ]

        valid = _archives_common.validate_tuples(SPEC, actual_dir_tuples, tar_tuples,
                                        logger=logger)

        if not valid:
            return False

    return True

def repair(pdsdir, logger=None):
    """Rewrite one target's archives if the first disagreeing one is found.

    Each archive is compared, as whole sorted lists, against the part of the directory
    inventory it packages, so this reports that something differs and not what;
    ``validate()`` is the task that names the disagreements one by one.

    **The loop ends at the first archive it acts on.** An archive that is missing is
    initialized and this returns; one that disagrees is rewritten and this returns; only
    an archive that agrees lets the loop reach the next. So a target whose second archive
    is wrong is repaired on the first run only as far as that archive, and running the
    task again is what reaches the rest.

    What it acts with is coarser still: both branches call a function that rewrites
    **every** archive of the target rather than the one that was wrong. A missing archive
    reaches ``initialize()``, which writes the missing ones and reports the rest as
    already there; a disagreeing one reaches a clobbering write, which replaces all of
    them.

    Parameters:
        pdsdir: The target to repair the archives of.
        logger: The logger to report through. Defaults to the tool's own.

    Returns:
        bool: True if anything was written, False if every archive agreed or the target
        resolved to none.
    """

    archive_paths = pdsdir.archive_paths()
    archive_dirs = pdsdir.archive_dirs()
    dir_tuples = _archives_common.load_directory_info(SPEC, pdsdir, logger=logger)

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
    """Write whichever of one target's archives are missing, and leave the rest alone.

    An archive that is there is left exactly as it is and its contents are not read: this
    task never discovers that an existing archive is out of date, which is what the
    ``--help`` text means by saying that pre-existing archive files are not updated.

    The loop stops at the first missing archive, because the write it then makes is not of
    that archive alone: it is a non-clobbering write of the whole target, which fills in
    every missing archive and reports every archive already in place as an error. So one
    call does write all of them, and the report of an already-archived directory arrives
    as an error line rather than as this task's own "skipping" line.

    Parameters:
        pdsdir: The target to fill in the archives of.
        logger: The logger to report through. Defaults to the tool's own.

    Returns:
        bool: True if any archive was missing, False if all of them were there or the
        target resolved to none.
    """

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
    """Return the length of the path prefix that archive-relative paths drop.

    This is the specification's ``lskip_for``, and it is read in one place:
    ``_archives_common.load_directory_info()`` calls it once per walk and slices that many
    characters off each absolute path to form the interior path the tuple carries. The
    count reaches the end of the bundle set, so an interior path begins with the bundle
    name.

    **It is computed from the target's own path components rather than looked up**, which
    is unlike everything else about this tool, and it is not the count the archives are
    written with: ``write_archive()`` gives each member the basename of its own packaged
    directory and the path below it. The two agree wherever an archive packages a bundle
    directory sitting directly under the bundle set, and they are the reason a comparison
    matches on absolute path rather than on the interior one.

    Parameters:
        pdsdir: The target being archived.

    Returns:
        int: The number of leading characters to drop, which is the length of the root,
        the category and the bundle set together.
    """

    return len(pdsdir.root_) + len(pdsdir.category_) + len(pdsdir.bundleset_)

def archive_targets(pdsf, path):
    """Return the bundle directories one command-line path names.

    This is the specification's ``expand_target``, which ``_common.run_main()`` calls once
    per command-line path. **It expands nothing**: whatever the path named comes back as
    one target, at whatever level it named, because how a target is split into archives is
    the archive tables' answer rather than this function's. A bundle set therefore reaches
    the tasks whole, where the PDS3 tool would hand its driver one target per bundle.

    Parameters:
        pdsf: The PdsFile the command-line path resolved to.
        path (str): The absolute path it resolved to, for the rejection messages.

    Returns:
        list: The one PdsFile, in a list, so that the driver can concatenate it with what
        the other command-line paths returned.

    Raises:
        SystemExit: from ``sys.exit()`` inside
            ``_archives_common.reject_checksum_and_archive_paths()``, with status 1 for a
            path naming checksum files or archive files.
    """

    _archives_common.reject_checksum_and_archive_paths(pdsf, path)

    # pdsdirs: a list, each element is the path of a bundle set, bundle, or a bundle
    # collection
    return [pdsf]

SPEC = _common.ToolSpec(
    progname='pdsarchives',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds4File,
    unit='bundle',
    holdings_sentinel='/pds4-holdings/',
    index_ext='.csv',
    file_log_level='normal',
    description=_archives_common.ARCHIVE_DESCRIPTION,
    task_help=_archives_common.ARCHIVE_TASK_HELP,
    positional_help=_archives_common.ARCHIVE_POSITIONAL_HELP,
    log_path_method='log_path_for_bundle',
    log_suffix='_archives',
    expand_target=archive_targets,
    handler_factories=(pdslogger.warning_handler, pdslogger.error_handler),
    lskip_for=archive_lskip)

TASKS = {'initialize': initialize,
         'reinitialize': reinitialize,
         'validate': validate,
         'repair': repair,
         'update': update}

def main():
    """Run the tool: hand this module's specification and tasks to the generic driver.

    This is the ``pds4archives`` console script's entry point. It does not return: the
    driver exits with status 1 if the run logged a fatal or an error and 0 otherwise, and
    exits before opening a log for a command line that names no task or a path that does
    not exist.

    Raises:
        SystemExit: from ``_common.run_main()``, on every path out of a run that is not an
            exception.
    """

    _common.run_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
