#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdsarchives.py
################################################################################

"""pdsarchives: pack a PDS3 volume into a .tar.gz file, and check that the two agree.

One archive file holds one volume directory tree, and sits under the ``archives-``
parallel of the category the volume came from. **A validation compares the two by metadata
alone** -- absolute path, byte count and modification time -- and never reads a file's
contents, which is what makes checking a whole volume set affordable and is what the
``--help`` text says.

What both flavors of this tool do alike is in ``_archives_common``: the walk that
inventories a directory tree, the tarfile member filter that decides what is archived, the
rejection of a command-line path naming checksum or archive files, and the comparison of
the two inventories. What is here is reading a ``.tar.gz`` file back, writing one, and the
five tasks that combine those with the shared pieces.

The two halves diverge more than the shape of the file suggests, and the reason is
structural rather than historical: one PDS3 volume is one archive, so everything here
works on a single archive path, while the PDS4 tool looks its archives up in a table and
loops over however many cover the target.

The driver is ``_common.run_main()``. Its own ``archive_targets()`` is what a command-line
path is expanded by, so each of the five tasks is called with one volume directory and
nothing else, and the True or False each returns is discarded. **Nothing anywhere reads
it**: the driver drops it, and ``re_validate``, the one caller that reaches into this
module as a library, calls ``validate()`` for its side effects and does not assign what
comes back.

The specification's log suffix is '_archives', as the PDS4 tool's is, so a run writes
``<volume>_archives_<time tag>_<task>.log``.

Two fields of the specification are set here and read nowhere a run of this tool reaches:
``index_ext``, which only the index shelf tools' target expansion reads, and
``holdings_sentinel``, whose two readers serve the other three families -- the checksum
and info shelf tools through ``_shelf_common.resolve_holdings_paths()`` and the link shelf
tools through ``_linkshelf_common.locate_nonlocal_link()``.

``file_log_level`` is the opposite case: 'info' is the method three of the four shared
functions report each file through, and the same lines in a PDS4 run go through 'normal'.
That decides which of the shared default limits can reach them, and the three scopes do
not agree: the walk and the comparison are capped at ``{'info': 100}`` for this tool and
uncapped for the PDS4 one, while the archive write is ``{'info': -1}`` and so uncapped for
both.
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

    A missing archive file is reported at critical level, which the run's tally counts as
    a fatal, and the result is an empty list rather than an exception. So a validation of
    a volume that has never been archived reports the absence, gives the comparison
    nothing to match, and ends the run with a nonzero exit status. The check is made
    before the log level for this scope is opened, so the message is written at the level
    the caller had open. The PDS4 tool makes no such check.

    Parameters:
        tarpath (str): The archive file to read. A relative path is made absolute.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the shared defaults.

    Returns:
        list: (absolute path, interior path, nbytes, modtime) tuples, in the order the
        tarfile lists its members, and an empty list if the file does not exist.

    Raises:
        ValueError: raised by ``from_abspath()``, before any log line is written, for a
            path outside every holdings tree.
        OSError: raised by ``tarfile.open()`` for a file that exists and cannot be read.
        tarfile.ReadError: raised by the same ``tarfile.open()`` call for a file that is
            not a gzipped tar. Both it and the OSError above are logged through
            ``exception()`` and re-raised, as is anything else the read raises.
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
    """Write the .tar.gz file for one volume, replacing what is there or refusing to.

    One call writes one archive. The whole tree is handed to ``tarfile`` in a single
    ``add()`` with the shared member filter attached, so what is left out is the filter's
    decision and not this function's, and the interior name each member gets is its
    absolute path with the leading characters ``archive_lskip()`` counts removed.

    The parent directory is created if it is not there, so the first archive of a volume
    set does not need the archives tree to exist first.

    With ``clobber`` false and an archive already there, **this logs an error and
    returns without writing.** Its caller does not learn that: ``initialize()``
    returns True either way.

    The "Written" line is logged before the file is closed, so it records that the members
    were added rather than that the archive is complete on disk.

    Parameters:
        pdsdir: The volume directory to archive. Its abspath is the tree that is added and
            its ``root_`` is what the logger reports paths relative to.
        clobber (bool): True to replace an archive that is already there, False to log an
            error and leave it alone.
        archive_invisibles (bool): True to archive files with a dot component in their
            path, False to skip them. Every call in this package leaves it True.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the shared defaults.

    Raises:
        ValueError: raised by ``archive_path_and_lskip()`` for a directory that is a
            checksum or archive path, or that has no volume name. A command line cannot
            reach the first two, which ``archive_targets()`` rejects before any task runs.
        OSError: raised by ``makedirs()`` if the archives tree cannot be created, and by
            ``tarfile.open()`` or ``add()`` if the archive cannot be written. Each is
            logged through ``exception()`` and re-raised, as is anything else the write
            raises. The partly written archive is left in place, and so is the open file
            object, which is closed only on the path where nothing was raised.
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
    """Write the archive for one volume, refusing to replace one already there.

    The refusal is ``write_archive()``'s, which logs an error and writes nothing when the
    file exists. **This returns True whether it wrote an archive or refused to**, so the
    return value reports that the task ran rather than that anything was written; what
    distinguishes the two is the error line, and through it the run's exit status.

    Parameters:
        pdsdir: The volume directory to archive.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the write.

    Returns:
        bool: True, always.
    """

    if limits is None:
        limits = {}
    write_archive(pdsdir, clobber=False, logger=logger, limits=limits)
    return True

def reinitialize(pdsdir, *, logger=None, limits=None):
    """Write the archive for one volume, replacing whatever is there.

    This is ``initialize()`` with the refusal turned off. Nothing is versioned first: the
    old archive is overwritten in place, and the log-directory versioning the checksum and
    shelf tools do through ``_shelf_common.move_old()`` has no counterpart for archives.

    Parameters:
        pdsdir: The volume directory to archive.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the write.

    Returns:
        bool: True, always.
    """

    if limits is None:
        limits = {}
    write_archive(pdsdir, clobber=True, logger=logger, limits=limits)
    return True

def validate(pdsdir, *, logger=None, limits=None):
    """Report every way one volume and its archive disagree.

    The directory tree is walked, the archive is read, and the two inventories are
    compared. Nothing is written whatever the answer, and every disagreement is logged, so
    one call reports all of them rather than the first.

    This is also the entry point ``re_validate`` reaches, as a library function rather
    than through the command line, for each volume type it was asked to re-validate. It
    does not read the value returned; what it takes from a call is the log the shared
    logger wrote.

    Parameters:
        pdsdir: The volume directory to check.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the walk, the read and the comparison.

    Returns:
        bool: True if the two agree on every entry, False if any error was logged. A
        volume with no archive at all comes back False, since the empty inventory the read
        returns leaves every real file "Missing from tar file".
    """

    if limits is None:
        limits = {}
    dir_tuples = _archives_common.load_directory_info(SPEC, pdsdir, logger=logger,
                                             limits=limits)

    tarpath = pdsdir.archive_path_and_lskip()[0]
    tar_tuples = read_archive_info(tarpath, logger=logger, limits=limits)

    return _archives_common.validate_tuples(SPEC, dir_tuples, tar_tuples, logger=logger,
                                   limits=limits)

def repair(pdsdir, *, logger=None, limits=None):
    """Rewrite one volume's archive if it disagrees with the directory, and not otherwise.

    Both inventories are sorted and compared as whole lists, so this reports that
    something differs and not what: ``validate()`` is the task that names the
    disagreements one by one. Where they differ, the archive is rewritten from scratch;
    where they agree, nothing is written and nothing is touched, which is unlike the
    checksum and shelf tools' repair tasks, since an archive carries no modification date
    of its own to fall behind the files in it.

    A volume with no archive at all is a warning rather than an error, and is handed to
    ``initialize()``.

    Parameters:
        pdsdir: The volume directory to repair the archive of.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the write.

    Returns:
        bool: True if an archive was written or initialized, False if the two agreed and
        the repair was canceled.
    """

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
    """Write the archive for one volume only if there is not one already.

    An archive that is there is left exactly as it is, and its contents are not read: this
    task never discovers that an existing archive is out of date, which is what the
    ``--help`` text means by saying that pre-existing archive files are not updated. Its
    use is a command line naming a volume set, which ``archive_targets()`` expands into
    every volume in it, so a set that has gained a volume gets that one archived and the
    rest untouched.

    Parameters:
        pdsdir: The volume directory to archive if it has no archive.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the write.

    Returns:
        bool: True if an archive was written, False if one was already there.
    """

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
    """Return the length of the path prefix that archive-relative paths drop.

    This is the specification's ``lskip_for``, and it is read in one place:
    ``_archives_common.load_directory_info()`` calls it once per walk and slices that many
    characters off each absolute path to form the interior path the tuple carries.
    ``write_archive()`` takes the same count from the same method for the interior names
    it gives the members, so the two agree by construction rather than by arrangement.

    The count ends before the volume name, so an interior path begins with it. It counts
    characters of the **archived directory's** path and not of the archive file's, which
    carries an extra "archives-" component; the two are the two halves of one call and
    only the second one is used here.

    Parameters:
        pdsdir: The volume directory being archived.

    Returns:
        int: The number of leading characters to drop.

    Raises:
        ValueError: raised by ``archive_path_and_lskip()`` for a directory that is a
            checksum or archive path, or that has no volume name.
    """

    return pdsdir.archive_path_and_lskip()[1]

def archive_targets(pdsf, path):
    """Return the volume directories one command-line path names.

    This is the specification's ``expand_target``, which ``_common.run_main()`` calls once
    per command-line path, and it is what makes a command line naming a volume set do the
    work for every volume in it.

    A path resolving to a volume gives that volume. Anything else is taken as naming a
    volume set, whose directory children are returned and whose files are not, which is
    what leaves a volume-set level readme out.

    Parameters:
        pdsf: The PdsFile the command-line path resolved to.
        path (str): The absolute path it resolved to, for the rejection messages.

    Returns:
        list: The volume directories to archive, which is one directory or all of a volume
        set's.

    Raises:
        SystemExit: from ``sys.exit()`` inside
            ``_archives_common.reject_checksum_and_archive_paths()``, with status 1 for a
            path naming checksum files or archive files.
        AttributeError: from the ``childnames`` read, for a path that has neither a volume
            nor a volume set above it, such as a category directory: ``volset_pdsfile()``
            answers None there and nothing checks it. The PDS4 tool cannot reach this, as
            its own expansion returns the path itself.
    """

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
    log_suffix='_archives',
    expand_target=archive_targets,
    handler_factories=(pdslogger.error_handler,),
    lskip_for=archive_lskip)

TASKS = {'initialize': initialize,
         'reinitialize': reinitialize,
         'validate': validate,
         'repair': repair,
         'update': update}

def main():
    """Run the tool: hand this module's specification and tasks to the generic driver.

    This is the ``pdsarchives`` console script's entry point. It does not return: the
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
