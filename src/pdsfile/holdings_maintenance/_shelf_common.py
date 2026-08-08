##########################################################################################
# pdsfile/holdings_maintenance/_shelf_common.py
##########################################################################################

"""What the checksum, info shelf and link shelf tools share.

The generic driver the tools of every family run on is in ``_common.py``. What one of
those families shares with nobody else lives beside this, in ``_indexshelf_common.py``
and ``_linkshelf_common.py``.

Six of the ten tools reach something here, and not the same something:

  * The two checksum tools and the two info shelf tools run on
    ``run_selection_main()``, the driver at the end of this module, and take their
    ``--help`` text, their ``--archives`` option and their path resolution from here.
  * Those four and the two link shelf tools version a superseded file through
    ``move_old()``, each naming the ``VersionedFile`` record that describes what it is
    replacing.
  * The two info shelf tools compare modification times through ``modtimes_agree()``,
    and the two checksum tools compute digests through ``hashfile()``.
  * The two link shelf tools also take ``LINKSHELF_LOGNAME`` and, as their spec's
    log path method, ``UNIT_LOG_PATH_METHOD``.

The archive tools and the index shelf tools use nothing here.

**What makes these tools need their own driver is the shape of their target.** A
command-line path can name one file inside a unit -- one archive file of a unit set, or
one top-level file of a unit -- so a path expands to (unit, selection) pairs rather than
to units, and each task function takes both. That is also why ``reinitialize`` on a
selection is quietly demoted to ``update``: reinitializing a whole checksum file to
cover one named file would erase every other entry in it.
"""

import argparse
import datetime
import glob
import hashlib
import os
import shutil
import sys
from dataclasses import dataclass

import pdslogger

from pdsfile.holdings_maintenance import _common

# The PdsLogger name each tool kind logs under. Both flavors of a kind share one.
CHECKSUMS_LOGNAME = 'pds.validation.checksums'
INFOSHELF_LOGNAME = 'pds.validation.fileinfo'
LINKSHELF_LOGNAME = 'pds.validation.links'


# The two log-path methods one of these tools picks between for each target: a
# target that names a unit logs under that unit, one that names only a unit set logs
# under the set. Both are defined on the shared PdsFile base, so the same pair of
# names serves the PDS3 and the PDS4 tools; Pds3File's log_path_for_volume and
# log_path_for_volset are aliases of these two.
UNIT_LOG_PATH_METHOD = 'log_path_for_bundle'
UNITSET_LOG_PATH_METHOD = 'log_path_for_bundleset'

# How far apart two modification times may be and still count as the same time.
# Seconds, exclusive: a difference of one second is a difference. Both times here
# come from the same generator at microsecond precision, so the only discrepancy to
# forgive is a sub-second one; on a filesystem that stores whole seconds, one second
# is the smallest change there is rather than an edge case, and reporting it is the
# point. validate_tuples() compares a tarfile's whole-second time against a
# filesystem time and so allows a full second inclusively; that difference between
# the two is deliberate, and follows from what each pair of operands is.
MODTIME_TOLERANCE = 1


def modtimes_agree(modtime1, modtime2, tolerance=MODTIME_TOLERANCE):
    """Return whether two modification times are the same time.

    The two are strings as generate_infodict() builds them,
    '%Y-%m-%d %H:%M:%S.%f'. They agree when they are less than the tolerance apart,
    which makes the comparison symmetric and monotone in the real difference between
    them: two times a millisecond apart agree wherever they fall, and two times a
    second or more apart never do.

    An empty string is the sentinel for a directory with nothing in it, and no
    sentinel parses as a time. Anything the two cannot be compared as times --
    a sentinel, a value that is not a time at all, or a pair that cannot be
    subtracted because only one of them carries a time zone -- falls back to
    comparing the two strings, so two sentinels agree and a sentinel never agrees
    with a real time.

    Parameters:
        modtime1: One modification time.
        modtime2: The other.
        tolerance: How many seconds apart they must stay within, exclusive.
            Default MODTIME_TOLERANCE.

    Returns:
        bool: True if they are the same time.
    """

    try:
        time1 = datetime.datetime.fromisoformat(modtime1)
        time2 = datetime.datetime.fromisoformat(modtime2)
        difference = abs((time1 - time2).total_seconds())
    except (TypeError, ValueError):
        return modtime1 == modtime2

    return difference < tolerance


@dataclass(kw_only=True)
class VersionedFile:
    """What move_old() needs to know about one kind of file it versions.

    Three instances exist and they are the whole set: CHECKSUM_FILE, INFO_SHELF and
    LINK_SHELF, each named by the tools that replace that kind of file. Nothing
    constructs one anywhere else.

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


def next_version_dest(log_dir, prefix, ext):
    """Return the unused <prefix>_v###<ext> path in one log directory.

    ### is one past the highest version already there, and 001 when there is none.

    The versions already there are found by globbing, and the three ``?`` of the pattern
    match any three characters rather than three digits, so a file whose name follows
    the shape but not the numbering is read as a version and fails the conversion. The
    highest is read as three characters at a fixed offset from the end, which is why the
    extension has to be the one the file actually carries.

    Nothing prevents the result from existing: the number is one past the highest of
    what the glob matched, and above 999 the name grows a fourth digit that the same
    glob no longer matches, so a directory holding 999 versions is handed the same
    ``_v1000`` path every time.

    Parameters:
        log_dir (str): The directory the versioned copy goes in.
        prefix (str): The superseded file's basename without its extension.
        ext (str): That extension, including the dot. An empty string makes the version
            slice empty, which fails the conversion below.

    Returns:
        str: The path to copy to.

    Raises:
        ValueError: from the ``int()`` conversion, on any path the glob matched whose
            three characters before the extension are not a number. An extension of ''
            makes that slice empty, so the first match fails; where the glob matches
            nothing, no conversion is attempted and '' is as good as any extension.
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

    The destinations are every directory in ``_common.LOGDIRS``, which the driver
    refills for each target it is about to work on. A process that never reached a
    driver, or that is between targets, leaves that list empty and this then versions
    nothing and logs nothing, however real the file is.

    The two log lines are not symmetric: "moved from" is written once for the whole
    call and "moved to" once per destination, so one line names the original and one
    names each copy. Both are forced past any message limit, because a change to the
    filesystem should not be the thing a cap drops.

    Parameters:
        path (str): The file about to be replaced. Nothing happens if it does not
            exist, or if no log directory has been recorded.
        kind (VersionedFile): The record describing it: the noun for the log lines, the
            fallback logger name, and the companion extensions.
        logger: The logger to report through. Defaults to the kind's own.

    Raises:
        FileNotFoundError: raised by ``copy()`` on a companion file that is not beside
            the original, and on a recorded log directory that does not exist. The
            versioned copy of the original is already in place by the time a companion
            fails, so such a call leaves the destination directory partly filled.
        ValueError: raised by ``next_version_dest()`` for a log directory already
            holding a file whose three characters before the extension are not a
            number.
    """

    if not os.path.exists(path):
        return

    logger = logger or pdslogger.PdsLogger.get_logger(kind.logname)

    (prefix, ext) = os.path.splitext(os.path.basename(path))
    stem = path.rpartition('.')[0]

    from_logged = False
    for log_dir in _common.LOGDIRS:
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
    """Return the MD5 digest of one file, as the checksum files record it.

    The file is read in blocks rather than at once, so the memory a call needs does not
    grow with the file. MD5 is what the PDS checksum manifests use; the digest is a
    check against corruption in transfer or storage and nothing here treats it as
    proof against tampering.

    Parameters:
        fname (str): The path of the file to read.
        blocksize (int): How many bytes to read at a time.

    Returns:
        str: The digest, as 32 lowercase hexadecimal characters.

    Raises:
        OSError: raised by ``open()`` if the file cannot be read.
    """

    hasher = hashlib.md5()

    with open(fname, 'rb') as f:
        for chunk in iter(lambda: f.read(blocksize), b''):
            hasher.update(chunk)

    return hasher.hexdigest()


##########################################################################################
# Command line for the checksum and shelf file tools
#
# These tools take a target that can name one file inside a unit rather than the
# whole unit, so a command-line path expands to (unit, selection) pairs and the
# driver below is not the one run_main provides.
##########################################################################################

ARCHIVES_ARGUMENT = (('--archives', '-a'),
                     {'default': False, 'action': 'store_true',
                      'help': 'Instead of referring to a {unit}, refer to the the '
                              'archive file for that {unit}.'})

INFOSHELF_ARGUMENT = (('--infoshelf', '-i'),
                      {'dest': 'infoshelf', 'default': False, 'action': 'store_true',
                       'help': 'After a successful run, also execute the equivalent '
                               'pdsinfoshelf command.'})

CHECKSUMS_DESCRIPTION = ('{progname}: Create, maintain and validate MD5 checksum files '
                         'for PDS {units} and {unit} sets.')

CHECKSUMS_TASK_HELP = {
    'initialize': 'Create an MD5 checksum file for a {unit} or {unit} set. Abort if '
                  'the checksum file already exists.',
    'reinitialize': 'Create an MD5 checksum file for a {unit} or {unit} set. Replace '
                    'the checksum file if it already exists. If a single file is '
                    'specified, such as one archive file in a {unit} set, only single '
                    'checksum is re-initialized.',
    'validate': 'Validate every file in a {unit} directory tree against its MD5 '
                'checksum. If a single file is specified, such as one archive file in '
                'a {unit} set, only that single checksum is validated.',
    'repair': 'Validate every file in a {unit} directory tree against its MD5 '
              'checksum. If any disagreement is found, the checksum file is replaced; '
              'otherwise it is unchanged. If a single file is specified, such as one '
              'archive file of a {unit} set, then only that single checksum is '
              "repaired. If any of the files checked are newerthan the checksum file, "
              "update shelf file's modification date",
    'update': 'Search a directory for any new files and add their MD5 checksums to the '
              'checksum file. Checksums of pre-existing files are not checked.',
}

CHECKSUMS_POSITIONAL_HELP = ('The path to the root directory of a {unit} or {unit} '
                             'set. For a {unit} set, all the {unit} directories inside '
                             'it are handled in sequence. Note that, for archive '
                             'directories, checksums are grouped into one file for the '
                             'entire {unit} set.')

INFOSHELF_DESCRIPTION = ('{progname}: Create, maintain and validate shelf files '
                         'containing basic information about each file.')

INFOSHELF_TASK_HELP = {
    'initialize': 'Create an infoshelf file for a {unit}. Abort if the file already '
                  'exists.',
    'reinitialize': 'Create an infoshelf file for a {unit}. Replace the file if it '
                    'already exists. If a single file is specified, such as one '
                    'archive file in a {unit} set, then only information about that '
                    'file is re-initialized.',
    'validate': 'Validate every file in a {unit} against the contents of its infoshelf '
                'file. If a single file is specified, such as an archive file in a '
                '{unit} set, then only information about that file is validated',
    'repair': 'Validate every file in a {unit} against the contents of its infoshelf '
              'file. If any file has changed, the infoshelf file is replaced. If a '
              'single file is specified, such as an archive file in a {unit} set, then '
              'only information about that file is repaired. If any of the files '
              "checked are newer than the shelf file, update the shelf file's "
              'modification date.',
    'update': 'Search a directory for any new files and add their information to the '
              'infoshelf file. Information about pre-existing files is not updated. If '
              'any of the files checked are newer than the shelf file, update the '
              "shelf file's modification date.",
}

INFOSHELF_POSITIONAL_HELP = ('The path to the root of the {unit} or {unit} set. For a '
                             '{unit} set, all the {unit} directories inside it are '
                             'handled in sequence.')


def resolve_holdings_paths(spec, paths, *, archives):
    """Return the absolute paths one of these tools was asked to work on.

    Each command-line path must fall inside a holdings tree and must not name
    checksum files. With archives set, a path that does not already name archive
    files is redirected to the archive files of the same unit. A path that does not
    resolve to anything gets one more chance, as a unit name standing in for that
    unit's .tar.gz archive.

    The redirection under --archives is textual: the part of the path after the holdings
    sentinel gets "archives-" put in front of it, so "volumes/COISS_1xxx" becomes
    "archives-volumes/COISS_1xxx" and a path already under an archives category is left
    alone. Nothing checks that the redirected path exists until it is resolved.

    The second chance is for a path that names no file. Its last component is treated as
    a unit name, and it is taken only when the parent directory is inside an archives
    category and the component carries no dot. The basename is then the unit name plus
    ".tar.gz" where the parent's bundletype is the spec's own unit, and the unit name
    plus "_<bundletype>.tar.gz" anywhere else, which is what an archived metadata or
    previews directory holds. The result is globbed, so a name that expands to several
    archives contributes all of them, in glob order rather than in any order imposed
    here.

    Every path is checked and resolved before any is returned, so one bad path in a
    command line stops the whole run.

    Parameters:
        spec (ToolSpec): The tool's specification.
        paths (list): The command-line paths.
        archives (bool): True if --archives was given.

    Returns:
        list[str]: The absolute paths, in command-line order. A path that took the
        second chance contributes one entry per archive the glob matched.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 if a path is outside the holdings
            tree or names checksum files.
        ValueError: from ``from_abspath()``. The first call's is caught and re-raised
            for a path that is not an unresolved unit name inside an archives
            directory, or that is one but matches no archive; the second call, on the
            parent directory, can raise one of its own.
        OSError: from the first ``from_abspath()`` call, caught and re-raised on the
            same terms.
    """

    sentinel = spec.holdings_sentinel
    abspaths = []
    for path in paths:

        # Make sure path makes sense
        path = os.path.abspath(path)
        parts = path.partition(sentinel)
        if not parts[1]:
            print('Not a holdings subdirectory: ' + path)
            sys.exit(1)

        if parts[2].startswith('checksums-'):
            print(spec.checksum_path_message + path)
            sys.exit(1)

        # Convert to an archives path if necessary
        if archives and not parts[2].startswith('archives-'):
            path = parts[0] + sentinel + 'archives-' + parts[2]

        # Convert to a list of absolute paths that exist (unit sets or units)
        try:
            pdsf = spec.pdsfile_cls.from_abspath(path, must_exist=True)
            abspaths.append(pdsf.abspath)

        except (ValueError, OSError):
            # Allow a unit name to stand in for a .tar.gz archive
            (dirname, basename) = os.path.split(path)
            pdsdir = spec.pdsfile_cls.from_abspath(dirname)
            if pdsdir.archives_ and '.' not in basename:
                if pdsdir.bundletype_ == spec.unit + 's/':
                    basename += '.tar.gz'
                else:
                    basename += f'_{pdsdir.bundletype_[:-1]}.tar.gz'

                newpaths = glob.glob(os.path.join(dirname, basename))
                if len(newpaths) == 0:
                    raise

                abspaths += newpaths
                continue
            else:
                raise

    return abspaths


def expand_selection_targets(spec, abspaths):
    """Return the (unit, selection) pairs those absolute paths name.

    A unit set expands to its unit directories, except an archive unit set, whose
    files are handled as one group. A file expands to its own unit paired with its
    basename, which is the selection the task functions narrow their work to.

    An archive unit set is the one directory that stays whole, and the reason holds for
    both kinds of tool on this driver: an archive's derived file covers the whole unit
    set rather than one unit, whether it is the checksum file the task help describes or
    the info shelf that PdsFile builds from the unit set downward. Any other unit set
    contributes its unit directories and nothing else, so a readme file sitting at
    unit-set level is dropped rather than rejected.

    A file is accepted on either of two grounds: it stands for a whole bundle, which is
    a unit's own archive or checksum file, or its parent is a unit directory, which
    makes it a top-level file of that unit. Either way the pair names the parent
    directory and the file's basename, so the task works on the unit and narrows to the
    one file. A file deeper inside a unit satisfies neither and is rejected.

    Parameters:
        spec (ToolSpec): The tool's specification. Its pdsfile_cls builds each object
            and its two invalid-path messages are what a rejection prints.
        abspaths (list): The absolute paths, as resolve_holdings_paths() returned them.

    Returns:
        list: (PdsFile, selection) pairs, where selection is None for a whole unit.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 for a directory or a file this
            tool cannot work on.
    """

    info = []
    for path in abspaths:
        pdsf = spec.pdsfile_cls.from_abspath(path)

        if pdsf.is_bundleset_dir:
            # Archive directories are handled by unit set
            if pdsf.archives_:
                info.append((pdsf, None))

            # Others are handled by unit
            else:
                children = [pdsf.child(c) for c in pdsf.childnames]
                info += [(c, None) for c in children if c.isdir]
                        # "if c.isdir" is False for unit set level readme files

        elif pdsf.is_bundle_dir:
            # Handle one unit
            info.append((pdsf, None))

        elif pdsf.isdir:
            print(spec.invalid_dir_message + pdsf.logical_path)
            sys.exit(1)

        else:
            pdsdir = pdsf.parent()
            if pdsf.is_bundle_file:
                # Handle one archive file
                info.append((pdsdir, pdsf.basename))
            elif pdsdir.is_bundle_dir:
                # Handle one top-level file in a unit
                info.append((pdsdir, pdsf.basename))
            else:
                print(spec.invalid_file_message + pdsf.logical_path)
                sys.exit(1)

    return info


@dataclass
class RunResult:
    """What run_selection_main() finished with, for a tool that has more to do.

    The three fields exist because the four tools on that driver disagree about what to
    do next, and each reads a different one: the info shelf tools read status alone, and
    the checksum tools read proceed and args together to decide whether to chain a
    pdsinfoshelf run.

    Attributes:
        args: The parsed command line.
        status: 1 if the run logged a fatal or an error, 0 otherwise.
        proceed: What the last task returned, or None if no task ran; forced to
            False when the run logged a fatal or an error. It is one value for the
            whole run rather than one per target, so on a command line naming several
            targets it reports the last of them.
    """

    args: argparse.Namespace
    status: int
    proceed: object


def run_selection_main(spec, tasks, argv):
    """Run one checksum or info shelf tool: parse the command line, log, do the task.

    This is the driver the two checksum tools and the two info shelf tools reach. It
    resolves and expands every command-line path itself rather than through the spec, so
    a tool on this driver leaves expand_target unset, and it picks the log path method
    per target rather than reading spec.log_path_method: a target that names a unit logs
    under that unit, one that names only a unit set logs under the set.

    Each task is called with the unit and the selection, and its return value becomes
    the run's ``proceed``. On a selection, a ``reinitialize`` task is run as ``update``
    instead, so narrowing to one file cannot erase the entries for every other.

    Unlike the other two drivers this returns rather than exiting, because what the four
    tools do with the outcome differs: the info shelf tools exit with the status, and
    the checksum tools read ``proceed`` to decide whether to chain a second run and
    otherwise exit 0 whatever the status was.

    Parameters:
        spec (ToolSpec): The tool's specification.
        tasks (dict): The tool's task functions, keyed by task name. Each is called
            with one target and its selection.
        argv (list): The full command line, sys.argv.

    Returns:
        RunResult: What the run finished with: the parsed command line, the status, and
        what the last task returned.

    Raises:
        SystemExit: from ``sys.exit()`` inside ``setup_run()`` with status 1 if no task
            was given, 0 for --help and 2 for a command line the parser cannot
            classify, and from the two path helpers on a path they reject. A task that
            raises is logged and re-raised, so the result is not built at all.
        ValueError: raised by ``resolve_holdings_paths()``, before any logging is open,
            for a path that resolves to nothing and is not an unresolved unit name
            inside an archives directory.
        OSError: raised by the same ``resolve_holdings_paths()`` call on the same terms.
    """

    (args, logger) = _common.setup_run(spec, argv)

    status = 0

    # Prepare the list of paths, then the list of tuples (pdsfile, selection)
    abspaths = resolve_holdings_paths(spec, getattr(args, spec.unit),
                                      archives=args.archives)
    info = expand_selection_targets(spec, abspaths)

    # Begin logging and loop through tuples...
    logger.open(' '.join(argv))
    proceed = None
    try:
        for (pdsdir, selection) in info:

            if selection:
                pdsf = pdsdir.child(os.path.basename(selection))
            else:
                pdsf = pdsdir

            # Save logs in up to two places
            method = (UNIT_LOG_PATH_METHOD if pdsf.bundlename
                      else UNITSET_LOG_PATH_METHOD)
            logfiles = _common.log_paths_for(pdsf, method, spec.log_suffix,
                                     task=args.task, dir=spec.progname)

            # Create all the handlers for this level in the logger
            local_handlers = []
            _common.set_log_dirs(logfiles)
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                local_handlers += [make_handler(logdir)
                                   for make_handler in spec.handler_factories]

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

                task = args.task
                if task == 'reinitialize' and selection:
                    task = 'update'         # don't erase everything else!

                proceed = tasks[task](pdsdir, selection)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                proceed = False
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        proceed = False
        status = 1
        raise

    finally:
        (fatal, errors, _warnings, _tests) = logger.close()
        if fatal or errors:
            proceed = False
            status = 1

    return RunResult(args=args, status=status, proceed=proceed)
