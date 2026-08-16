#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdsinfoshelf.py
################################################################################

"""pdsinfoshelf: shelve the size, date, digest and preview shape of a PDS3 volume's files.

An info shelf answers, for one volume, the five questions PdsFile is asked about a file
often enough that reading them off the filesystem each time is too slow: how many bytes it
holds, how many children a directory has, when it was last modified, what its MD5 digest
is, and, for a preview image, how many pixels across and down it is. It is a pickled
dictionary in the ``_infoshelf-<category>/`` tree, written beside a readable ``.py`` file
of the same mapping.

**This tool reads the checksum file rather than computing digests**, so every entry it
writes is only as current as ``pdschecksums`` left it. The dependency is hard, not
advisory: a volume with no checksum file gets a "Missing entry in checksum file" error for
every file it holds and then ends in ``FileNotFoundError``, because the walk dates the
volume partly by the checksum file's own modification time. It runs the other way too:
``pdschecksums --infoshelf`` chains a run of this tool after a successful one of its own.

The driver is ``_shelf_common.run_selection_main()``, which this tool reaches because a
command-line path here can name **one file inside a volume** as well as a whole volume or
volume set. Every task therefore takes a ``selection``, which is a basename and not a
path, and a task given one narrows its work to the file of that name while leaving every
other entry in the shelf as it was. The driver enforces the one case where that is not
safe by itself: ``reinitialize`` on a selection is run as ``update`` instead.

Beyond the driver and the path resolution, what this tool shares with the rest is small
and specific: ``_shelf_common.move_old()`` versions the shelf a task is about to replace
into the run's log directories, ``INFO_SHELF`` is the record that says how and names the
``.py`` sidecar as the file that travels with it, and ``_shelf_common.modtimes_agree()``
is the comparison a validation makes on the third field. Everything else here is this
module's, and is a near-copy of the PDS4 tool's; the differences between the two are
recorded on the functions that carry them.

**Every modification time is formatted in the local time zone**, so the same volume
shelved under two settings of ``TZ`` produces two different shelves. The times are then
compared as strings, which works because the format sorts the same way the times do.

Two fields of the specification are set here and read nowhere a run of this tool reaches.
``index_ext`` is read only by the index shelf tools' target expansion. And
``file_log_level`` is set to 'info' and reaches nothing: its four readers are all in the
archive and link shelf machinery, and the per-file lines below name their level directly.
``log_path_method`` is a third field this driver never consults, and it is not set here at
all: it stays at its empty default, because the driver picks between the volume and the
volume set log path per target instead.
"""

import datetime
import os
import pickle
import re
import sys

import pdslogger
from PIL import Image

import pdsfile
from pdsfile.holdings_maintenance import _common, _shelf_common
from pdsfile.holdings_maintenance.pds3 import pdschecksums

LOGNAME = _shelf_common.INFOSHELF_LOGNAME

PREVIEW_EXTS = {'.jpg', '.png', '.gif', '.tif', '.tiff',
                '.jpeg', '.jpeg_small'}

# Default limits
GENERATE_INFODICT_LIMITS = {}
LOAD_INFODICT_LIMITS = {}
WRITE_INFODICT_LIMITS = {}

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################

def generate_infodict(pdsdir, selection, old_infodict={}, *, logger=None,
                     limits=None):
    """Return what is known about every file in one volume, and the newest date seen.

    The tree is descended recursively from the volume directory, or from the one named
    file when a selection is given, and each path visited gets a five-element entry:
    byte count, child count, modification time, MD5 digest, and preview size.

    **A directory's entry is the sum of what is under it.** Its byte count is the total of
    its children's, its child count is how many entries it kept, and its modification time
    is the greatest of its children's rather than the directory's own. Its digest is empty
    and its preview size is (0, 0), and an empty directory carries an empty modification
    time, which is the sentinel ``_shelf_common.modtimes_agree()`` treats as comparable
    only with itself.

    The digests are not computed here. The volume's checksum file is read once, through
    ``pdschecksums.checksum_dict()``, and a file it does not carry is reported as a
    missing checksum entry and shelved with an empty digest.

    ``old_infodict`` is what makes an update affordable: a **file** already keyed in it
    keeps its entry and is not measured again. **A directory's entry always comes from
    this walk**, because it is an aggregate of the children the walk found and the old
    one is stale as soon as anything below it changes. **An entry for a path the walk did
    not visit is reported and dropped**, so a file deleted from the tree leaves the shelf
    too. **On a selection the merge is narrower**: only the named file's own entry is
    written over the old dictionary, and nothing is dropped.

    The newest date is taken over the entries merged in, and then compared against the
    checksum file's own modification time, the later of the two winning. That is what lets
    ``repair()`` notice that the checksums have been rebuilt since the shelf was written.
    An empty result reports "No files found" and dates the volume by the checksum file
    alone.

    Parameters:
        pdsdir: The volume directory to walk. Its abspath is the root of the walk and its
            ``root_`` is what the logger reports paths relative to.
        selection (str): The basename of the one file to descend into, or None for the
            whole volume. It is joined to the volume directory, so it names a top-level
            file of the volume and not a file deeper inside it.
        old_infodict (dict): What the shelf already holds, keyed by absolute path.
            **A mutable default** of ``{}``, **which nothing here writes to.**
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over this module's defaults.

    Returns:
        tuple: the entries keyed by absolute path, and the newest modification time as the
        same formatted string the entries carry.

    Raises:
        ValueError: raised by ``checksum_path_and_lskip()`` for a volume that has no name
            or that already names checksum files.
        OSError: raised by ``getsize()`` or ``getmtime()`` on a file the listing named and
            that is gone by the time it is measured, by ``listdir()`` on a directory that
            cannot be read, and by ``getmtime()`` on a checksum file that is not there.
            Each is logged through ``exception()`` and re-raised, as is anything else the
            walk raises.
    """

    if limits is None:
        limits = {}

    ### Internal function

    # The keys this walk computed as directories, which are the entries the merge
    # below has to take from the walk rather than from the old dictionary.
    dirkeys = set()

    def get_info_for_file(abspath):
        """Return the five-element entry for one file.

        The digest comes from the enclosing call's checksum dictionary and the logger from
        its logger; neither is passed in, and both are read at call time rather than at
        definition time, which is what lets this be defined above the line that loads the
        checksums.

        A preview size is measured only for a file whose extension is in ``PREVIEW_EXTS``,
        and any failure to read one -- a file that is not an image, a truncated one, a
        format the library cannot open -- is caught, reported as "Preview size not found",
        and shelved as (0, 0). The close is the last statement of the guarded block rather
        than a context manager's, so it is reached only where nothing was raised; the PDS4
        tool opens the image as a context manager instead. Only one statement sits between
        the open and the close, an attribute read, and no input was found that raises
        there, so the difference is one of shape rather than one observed.

        The modification time is formatted in the local time zone, to microseconds.

        Parameters:
            abspath (str): The file to measure.

        Returns:
            tuple: byte count, child count of zero, modification time, MD5 digest or the
            empty string, and preview size or (0, 0).

        Raises:
            OSError: raised by ``getsize()`` or ``getmtime()`` if the file is gone or
                cannot be read. The preview measurement below them is guarded and this is
                not.
        """

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
        """Return the entry for one path, filling in everything below it on the way.

        A directory is descended into and its entry derived from its children's; a file is
        taken from ``old_infodict`` if it is there and measured otherwise. Every path
        visited, directory or file, is written into ``infodict``, so one call at the top
        of a volume fills the whole dictionary and the value it returns is only the
        root's.

        Three kinds of entry are left out of a directory's listing and out of the result:
        a ``.DS_Store``, a dot-underscore file and a backup file. An invisible file is
        logged and kept, and counts toward the directory's child count. The three tests
        apply to directory names as well as to file names, since one listing covers both.

        Parameters:
            abspath (str): The path to describe.
            infodict (dict): The dictionary every path visited is written into. Modified.
            old_infodict (dict): What the shelf already holds. A file found here is taken
                as it stands; a directory is recomputed whether or not it is here.
            checkdict (dict): Accepted and passed down, and read by nothing. The digest
                lookup below reads the enclosing call's dictionary from its closure, which
                is the same object, so the argument is inert rather than wrong.

        Returns:
            tuple: this path's five-element entry.

        Raises:
            OSError: raised by ``isdir()`` or ``listdir()`` on a directory that cannot be
                read, and by the measurement of a file below it.
        """

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

                if '/.' in absfile:             # flag invisible files
                    logger.invisible('Invisible file', absfile)

                info = get_info(absfile, infodict, old_infodict, checkdict)
                nbytes += info[0]
                children += 1
                modtime = max(modtime, info[2])

            info = (nbytes, children, modtime, '', (0,0))
            dirkeys.add(abspath)

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
            # An entry for a path the walk did not visit is a deletion: report it and
            # leave it out, so the shelf and the tree agree about what is there.
            for key in set(merged) - set(infodict):
                logger.info('Removed entry for missing file', key, force=True)
                del merged[key]

            for (key, _value) in infodict.items():
                # A file already shelved keeps its entry, which is what makes an
                # update affordable. A directory's entry is an aggregate of what is
                # under it, so this walk's is the current one and the old is stale.
                if key not in merged or key in dirkeys:
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

def load_infodict(pdsdir, *, logger=None, limits=None):
    """Return one volume's shelved entries, with every stored path made absolute again.

    The shelf stores each key as the path below the volume, so reading it is the inverse
    of what ``write_infodict()`` does: the volume's own prefix is put back in front of
    each. The empty key is the volume directory itself and is restored as such. An archive
    target is the exception at both ends, since one shelf there covers a whole volume set
    and its keys are the paths below that.

    **A digest of dashes is read back as no digest.** Any value whose first character is a
    dash is replaced with the empty string, which is what a directory's entry carries.
    Nothing in this package writes a dashed digest -- ``write_infodict()`` stores the
    empty string for a directory, and a scan of every info shelf in the PDS3 test
    holdings, 6,723 files and 21,711,938 entries, found no dashed digest and 186,305 empty
    ones -- so this is a defensive read of some other producer's output rather than a
    description of the format written here.

    The pickle is read straight from disk rather than through the PdsFile shelf cache, so
    what comes back is what the file holds now.

    Parameters:
        pdsdir: The volume directory whose shelf is to be read. Its ``root_`` is what the
            logger reports paths relative to.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over this module's defaults.

    Returns:
        dict: the five-element entry of each path, keyed by absolute path, and empty if
        there is no shelf file.

    Raises:
        ValueError: raised by ``shelf_path_and_lskip()`` for a checksum path, for an
            archive path with no volume set, and for anything else no volume name can be
            found for.
        OSError: raised by ``open()`` for a shelf that exists and cannot be read.
        pickle.UnpicklingError: raised by ``load()`` for a file that is not a pickle, and
            for most truncations of one: truncating a real shelf at 2,001 sampled prefixes
            gave this 1,758 times and ``EOFError`` 243. It is not an OSError, so a caller
            guarding only against the entry above catches neither. Each is logged through
            ``exception()`` and re-raised, as is anything else the read raises.
    """

    if limits is None:
        limits = {}

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

def write_infodict(pdsdir, infodict, *, logger=None, limits=None):
    """Write a new info shelf for one volume, and its Python sidecar.

    Two files are written under two log levels: the pickle at the volume's info shelf
    path, keyed by the path below the volume rather than by absolute path, and a
    readable ``.py`` beside it holding the same mapping as Python source. The parent
    directory is created if it is not there.

    **The sidecar is not only for a person to read.** ``_shelves.shelf_lookup()`` answers
    a question about the volume itself by reading the sidecar's **second line** rather
    than unpickling the whole shelf. Two properties of the write below are load-bearing
    for that: the entries are sorted by absolute path, and where the dictionary covers a
    whole volume the volume directory's own path is a prefix of every other, so its entry
    -- the one keyed by the empty string -- is written first and is the file's second
    line.

    **That holds of the dictionary a full walk produces and not of every dictionary this
    is given.** ``reinitialize()`` on a selection hands it one entry, for the named file
    alone, and the pair it then writes has no empty key at all; ``shelf_lookup()`` reads
    that file's second line regardless and returns the named file's entry as though it
    were the volume's, because nothing on that path checks which key it got. The sidecar
    is also what the versioning record names as the file travelling with the pickle.

    In the sidecar the keys are padded to a common width and the entries are written in
    sorted key order, which the pickle is not: the pickle is written in the order the
    dictionary was built. The dictionary is named for the **first two underscore-separated
    parts** of the file's basename with "_info" appended. Every path this builds ends in
    "_info.py", so there are always at least two such parts and the name a shelf gets is
    its first two; a basename with more than two loses the rest, which is what makes the
    name in the sidecar differ from the file it is in. The sidecar is written as latin-1.

    Neither file is versioned here; a caller that wants the old pair kept calls
    ``_shelf_common.move_old()`` first, and the three tasks that replace a shelf do.

    Parameters:
        pdsdir: The volume directory the shelf covers. Its ``root_`` is what the logger
            reports paths relative to.
        infodict (dict): The entries, keyed by absolute path, as generate_infodict() built
            them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for the first of the two scopes, merged over this
            module's defaults. The sidecar's scope is opened with this argument as it
            stands, so this module's defaults do not apply there.

    Raises:
        ValueError: raised by ``shelf_path_and_lskip()`` for a checksum path, for an
            archive path with no volume set, and for anything else no volume name can be
            found for.
        OSError: raised by ``makedirs()`` if the shelf tree cannot be created and by
            ``open()`` if either file cannot be written. Each is logged through
            ``exception()`` and re-raised, as is anything else either write raises. **The
            pickle is written first and is not removed if the sidecar then fails**, so
            such a call leaves a pickle with no sidecar or with an older one. Reading the
            shelf still works, and so do ``validate()`` and an ``update()`` with nothing
            to write; what fails on the sidecar rather than on the shelf is the repair
            task, the versioning any task that does write performs, and the shortcut
            ``_shelves.shelf_lookup()`` takes for a question about the volume itself.
    """

    if limits is None:
        limits = {}

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
        for (abspath, _values) in infodict.items():
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
                      limits=None):
    """Report every way one volume's entries and its shelf's disagree.

    A key both dictionaries carry is compared field by field, and each of the five fields
    that differs is its own error line, so one path can produce five. The third is
    compared through ``_shelf_common.modtimes_agree()``, which forgives a sub-second
    difference and nothing more, and the message prints each time cut back to the second
    while the comparison used the whole of it.

    **Both dictionaries are emptied as it goes**: a key present in both is compared and
    then deleted from both, so what is left in each at the end is what the other lacks,
    and that is what the last two loops report. A caller that still needs either
    dictionary afterwards has to pass a copy.

    **With a selection, the shelf dictionary is pruned before anything is compared**, down
    to the one key naming that file, and that pruning happens outside the guarded block.
    So a narrowed validation reports nothing about the volume's other files rather than
    reporting them all as missing.

    Parameters:
        pdsdir: The volume the entries are about. Only its ``root_`` and its abspath are
            read, for the logger's root and the log line.
        dirdict (dict): The entries a fresh walk found. Emptied.
        shelfdict (dict): The entries the shelf holds. Pruned to the selection where there
            is one, then emptied.
        selection (str): The basename of the one file to check, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, passed as they stand; this module's
            defaults do not apply here.

    Returns:
        tuple: what closing this scope's log level reported. Anything raised inside is
        logged and re-raised: the level is closed in the ``finally`` and the return sits
        after it, so a comparison that failed part way through does not come back as a
        result.
    """

    if limits is None:
        limits = {}

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

                agreement = True
                if bytes1 != bytes2:
                    logger.error('File size mismatch %d %d' %
                                    (bytes1, bytes2), key)
                    agreement = False

                if count1 != count2:
                    logger.error('Child count mismatch %d %d' %
                                    (count1, count2), key)
                    agreement = False

                if not _shelf_common.modtimes_agree(modtime1, modtime2):
                    # Reported to the second, though compared in full
                    logger.error('Modification time mismatch "%s" "%s"' %
                        (modtime1.rpartition('.')[0],
                         modtime2.rpartition('.')[0]), key)
                    agreement = False

                if checksum1 != checksum2:
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
        results = logger.close()

    return results

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, selection=None, logger=None, limits=None):
    """Write one volume's info shelf, refusing to replace one already there.

    A shelf already in place is an error and nothing is walked. A selection is refused
    too, since there is no sense in creating a shelf that covers one named file. Both
    refusals are log lines: the logger is resolved before either test, so neither path
    depends on the caller having supplied one, and the driver supplies none.

    Nothing is returned. The driver records the return value as the run's ``proceed``, and
    for all five of this tool's tasks that value is None.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of one file. Anything but None ends the task.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the walk and the write.
    """

    if limits is None:
        limits = {}

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

    info_path = pdsdir.shelf_path_and_lskip('info')[0]

    # Make sure file does not exist
    if os.path.exists(info_path):
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

def reinitialize(pdsdir, selection=None, logger=None, limits=None):
    """Rebuild one volume's info shelf, versioning and replacing what is there.

    The walk is given nothing to copy from, so every file is measured again and its digest
    re-read from the checksum file. The old shelf and its sidecar are copied into the
    run's log directories before the new pair is written.

    A volume with no shelf is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead.

    **On a selection this shelves only the named file.** The walk is rooted at that file
    rather than at the volume, and nothing is read from the existing shelf, so the pair
    that gets written covers one file and the volume's other entries are lost. The driver
    does not let a command line reach that: a selection turns ``reinitialize`` into
    ``update``, and this path is reachable only by a direct call.

    Nothing is returned.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of the one file to shelve, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the walk and the write.
    """

    if limits is None:
        limits = {}

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
        _shelf_common.move_old(info_path, _shelf_common.INFO_SHELF, logger=logger)

    # Save info file
    write_infodict(pdsdir, infodict, logger=logger, limits=limits)

def validate(pdsdir, selection=None, logger=None, limits=None):
    """Report every way one volume and its info shelf disagree.

    The shelf is read whole, the tree is walked from scratch, and the two are compared.
    Nothing is written whatever the answer.

    This is also the entry point ``re_validate`` reaches, as a library function rather
    than through the command line, both for a volume type and, with a selection, for one
    archive file of a volume set.

    A missing shelf is an error and stops the task before anything is walked. A missing
    checksum file stops it differently and later: the walk reports a missing checksum
    entry for every file in the volume and then ends in ``FileNotFoundError``, so the
    comparison is never made.

    Nothing is returned, and neither the comparison's result nor its error count reaches
    the caller; what a run reports is its log and its exit status.

    Parameters:
        pdsdir: The volume directory to check.
        selection (str): The basename of the one file to check, or None for all of them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the comparison.
    """

    if limits is None:
        limits = {}

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

def repair(pdsdir, selection=None, logger=None, limits=None):
    """Rewrite one volume's info shelf if it disagrees, or re-date it if it does not.

    The shelf and a fresh walk are compared as whole dictionaries, so this reports that
    something differs and not what; ``validate()`` is the task that names the
    disagreements one by one. Where they differ, the old pair is versioned into the run's
    log directories and a new pair is written.

    Where they agree the content is right and only the dates can be wrong, so the pair is
    compared against the newest date the walk produced, which is the greatest entry date
    or the checksum file's own, whichever is later.

      * The pair's age is the **older** of the pickle's and the sidecar's modification
        times, so a pair with one stale half is treated as stale.
      * If the holdings are newer, both files are touched to now and the run reports how
        far behind they were. The report is in days at or above a tenth of a day, which is
        8,640 seconds, and in minutes below that.
      * If the holdings are not newer, the repair is canceled and nothing is touched.
        Equal times take this branch, since the test is strict.

    **On a selection the comparison is made against a copy of the shelf with the one
    entry replaced**, so what is written when they differ is the whole shelf with that
    file's entry brought up to date.

    A volume with no shelf is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead.

    Nothing is returned.

    Parameters:
        pdsdir: The volume directory to repair the shelf of.
        selection (str): The basename of the one file to re-measure, or None for all.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the write.

    Raises:
        OSError: raised by the two ``getmtime()`` calls that date the pair, and
            ``FileNotFoundError`` in particular where the shelf pickle is present and its
            ``.py`` sidecar is not. **A missing sidecar stops this task on either branch,
            from two different places.** The two ``getmtime()`` calls are inside the
            agreement branch; where the shelf and the walk differ, the versioning that
            comes next raises the same exception out of ``move_old()``, which copies the
            sidecar beside the pickle.
    """

    if limits is None:
        limits = {}

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
    _shelf_common.move_old(info_path, _shelf_common.INFO_SHELF, logger=logger)
    write_infodict(pdsdir, dir_infodict, logger=logger, limits=limits)

def update(pdsdir, selection=None, logger=None, limits=None):
    """Add the entry of any file the info shelf does not already carry.

    The existing shelf is handed to the walk as what is already known, so every **file**
    already shelved keeps the entry it was shelved with and only a file the shelf lacks is
    measured. A file whose size or date has changed is therefore not noticed here; that is
    ``validate()``'s and ``repair()``'s work.

    **A directory already shelved is not refreshed either.** The walk does recompute one
    from the children it found, and the merge then writes a key only where the shelf lacks
    it, so the recomputed value is discarded and every ancestor directory of a new file
    keeps the child count, the byte total and the modification time it was shelved with.
    ``validate()`` reports all three as mismatches, so the two tasks disagree about the
    same shelf until a ``reinitialize`` or a ``repair``.

    **A deletion is invisible.** The result starts from the whole of what the shelf held,
    so an entry for a file that is no longer there survives; and because it survives, and
    because a directory's entry is not refreshed either, the comparison this task makes
    still holds and the run reports that the shelf is complete.

    Where the walk returns exactly what the shelf held, nothing is written or touched and
    that is reported at info level; the "out of date" re-dating ``repair()`` does has no
    counterpart here.

    A volume with no shelf is a warning and is handed to ``initialize()``, unless a
    selection was given, which makes it an error instead. That is also the task this one
    stands in for: the driver runs ``reinitialize`` on a selection as ``update``.

    Nothing is returned.

    Parameters:
        pdsdir: The volume directory to walk.
        selection (str): The basename of one file, which roots the walk at that file and
            narrows the merge to its one entry, or None for the whole volume.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the walk and the write.
    """

    if limits is None:
        limits = {}

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
    _shelf_common.move_old(info_path, _shelf_common.INFO_SHELF, logger=logger)
    write_infodict(pdsdir, dir_infodict, logger=logger, limits=limits)

################################################################################
################################################################################

SPEC = _common.ToolSpec(
    progname='pdsinfoshelf',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds3File,
    unit='volume',
    holdings_sentinel='/holdings/',
    index_ext='.tab',
    file_log_level='info',
    description=_shelf_common.INFOSHELF_DESCRIPTION,
    task_help=_shelf_common.INFOSHELF_TASK_HELP,
    positional_help=_shelf_common.INFOSHELF_POSITIONAL_HELP,
    log_suffix='_info',
    handler_factories=(pdslogger.error_handler,),
    extra_arguments=(_shelf_common.ARCHIVES_ARGUMENT,),
    checksum_path_message='No infoshelves for checksum files: ',
    invalid_dir_message='Invalid directory for an infoshelf: ',
    invalid_file_message='Invalid file for an infoshelf: ')

TASKS = {'initialize': initialize,
         'reinitialize': reinitialize,
         'validate': validate,
         'repair': repair,
         'update': update}

def main():
    """Run the tool and exit with the status the run computed.

    This is the ``pdsinfoshelf`` console script's entry point. The driver returns rather
    than exiting, and this is the whole of what is done with what it returned: the status
    is 1 if the run logged a fatal or an error and 0 otherwise. The other two fields of
    the result are not read, and one of them could not be useful here in any case, since
    all five of this tool's tasks return None.

    That makes this the half of the pair that does report what a task found. The two
    checksum tools share this driver and never read the status it computed, so what they
    exit nonzero for is only what was settled before a task started.

    Raises:
        SystemExit: from ``sys.exit()``, with the run's status, on every path out of a run
            that is not an exception.
    """

    result = _shelf_common.run_selection_main(SPEC, TASKS, sys.argv)
    sys.exit(result.status)

if __name__ == '__main__':
    main()
