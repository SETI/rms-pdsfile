#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdschecksums.py
################################################################################

"""pdschecksums: write and check the MD5 manifest of a PDS3 volume.

A checksum file is a text manifest, one line per file, holding a 32-character MD5 digest
and the file's path below the volume set. It sits in the ``checksums-<category>/``
parallel of the tree it describes, and what one manifest covers is
``checksum_path_and_lskip()``'s answer rather than this tool's: one file per volume in an
ordinary category, one for the whole volume set in an archives category, and one for each
of the three kinds of directory that sit under a volume set without being a volume -- a
name starting ``checksums_``, a name starting ``superseded``, or a name ending
``_support``. This tool writes those manifests and checks a tree against one.

The driver is ``_shelf_common.run_selection_main()``, which this tool reaches because a
command-line path here can name **one file inside a volume** as well as a whole volume or
volume set. Every task below therefore takes a ``selection``, which is a basename and not
a path, and a task given one narrows its work to the file of that name while leaving every
other entry in the manifest as it was. The driver enforces the one case where that is not
safe by itself: ``reinitialize`` on a selection is run as ``update`` instead, since
rebuilding a whole manifest from one named file would erase the rest of it.

``--archives`` redirects a command-line path to the archive files of the same target, and
``--infoshelf`` chains a run of ``pdsinfoshelf`` over the same command line after a
successful one here. Both come from ``_shelf_common``, which the info shelf tool also
takes its ``--archives`` option from.

Beyond the driver and the path resolution, what this tool shares with the rest is small
and specific: ``_shelf_common.hashfile()`` computes a digest, ``_shelf_common.move_old()``
versions the manifest a task is about to replace into the run's log directories, and
``CHECKSUM_FILE`` is the record that says how. Everything else here -- the walk, the
manifest format, the comparison -- is this module's, and is a near-copy of the PDS4
tool's. The differences between the two are worth knowing and none of them is a difference
of purpose; they are recorded on the functions that carry them.

**A run's exit status does not report what a task found.** The driver returns rather than
exiting and ``main()`` never reads the status it computed, so a ``--validate`` that
reported every file in a volume as a mismatch still exits 0. What a run does exit nonzero
for is everything settled before a task starts -- a command line naming no task exits 1, a
command line the parser cannot classify exits 2, and a path outside a holdings tree or
naming checksum files exits 1 -- and a task that raises ends the process through the
traceback. That is deliberate in the driver, which leaves the decision to the tool, and
the silence about what a task found is a property of these two tools rather than of the
other eight.

Two fields of the specification are set here and read nowhere a run of this tool reaches.
``index_ext`` is read only by the index shelf tools' target expansion. And
``file_log_level`` is set to 'info' and reaches nothing: its four readers are all in the
archive and link shelf machinery, and the per-file lines below name their level directly,
which is why the same lines go through ``info()`` here and through ``normal()`` in the
PDS4 tool without either tool reading the field that says so. ``log_path_method`` is a
third field this driver never consults, and it is not set here at all: it stays at its
empty default, because the driver picks between the volume and the volume set log path per
target instead.
"""

import datetime
import os
import re
import subprocess
import sys

import pdslogger

import pdsfile
from pdsfile.holdings_maintenance import _common, _shelf_common

LOGNAME = _shelf_common.CHECKSUMS_LOGNAME

# Default limits
GENERATE_CHECKSUMS_LIMITS = {'info': -1}
READ_CHECKSUMS_LIMITS = {'debug': 0}
WRITE_CHECKSUMS_LIMITS = {'dot_': -1, 'ds_store': -1, 'invisible': 100}
VALIDATE_PAIRS_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################

def generate_checksums(pdsdir, selection=None, oldpairs=[], *, regardless=True,
                       logger=None, limits=None):
    """Return the MD5 digest of every file in one volume, and the newest date seen.

    The walk is recursive and covers files only; a directory has no digest and contributes
    nothing. Four kinds of file are left out: a ``.DS_Store``, a dot-underscore file, a
    backup file matching ``BACKUP_FILENAME`` or carrying " copy" in its basename, and,
    with a selection, everything not named by it. An invisible file is logged and kept.

    **A digest is computed only where one is not already known.** ``oldpairs`` seeds a
    dictionary of what is known, so a file already in it is copied across rather than
    re-read, which is what makes an update of a large volume affordable. ``regardless``
    overrides that for a selection alone: with both set, the named file is re-read even
    though its digest is there.

    **The modification time is the newest among every file the walk sees**, taken before
    any of the four skip tests and whether or not the file is opened. A ``.DS_Store`` or a
    backup file touched today therefore moves it, and so does a file excluded by the
    selection. The callers that compare it against the manifest's own date rely on that
    reading: it answers "has anything under here changed", not "has anything checksummed
    here changed".

    The order of the result is the order of ``oldpairs`` first, in full, and then the
    files the walk found that were not already in it, in walk order.

    Parameters:
        pdsdir: The volume directory to walk. Its abspath is the root of the walk and its
            ``root_`` is what the logger reports paths relative to.
        selection (str): The basename of the one file to digest, or None for all of them.
        oldpairs (list): (absolute path, digest) pairs already known.
            **A mutable default** of ``[]``, **which nothing here writes to.**
        regardless (bool): True to digest a selection even where ``oldpairs`` already
            carries it.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over this module's defaults.

    Returns:
        tuple: the (absolute path, digest) pairs, and the newest modification time as a
        timestamp. **A selection that matched no file, or more than one, gives an empty
        dict rather than an empty list** for the first element, which every caller reads
        only for truth and none for its type; the PDS4 tool returns a list there.

    Raises:
        OSError: raised by ``getmtime()`` on a file the walk listed and that is gone by
            the time it is measured, and by ``hashfile()`` on one that cannot be read.
            Each is logged through ``exception()`` and re-raised, as is anything else the
            walk raises.
        KeyError: from the ``__getitem__()`` that re-reads the digest dictionary while
            restoring the original order, if ``oldpairs`` names one path twice: the first
            occurrence deletes the entry the second needs.
    """

    if limits is None:
        limits = {}

    dirpath = pdsdir.abspath

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = GENERATE_CHECKSUMS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Generating MD5 checksums', dirpath, limits=merged_limits)

    latest_mtime = 0.
    try:
        md5_dict = {}
        for (abspath, old_md5) in oldpairs:
            md5_dict[abspath] = old_md5

        newtuples = []
        for (path, _dirs, files) in os.walk(dirpath):
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
                    md5 = _shelf_common.hashfile(abspath)
                    newtuples.append((abspath, md5, file))
                    logger.info('Selected MD5=%s' % md5, abspath)

                elif abspath in md5_dict:
                    newtuples.append((abspath, md5_dict[abspath], file))
                    logger.debug('MD5 copied', abspath)

                else:
                    md5 = _shelf_common.hashfile(abspath)
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

        for (key, _new_md5, _new_file) in newtuples:
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

def read_checksums(check_path, selection=None, *, logger=None, limits=None):
    """Return what one MD5 manifest holds, as the pairs a fresh walk is compared to.

    **The manifest is parsed by fixed offsets, not by splitting.** A record's first 32
    characters are the digest and everything from the 35th to the end of the line,
    stripped of trailing whitespace, is the path; the two characters between are the
    separator this module writes and are not examined. **A record too short to hold a
    path, a blank line among them, ends the whole read**: the basename it yields is empty
    and the test for an invisible file subscripts it. With a selection given, such a
    record is dropped by the basename comparison above that test and the read completes,
    so whether a manifest can be read at all depends on the task.

    Each path is made absolute by putting the manifest's own prefix in front of it, which
    is the counterpart of the trimming ``write_checksums()`` does.

    A ``.DS_Store`` entry and a dot-underscore entry are each reported as an error and
    left out; an invisible entry is logged and kept. A manifest that is not there is an
    error and an empty list, and so is a selection that no record names.

    Parameters:
        check_path (str): The manifest to read. A relative path is made absolute.
        selection (str): The basename of the one entry to return, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over this module's defaults.

    Returns:
        list: the (absolute path, digest) pairs, in the order the records were read, and
        an empty list for a missing manifest or an unmatched selection.

    Raises:
        IndexError: from the ``__getitem__()`` that tests a basename's first character,
            for a record with no path in it.
        ValueError: raised by ``from_abspath()``, before any log line is written, for a
            path outside every holdings tree.
        OSError: raised by ``open()`` for a manifest that exists and cannot be read. It is
            logged through ``exception()`` and re-raised, as is anything else the read
            raises. A ``KeyboardInterrupt`` is not: this handler catches ``Exception``
            alone, so an interrupt here closes the log level and propagates unlogged. Of
            the ten other functions in this module, three catch and log an interrupt and
            seven install no handler at all, so this is the only one whose handler is
            narrower than what it lets past.
    """

    if limits is None:
        limits = {}

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
        with open(check_path) as f:
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

def checksum_dict(dirpath, *, logger=None, limits=None):
    """Return one volume's shelved digests, keyed by absolute path.

    This is the accessor ``pdsinfoshelf`` uses rather than one this module's own tasks
    need: an info shelf entry carries the file's digest, and this is where it comes from.
    It resolves the manifest's path from the directory, reads it, and turns the pairs into
    a dictionary, so a path listed twice keeps the digest of its last record.

    Unlike the two functions here that read or write a manifest, it opens no log level
    of its own, so its "Loading checksums for" and "Checksum load completed" lines are
    written at whatever level the caller had open, and both are forced past any message
    limit.

    Parameters:
        dirpath (str): The volume directory whose manifest is to be read. A relative path
            is made absolute.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read.

    Returns:
        dict: the digest of each file, keyed by absolute path, and empty if the manifest
        is not there.

    Raises:
        ValueError: raised by ``from_abspath()`` for a path outside every holdings tree,
            and by ``checksum_path_and_lskip()`` for one inside a holdings tree that has
            no volume name or that already names checksum files.
        OSError: raised by ``read_checksums()`` for a manifest that exists and cannot be
            read.
    """

    if limits is None:
        limits = {}

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

def write_checksums(check_path, abspairs, *, logger=None, limits=None):
    """Write one MD5 manifest, in the order the pairs are given.

    Each record is the digest, two spaces, and the path with the manifest's own prefix
    trimmed off the front, which is what ``read_checksums()`` puts back. The pairs are
    written as they arrive, so the order of the manifest is the order
    ``generate_checksums()`` built.

    A ``.DS_Store`` pair and a dot-underscore pair are logged and left out, so a manifest
    never records one however it got into the list; an invisible file is logged and
    written. The parent directory is created if it is not there.

    Nothing is versioned here. A caller replacing a manifest that matters calls
    ``_shelf_common.move_old()`` first, and the three tasks that replace one do.

    Parameters:
        check_path (str): The manifest to write. A relative path is made absolute.
        abspairs (list): The (absolute path, digest) pairs to record.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over this module's defaults.

    Raises:
        ValueError: raised by ``from_abspath()``, before any log line is written, for a
            path outside every holdings tree.
        OSError: raised by ``makedirs()`` if the checksums tree cannot be created and by
            ``open()`` if the manifest cannot be written. Each is logged through
            ``exception()`` and re-raised, as is anything else the write raises. The file
            is closed on the path where nothing was raised and not otherwise, so a failure
            part way through leaves a truncated manifest whose remaining records are
            flushed whenever the object is collected.
    """

    if limits is None:
        limits = {}

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
            (abspath, md5) = pair

            if abspath.endswith('/.DS_Store'):      # skip .DS_Store files
                logger.ds_store('.DS_Store skipped', abspath)
                continue

            if '/._' in abspath:                    # skip dot-underscore files
                logger.dot_underscore('._* file skipped', abspath)
                continue

            if '/.' in abspath:                     # flag invisible files
                logger.invisible('Invisible file', abspath)

            f.write('%s  %s\n' % (md5, abspath[lskip:]))
            logger.debug('Written', abspath)

        f.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_pairs(pairs1, pairs2, selection=None, *, logger=None,
                   limits=None):
    """Report every way a fresh walk's digests and a manifest's disagree.

    The second list becomes a dictionary and the first is walked against it. A path the
    manifest does not carry is "Missing checksum"; a path both carry with different
    digests is "Checksum mismatch"; a path left in the manifest when the walk has been
    accounted for is "Extra file". Every disagreement is its own error line and the walk
    continues, so one call reports all of them.

    **With a selection, the sweep for extra files is skipped entirely.** That is what
    makes a narrowed run safe: the manifest's other entries are not compared against a
    walk that was never asked about them, and so are not reported as extra.

    **Nothing raised inside this escapes it.** The ``return`` sits in the ``finally``
    clause, so the re-raise above it is discarded and the caller is given the flag as it
    stood, which for a failure part way through a comparison is True unless a mismatch had
    already been seen. A ``KeyboardInterrupt`` is swallowed the same way. It is the reason
    ``B012`` is on this file's ruff ignore list.

    Parameters:
        pairs1 (list): The (absolute path, digest) pairs a fresh walk found.
        pairs2 (list): The pairs the manifest holds.
        selection (str): The basename of the one file to check, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope. This module's defaults for this
            scope are empty and are merged into a value that is then not passed, so what
            reaches the log level is this argument itself.

    Returns:
        bool: True if the two agree on every entry compared, False if any error was
        logged, and True for an exception raised part way through a comparison that had
        so far agreed.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

    merged_limits = VALIDATE_PAIRS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Validating checksums', limits=limits)

    success = True
    try:
        md5_dict = {}
        for (abspath, md5) in pairs2:
            md5_dict[abspath] = md5

        for (abspath, md5) in pairs1:
            if selection and selection != os.path.basename(abspath):
                continue

            if abspath not in md5_dict:
                logger.error('Missing checksum', abspath)
                success = False

            elif md5 != md5_dict[abspath]:
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
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, selection=None, *, logger=None, limits=None):
    """Write one volume's MD5 manifest, refusing to replace one already there.

    A manifest already in place is an error and nothing is walked. **A selection is
    refused by raising rather than by logging**: there is no sense in creating a manifest
    that covers one named file, and the exception is what a run of this task on a
    selection ends with. No other task here refuses a selection at all, and
    ``pdsinfoshelf``'s ``initialize`` refuses one by calling ``error()`` on a logger the
    driver never supplied, so it ends in ``AttributeError`` rather than in a report; only
    the PDS4 info shelf tool logs and returns.

    The driver reaches this on a selection only for the ``initialize`` task itself, since
    it demotes ``reinitialize`` on a selection to ``update``.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of one file. Anything but None raises.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the walk and the write.

    Returns:
        bool: True if a manifest was written, False if one was already there or the walk
        found no files at all.

    Raises:
        ValueError: if a selection is given.
    """

    if limits is None:
        limits = {}

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

def reinitialize(pdsdir, selection=None, *, logger=None, limits=None):
    """Rebuild one volume's MD5 manifest, versioning and replacing what is there.

    Every digest is computed afresh: the walk is given nothing to copy from, so this is
    the task that finds a manifest entry which is right in the manifest and wrong on disk.
    The old manifest is copied into the run's log directories before the new one is
    written.

    A volume with no manifest is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead, since there is nothing to
    preserve around the named file.

    **On a selection this rebuilds only the named file's digest and copies the rest**, by
    reading the existing manifest first and handing it to the walk to copy from. The
    driver does not let a command line reach this path: a selection turns ``reinitialize``
    into ``update``, so what runs here on a selection is a direct call rather than a run.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of the one file to rebuild, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the write.

    Returns:
        bool: True if a manifest was written, and False if there was none to replace and a
        selection was given, if a selection's own read came back empty, or if the walk
        found no files.
    """

    if limits is None:
        limits = {}

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
    _shelf_common.move_old(check_path, _shelf_common.CHECKSUM_FILE, logger=logger)

    new_limits = WRITE_CHECKSUMS_LIMITS.copy()
    new_limits.update(limits)
    write_checksums(check_path, pairs, logger=logger, limits=new_limits)
    return True

def validate(pdsdir, selection=None, *, logger=None, limits=None):
    """Report every way one volume and its MD5 manifest disagree.

    The manifest is read and the tree is walked from scratch, every file being digested,
    and the two are compared. Nothing is written whatever the answer.

    This is also the entry point ``re_validate`` reaches, as a library function rather
    than through the command line, both for a volume type and, with a selection, for one
    archive file of a volume set.

    **A False here does not reach the exit status of a command-line run.** The driver
    records it, ``main()`` uses it only to decide whether to chain a ``pdsinfoshelf`` run,
    and a run that chains nothing exits 0.

    Parameters:
        pdsdir: The volume directory to check.
        selection (str): The basename of the one file to check, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the comparison.

    Returns:
        bool: True if the two agree, and False if there is no manifest, if the read or the
        walk came back empty, or if any disagreement was logged.
    """

    if limits is None:
        limits = {}

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

def repair(pdsdir, selection=None, *, logger=None, limits=None):
    """Rewrite one volume's MD5 manifest if it disagrees, or re-date it if it does not.

    The manifest and a fresh walk are sorted and compared as whole lists, so this reports
    that something differs and not what; ``validate()`` is the task that names the
    disagreements one by one. Where they differ, the old manifest is versioned into the
    run's log directories and a new one is written.

    Where they agree the content is right and only the dates can be wrong, so the manifest
    is compared against the newest file the walk **saw**, which is not the same as the
    newest it digested: the walk takes each file's modification time before any skip test,
    so a ``.DS_Store`` or a backup file touched today dates the volume.

      * If the holdings are newer, the manifest is touched to now and the run reports how
        far behind it was. The report is in days at or above a tenth of a day, which is
        8,640 seconds, and in minutes below that. The time it says it set is read from the
        clock just before the touch rather than from the file afterwards.
      * If the holdings are not newer, the repair is canceled and nothing is touched.
        Equal times take this branch, since the test is strict.

    On a selection the walk is given the existing manifest to copy from and told to digest
    the named file regardless, so only that file's digest is recomputed and the comparison
    then covers the whole manifest.

    A volume with no manifest is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead.

    Parameters:
        pdsdir: The volume directory to repair the manifest of.
        selection (str): The basename of the one file to re-digest, or None for all.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read and the walk. The write of a
            new manifest takes none, so its own defaults apply there.

    Returns:
        bool: True if a manifest was written, initialized, touched or found up to date,
        and False if there was none and a selection was given, if the read came back
        empty, or if the walk found no files.
    """

    if limits is None:
        limits = {}

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
    _shelf_common.move_old(check_path, _shelf_common.CHECKSUM_FILE, logger=logger)
    write_checksums(check_path, dirpairs, logger=logger)
    return True

def update(pdsdir, selection=None, *, logger=None, limits=None):
    """Add the digest of any file the manifest does not already carry.

    The existing manifest is handed to the walk as what is already known, and
    ``regardless`` is off, so every file already recorded keeps the digest it was recorded
    with and only a file the manifest lacks is read. A file whose contents have changed is
    therefore not noticed here; that is ``validate()``'s and ``repair()``'s work, and is
    what the ``--help`` text means by saying checksums of pre-existing files are not
    checked.

    **It does not notice a deletion either.** The walk rebuilds its result from the whole
    of what it was handed, and only then appends what it found, so an entry for a file
    that is no longer there survives; and because it survives, the comparison this task
    makes still holds and the run reports that the manifest is complete. An update
    therefore adds new files and does nothing else. Only ``reinitialize`` or ``repair``
    clears a stale entry.

    Where the walk returns exactly what the manifest held, nothing is written or touched
    and that is reported at info level; the "out of date" re-dating ``repair()`` does has
    no counterpart here.

    A volume with no manifest is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead. That is also the task this one
    stands in for: the driver runs ``reinitialize`` on a selection as ``update``.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of one file. It reaches the walk, where with
            ``regardless`` off it narrows the walk to that file without forcing a
            re-digest, so a file already in the manifest contributes its old digest.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to nothing: every call this makes is
            written without one, so each takes its own defaults.

    Returns:
        bool: True if a manifest was written, initialized, or found already complete, and
        False if there was none and a selection was given, if the read came back empty, or
        if the walk found no files.
    """

    if limits is None:
        limits = {}

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
     _latest_mtime) = generate_checksums(pdsdir, selection, md5pairs,
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
    _shelf_common.move_old(check_path, _shelf_common.CHECKSUM_FILE, logger=logger)
    write_checksums(check_path, dirpairs, logger=logger)
    return True

################################################################################
# Executable program
################################################################################

SPEC = _common.ToolSpec(
    progname='pdschecksums',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds3File,
    unit='volume',
    holdings_sentinel='/holdings/',
    index_ext='.tab',
    file_log_level='info',
    description=_shelf_common.CHECKSUMS_DESCRIPTION,
    task_help=_shelf_common.CHECKSUMS_TASK_HELP,
    positional_help=_shelf_common.CHECKSUMS_POSITIONAL_HELP,
    log_suffix='_md5',
    handler_factories=(pdslogger.error_handler,),
    extra_arguments=(_shelf_common.ARCHIVES_ARGUMENT,
                     _shelf_common.INFOSHELF_ARGUMENT),
    checksum_path_message='No checksums for checksum files: ',
    invalid_dir_message='Invalid directory for checksumming: ',
    invalid_file_message='Invalid file for checksumming: ')

TASKS = {'initialize': initialize,
         'reinitialize': reinitialize,
         'validate': validate,
         'repair': repair,
         'update': update}

def main():
    """Run the tool, and chain a pdsinfoshelf run over the same command line if asked.

    This is the ``pdschecksums`` console script's entry point. The driver returns rather
    than exiting, so what happens next is decided here, and it is decided by two things
    together: the last task has to have returned something true, and ``--infoshelf`` has
    to have been given. Either missing, and this returns and the process exits 0.

    The exit status is the run's own: 0 when the run logged no fatal and no error, and
    1 when it logged either, so a ``--validate`` that reported a mismatch exits 1. Where
    the chain also ran, this run's status wins if it is nonzero and the chained run's is
    used otherwise, so a failure in either half is visible to the caller. Everything
    settled before a task starts keeps its own status: 1 for a command line naming no
    task, 2 for one the parser cannot classify, and 1 for a path outside a holdings tree
    or naming checksum files.

    The chained command line is this one with every occurrence of the string
    "pdschecksums" replaced by "pdsinfoshelf" and the ``--infoshelf`` flag dropped, run as
    a subprocess. It is a text substitution over the whole of ``sys.argv``, so it rewrites
    the program name and would rewrite any argument carrying that text; every path under a
    holdings tree that carries it would be rewritten too.

    Raises:
        SystemExit: from ``sys.exit()`` on every path out of a run, with the run's own
            status, or with the chained run's return code where this run's status is 0
            and the chain ran; from ``setup_run()`` with 1 for a missing task, 0 for
            --help and 2 for a command line the parser cannot classify; and from the two
            path helpers with 1 for a path they reject.
    """

    result = _shelf_common.run_selection_main(SPEC, TASKS, sys.argv)

    # If everything went well, execute pdsinfoshelf too. Only argv[0] names the program, so
    # only argv[0] is rewritten: substituting throughout would rewrite a --log directory
    # or any holdings path that happens to carry this program's name.
    if result.proceed and result.args.infoshelf:
        new_list = [a for a in sys.argv if a not in ('--infoshelf', '-i')]
        new_list[0] = new_list[0].replace('pdschecksums', 'pdsinfoshelf')
        completed = subprocess.run(new_list, check=False)
        sys.exit(result.status or completed.returncode)

    sys.exit(result.status)


if __name__ == '__main__':
    main()
