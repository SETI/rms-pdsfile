##########################################################################################
# pdsfile/holdings_maintenance/_archives_common.py
##########################################################################################

"""What the two archive tools share.

The generic driver the tools of every family run on is in ``_common.py``; this is the
part only pdsarchives and pds4archives use. Both run on ``_common.run_main()``.

An archive tool packs one unit directory tree into a ``.tar.gz`` file under the parallel
``archives-<category>/`` tree, and validates the two against each other. The comparison
is by metadata alone: a file matches its archived member when the interior path, the
byte count and the modification time agree. **Contents are never compared**, which is
what makes validating a whole volume set affordable and is what the ``--help`` text
says.

Three pieces are here because both flavors need them and neither differs on them: the
walk that inventories a directory tree, the tarfile member filter that decides what goes
into an archive and under what identity, and the comparison of the two inventories.
Both sides of that comparison are lists of ``(abspath, interior path, nbytes, modtime)``
tuples: ``load_directory_info()`` builds one from the filesystem, and each tool builds
the other from its ``.tar.gz`` file. The tuples' second element is named ``dirpath``
throughout, and it is an interior path rather than a directory.

The rest of the module is the constants the two tools share: the default message limits
of each scope, and the ``--help`` text, whose ``{unit}`` and ``{units}`` fields
``_common.build_arg_parser()`` fills in.
"""

import os
import sys

import pdslogger

from pdsfile.holdings_maintenance._common import BACKUP_FILENAME


def reject_checksum_and_archive_paths(pdsf, path):
    """Exit when a command-line path names checksum files or archive files.

    An archive tool writes into the archives tree, so a path already inside it, or
    inside the checksums tree, names files this tool does not archive. Either is
    rejected outright rather than skipped, so a command line that mixes such a path in
    with valid ones does nothing at all.

    A path that names neither returns None and the caller carries on.

    Parameters:
        pdsf: The PdsFile the path resolved to.
        path (str): The absolute path the command line resolved to, for the message.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 in either case.
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
    """Return what one directory tree holds, as the tuples an archive is compared to.

    The walk is recursive and covers files and directories alike. A directory
    contributes a tuple with a byte count and a modification time of zero, so the two
    fields that the comparison examines are neutral for it and only its presence is
    checked. The first tuple returned is the tree's own root, on the same terms.

    Three kinds of file are left out of the result, each logged under its own level so
    that a message limit can be set on it: ``.DS_Store`` files, dot-underscore files,
    and backup files, which are those matching ``BACKUP_FILENAME`` or carrying " copy"
    anywhere in the basename. A backup file is logged as an **error**, not merely
    skipped, so finding one gives the whole run a nonzero exit status. Dot-underscore
    directories are skipped as well, but the walk still descends into them, because
    pruning happens through the directory list ``os.walk()`` is given and this loop does
    not modify it.

    An invisible file or directory -- one with a dot component anywhere in its absolute
    path -- is logged and then kept, so invisibles are inventoried here whatever the
    archive writer later does with them.

    Parameters:
        spec (ToolSpec): The tool's specification. Its lskip_for computes the trim, its
            file_log_level names the method the per-file lines go through, and its
            logname is the fallback logger's name.
        pdsdir: The unit directory to walk. Its abspath is the root of the walk and its
            ``root_`` is what the logger reports paths relative to.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Returns:
        list: (abspath, interior path, nbytes, modtime) tuples, the root first and the
        rest in walk order. The interior path of each is its absolute path with the
        leading characters the spec's lskip_for counts removed.

    Raises:
        OSError: from ``getsize()`` or ``getmtime()`` on a file the walk listed and that
            is no longer readable when it is measured. It is logged through
            ``exception()`` and re-raised, as is anything else the walk raises.
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

    The filter is a closure over all three arguments, so one call to this makes a filter
    for one archive being written, and the logger it reports to is fixed at that point.
    ``tarfile`` calls it once per member as the tree is added.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its file_log_level is read,
            naming the method each archived file is reported through.
        logger: The logger the filter reports to.
        archive_invisibles (bool): True to archive invisible files, False to skip them.

    Returns:
        collections.abc.Callable: A tarfile filter, returning the member to archive it
        and None to skip it.
    """

    file_log = getattr(logger, spec.file_log_level)

    def archive_filter(member):
        """Decide whether one member is archived, and under whose ownership.

        The ownership fields are rewritten to root before anything else, so every
        archive this package writes is reproducible on that count and independent of
        who ran the tool. That happens even for a member this then rejects, which
        costs nothing because a rejected member is not written.

        Three kinds of member are dropped: a ``.DS_Store``, recognized by basename; a
        dot-underscore file, recognized by basename or by any path component; and,
        when the enclosing call asked for it, an invisible file, which is one whose
        basename or any path component begins with a dot. The dot-underscore test runs
        first, so a ``._x`` is reported as a dot-underscore rather than as an
        invisible.

        Parameters:
            member (tarfile.TarInfo): The member ``tarfile`` is about to add. Its
                ownership fields are overwritten in place.

        Returns:
            tarfile.TarInfo: The member, to archive it, or None to skip it.
        """

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
    """Report every way a directory tree and its archive disagree.

    The two lists are matched on absolute path. A path in the directory list and not in
    the archive is "Missing from tar file"; a path left over in the archive when every
    directory entry has been accounted for is "Missing from directory". Where both hold
    the path, the byte count and the modification time are compared and each mismatch
    is its own error line.

    **The modification times are allowed to differ by a full second.** The two operands
    are not comparable to better than that: one is a filesystem timestamp and the other
    is a whole-second time recovered from the tarfile. The test rejects a difference
    strictly greater than one second, so exactly one second passes.

    **The interior path is part of neither comparison.** It is carried in the tuple and
    is what the "Validated" line reports, but two entries that agree on absolute path,
    byte count and modification time are accepted whatever their interior paths are.
    That case cannot arise from the tools as they stand, since each list derives its
    interior path from its own absolute path by a fixed rule.

    Every mismatch is logged and the walk continues, so one call reports all of them
    rather than the first.

    Parameters:
        spec (ToolSpec): The tool's specification. Its file_log_level names the method
            each matching file is reported through, and its logname is the fallback
            logger's name.
        dir_tuples (list): What the directory tree holds, as load_directory_info()
            returns it.
        tar_tuples (list): What the archive holds, in the same form.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Returns:
        bool: True if the two agree on every entry, False if any error was logged.
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
