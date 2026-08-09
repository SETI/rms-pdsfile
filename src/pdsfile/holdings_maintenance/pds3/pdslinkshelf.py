#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdslinkshelf.py
################################################################################

"""pdslinkshelf: find the links inside a PDS3 volume's files, and shelve them.

A link shelf records, for every file in a volume, either the list of files that file
points at or the label that describes it. What is here is the scan that finds them, which
is the one thing the two flavors of this tool do differently, because a PDS3 label names
the file it describes in ``KEYWORD = FILENAME`` syntax and a PDS4 label in an XML element.
Everything that reads, writes, compares or drives a link shelf is in
``_linkshelf_common``, and so are all five tasks; the driver is ``_common.run_main()``.

Four tables here say what the scan means by a link:

  * ``TARGET_REGEX1`` recognizes a label naming the file it describes, and is what the
    specification carries as ``link_target_regex``. It is the shared file-name pattern
    with the PDS3 ``KEYWORD =`` prefix in front of it, so it also admits the opening
    bracket or brace that starts a list of targets running over several records.
  * ``EXTS_WO_LABELS`` is the five extensions a file is searched for links in --
    ``.LBL``, ``.CAT``, ``.TXT``, ``.FMT`` and ``.SFD`` -- and is at the same time the set
    of extensions a file does not need a label of its own for. The one test serves both,
    which is why a ``.TXT`` file that has a label is reported as carrying an unnecessary
    one rather than as satisfying a requirement.
  * ``KNOWN_MISSING_LABELS`` names the files a label is not looked for: "missing" for one
    that has no label and is not expected to, and "unneeded" for one that carries a PDS3
    label inside itself.
  * ``REPAIRS``, imported from ``linkshelf_repairs``, is the table of published links that
    are wrong and what each was meant to say. That module documents how an entry works.

The specification names ``_shelf_common.UNIT_LOG_PATH_METHOD`` as its log path method,
which is ``log_path_for_bundle`` on the shared PdsFile base rather than the
``log_path_for_volume`` alias ``Pds3File`` also carries; the two are the same method,
since the alias forwards. Its log suffix is '_links',
which ``pdsarchives`` also passes, and the two do not collide because each tool's
``progname`` becomes a directory component of the log path.

One field of the specification is set here and read nowhere a run of this tool reaches:
``index_ext``, which only the index shelf tools' target expansion reads. Both of the
others that differ by flavor do reach something: ``holdings_sentinel`` is where the
upward search for a non-local link stops, and ``file_log_level`` is the method a created
directory is reported through when a shelf is written.

The five shared tasks are bound to this module's own names with this specification
supplied. ``re_validate`` reaches ``validate`` that way, as a library function rather than
through a command line.
"""

import datetime
import os
import re
import sys

import pdslogger
import translator

import pdsfile
from pdsfile.holdings_maintenance import _common, _linkshelf_common, _shelf_common
from pdsfile.holdings_maintenance.pds3.linkshelf_repairs import REPAIRS

LOGNAME = _shelf_common.LINKSHELF_LOGNAME

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

KNOWN_MISSING_LABELS = translator.TranslatorByRegex([
    (r'.*/document/.*',                                     re.I, 'missing'),
    (r'.*/COCIRS_.*\.VAR',                                  0,    'missing'),
    (r'.*/COCIRS_.*VANILLA.*',                              re.I, 'missing'),
    (r'.*/COCIRS_0209/DATA/NAV_DATA/RIN02101300.DAT',       0,    'missing'),
    (r'.*/COCIRS_0602/DATA/UNCALIBR/FIFM06021412.DAT',      0,    'missing'),
    (r'.*/COISS_00.*/document/report/.*',                   0,    'missing'),
    (r'.*/COISS_0011/calib.*\.tab',                         0,    'missing'),
    (r'.*/COISS_0011/calib/calib.tar.gz',                   0,    'missing'),
    (r'.*/COISS_0011/extras/.*\.pro',                       0,    'missing'),
    (r'.*/COISS_0011/extras/cisscal.*',                     0,    'missing'),
    (r'.*/CO(ISS|VIMS)_.*/extras/.*\.(tiff|png|jpg|jpeg|jpeg_small)',
                                                            0,    'missing'),
    (r'.*/COSP_xxxx.*\.(pdf|zip|tm|orb)',                   0,    'missing'),
    (r'.*/COUVIS_.*/SOFTWARE/.*\.(PRO|pro|DAT|IDL|JAR|SAV)',0,    'missing'),
    (r'.*/COUVIS_.*/CALIB/.*\.DOC',                         0,    'missing'),
    (r'.*/COUVIS_0xxx.*/SOFTWARE/CALIB/VERSION_4/t.t',      0,    'missing'),
    (r'.*/COVIMS_0xxx.*/index/index.csv',                   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/software/.*',                       0,    'missing'),
    (r'.*/COVIMS_0xxx.*/calib/example.*',                   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/calib/.*\.(tab|qub|cub|bin|lbl)',   0,    'missing'),
    (r'.*/COVIMS_0xxx.*/browse/.*\.pdf',                    0,    'missing'),
    (r'.*/COVIMS_0xxx.*\.(lbl|qub)-old_V[0-9]+',            0,    'missing'),
    (r'.*/GO_0xxx_v1/GO_0001/CATALOG/REF.CAT.BAK',          0,    'missing'),
    (r'.*/GO_0xxx.*/GO_0001/SOFTWARE/GALSOS2.EXE',          0,    'missing'),
    (r'.*/GO_0xxx_v1/GO_0016/AAREADME.SL9',                 0,    'missing'),
    (r'.*/JNOJNC_0xxx.*/EXTRAS/.*\.PNG',                    0,    'missing'),
    (r'.*/NH.*/browse/.*\.jpg',                             0,    'missing'),
    (r'.*/NH.*/index/newline',                              0,    'missing'),
    (r'.*/NHxxMV.*/calib/.*\.png',                          0,    'missing'),
    (r'.*/NHSP_xxxx.*/DATASET.HTML',                        0,    'missing'),
    (r'.*/RPX.*/UNZIP532.*',                                0,    'missing'),
    (r'.*/RPX_xxxx/RPX_0201/CALIB/.*/(-180|128)',           0,    'missing'),
    (r'.*/VG.*/VG..NESR\.DAT',                              0,    'missing'),
    (r'.*/VG_0xxx.*/CUMINDEX.TAB',                          0,    'missing'),
    (r'.*/VG_0xxx.*/SOFTWARE/.*',                           0,    'missing'),
    (r'.*/VG._9xxx.*/SOFTWARE/.*',                          0,    'missing'),
    (r'.*/VG2_9065/BROWSE/C0SR01AA.LOG',                    0,    'missing'),

# These files have internal PDS3 labels, so these are not errors
    (r'.*/COISS_3xxx.*\.IMG',                               0,    'unneeded'),
    (r'.*/COUVIS_.*/SOFTWARE/.*\.txt_.*',                   0,    'unneeded'),
    (r'.*/VG_.*\.(IMQ|IRQ|IBG)',                            0,    'unneeded'),
    (r'.*/VG_0xxx.*/(AAREADME.VMS|VTOC.SYS|IMGINDEX.DBF)',  0,    'unneeded'),
])

# Match pattern for the file name in anything of the form "keyword = filename"
TARGET_REGEX1 = re.compile(r'^ *\^?\w+ *= *\(?\{? *' +
                           _linkshelf_common.LINK_NAME_PATTERN, re.I)

EXTS_WO_LABELS = {'.LBL', '.CAT', '.TXT', '.FMT', '.SFD'}

################################################################################

def generate_links(dirpath, old_links=None, *, logger=None, limits=None):
    """Return what every file in one volume points at, or what points at it.

    This is the specification's ``generate_links``, and the five shared tasks call nothing
    else to learn what a volume holds. It walks the volume once and does two passes over
    each directory: the first reads every file with one of the five link-bearing
    extensions and resolves what it names, and the second decides which label, if any,
    describes each of the remaining files.

    **Resolving a link is a search, and it can end four ways.** A name matching a file in
    the same directory resolves there, case-insensitively, and the shelved name takes the
    case the filesystem has. A name that matches nothing local is put through the repair
    table first, then discarded if it parses as a float or as a Fortran format code such
    as ``F10.3``, and only then searched up the tree. A search that fails is an error for
    a ``.FMT`` or a ``.CAT`` name and a debug line for anything else, on the reasoning
    that most unresolved candidates are not links at all.

    A label is credited to a file on one of three grounds, in order: the label's own name
    matches the file's up to the extension; exactly one label in the directory named the
    file in a target position; or, failing both, the file is reported as having a missing
    or an ambiguous label and is shelved with an empty string. ``KNOWN_MISSING_LABELS``
    excuses a file from the search altogether.

    **The modification time is the newest among every file the walk sees**, taken before
    any skip test and whether or not the file is opened, so a ``.DS_Store`` or a backup
    file touched today moves it. Four kinds of file are skipped after that: a
    ``.DS_Store``, a dot-underscore file, a backup file, and any file whose basename
    begins with a dot.

    ``old_links`` is what makes an update affordable and is the one argument that changes
    the shape of the answer. A file already keyed in it is not re-read, and its shelved
    triples are carried through as they are. **The result is still assembled from the
    files the walk found**, so an entry in ``old_links`` for a file that has since been
    deleted is dropped rather than carried.

    Parameters:
        dirpath (str): The volume directory to walk. A relative path is made absolute.
        old_links (dict): What the shelf already holds, keyed by absolute path, or None
            for a scan from scratch. Its string values seed the label map and its list
            values are carried through untouched.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the shared defaults.

    Returns:
        tuple: the links keyed by absolute path, and the newest modification time as a
        timestamp. A file that points at others maps to a list of (record number, link
        text, absolute path) triples; a file that is pointed at maps to the absolute path
        of its label; a file that neither points nor is pointed at maps to the empty
        string, and so does one whose label is missing or ambiguous.

    Raises:
        ValueError: raised by ``from_abspath()``, before any log line is written, for a
            directory outside every holdings tree.
        OSError: raised by ``getmtime()`` on a file the walk listed and that is gone by
            the time it is measured, by ``read_links()`` on one that cannot be read, and
            by the ``listdir()`` calls inside the upward search. Each is logged through
            ``exception()`` and re-raised, as is anything else the scan raises.
    """

    if old_links is None:
        old_links = {}
    if limits is None:
        limits = {}

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)

    merged_limits = _linkshelf_common.GENERATE_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Finding link shelf files', dirpath, limits=merged_limits)

    try:

        linkinfo_dict = old_links.copy()      # abspath: list of LinkInfo objects
        label_dict = {k:v for k,v in old_links.items() if isinstance(v,str)}
                                            # abspath: label for this file
        abspaths = []                         # list of all abspaths

        latest_mtime = 0.

        # Walk the directory tree, one subdirectory "root" at a time...
        for (root, _dirs, files) in os.walk(dirpath):

            local_basenames = []            # Tracks the basenames in this directory
            local_basenames_uc = []         # Same as above, but upper case
            for basename in files:
                abspath = os.path.join(root, basename)
                latest_mtime = max(latest_mtime, os.path.getmtime(abspath))

                if basename == '.DS_Store':         # skip .DS_Store files
                    logger.ds_store('.DS_Store file skipped', abspath)
                    continue

                if basename.startswith('._'):       # skip dot_underscore files
                    logger.dot_underscore('dot_underscore file skipped',
                                          abspath)
                    continue

                if BACKUP_FILENAME.match(basename) or ' copy' in basename:
                    logger.error('Backup file skipped', abspath)
                    continue

                if basename.startswith('.'):    # skip invisible files
                    logger.invisible('Invisible file skipped', abspath)
                    continue

                abspaths.append(abspath)
                local_basenames.append(basename)
                local_basenames_uc.append(basename.upper())

            # Update linkinfo_dict, searching each relevant file for possible links.
            # If the linking file is a label and the target file has a matching
            # name, update the label_dict entry for the target.
            candidate_labels = {}       # {target: list of possible label basenames}
            for basename in local_basenames:

                abspath = os.path.join(root, basename)
                if abspath in linkinfo_dict:    # for update op, skip existing links
                    continue

                basename_uc = basename.upper()

                # Only check LBL, CAT, TXT, etc.
                ext = basename_uc[-4:] if len(basename) >= 4 else ''
                if ext not in EXTS_WO_LABELS:
                    continue

                # Get list of link info for all possible linked filenames
                logger.debug('*** REVIEWING', abspath)
                linkinfo_list = _linkshelf_common.read_links(SPEC, abspath,
                                                        logger=logger)

                # Apply repairs
                repairs = REPAIRS.all(abspath)
                for info in linkinfo_list:
                    for repair in repairs:
                        linkname = repair.first(info.linktext)
                        if linkname is None:

                            # Attempt repair with leading directory path removed
                            if '/' in info.linktext:
                                info.remove_path()
                                linkname = repair.first(info.linktext)

                            if linkname is None:
                                continue            # no repair found

                        info.linkname = linkname
                        if linkname == '':
                            logger.info('Ignoring link "%s"' %
                                        info.linktext, abspath, force=True)
                        else:
                            logger.info('Repairing link "%s"->"%s"' %
                                        (info.linktext, linkname),
                                        abspath, force=True)

                        # Validate non-local targets of repairs
                        if '/' in linkname:
                            target = os.path.join(root, linkname)
                            if os.path.exists(target):
                                info.target = os.path.abspath(target)
                            else:
                                logger.error('Target of repaired link is missing',
                                             target)

                        break       # apply only one repair per found link

                # Validate or remove other targets
                new_linkinfo_list = []
                baseroot_uc = basename_uc.partition('.')[0]
                ltest = len(baseroot_uc)
                for info in linkinfo_list:
                    if info.target:         # Non-local, repaired links have targets
                        new_linkinfo_list.append(info)
                        continue

                    # A blank linkname is from a repair; indicates to ignore
                    if info.linkname == '':
                        continue

                    # Ignore self-references
                    linkname_uc = info.linkname.upper()
                    if linkname_uc == basename_uc:
                        continue

                    # Check for target inside this directory
                    try:
                        match_index = local_basenames_uc.index(linkname_uc)
                    except ValueError:
                        match_index = None

                    # If not found, maybe it is a non-local reference (.FMT perhaps)
                    if match_index is None:

                        # It's easy to pick up floats as link candidates; ignore
                        try:
                            _ = float(info.linkname)
                            continue            # Yup, it's just a float
                        except ValueError:
                            pass

                        if info.linkname[-1] in ('e', 'E'):
                            try:
                                _ = float(info.linkname[:-1])
                                continue            # Float with exponent
                            except ValueError:
                                pass

                        # Also ignore format specifications (e.g., "F10.3")
                        if info.linkname[0] in ('F', 'E', 'G'):
                            try:
                                _ = float(info.linkname[1:])
                                continue            # Format
                            except ValueError:
                                pass

                        # Search non-locally
                        if '/' in info.linkname:
                            nonlocal_target = _linkshelf_common.locate_link_with_path(
                                                SPEC, abspath, info.linkname)
                        else:
                            nonlocal_target = _linkshelf_common.locate_nonlocal_link(
                                                SPEC, abspath, info.linkname)

                        # Report the outcome
                        if nonlocal_target:
                            logger.debug('Located "%s"' % info.linkname,
                                         nonlocal_target)
                            info.target = nonlocal_target
                            new_linkinfo_list.append(info)
                            continue

                        if linkname_uc.endswith('.FMT'):
                            logger.error('Unable to locate .FMT file "%s"' %
                                         info.linkname, abspath)
                        elif linkname_uc.endswith('.CAT'):
                            logger.error('Unable to locate .CAT file "%s"' %
                                         info.linkname, abspath)
                        else:
                            logger.debug('Substring "%s" is not a link, ignored' %
                                         info.linkname, abspath)

                        continue

                    # Save the match
                    info.linkname = local_basenames[match_index]    # update case
                    info.target = os.path.join(root, info.linkname)
                    new_linkinfo_list.append(info)

                    # Could this be the label?
                    if ext != '.LBL':       # nope
                        continue

                    # If names match up to '.LBL', then yes
                    if (len(linkname_uc) > ltest and
                        linkname_uc[:ltest] == baseroot_uc and
                        linkname_uc[ltest] == '.'):
                        label_dict[info.target] = abspath
                        logger.debug('Label identified for %s' % info.linkname,
                                     abspath)
                        continue

                    # Otherwise, then maybe
                    if info.is_target:
                        if info.linkname in candidate_labels:
                            if basename not in candidate_labels[info.linkname]:
                                candidate_labels[info.linkname].append(basename)
                        else:
                            candidate_labels[info.linkname] = [basename]

                        logger.debug('Candidate label found for ' +
                                     info.linkname, abspath)

                linkinfo_dict[abspath] = new_linkinfo_list

            # Identify labels for files
            for basename in local_basenames:

                basename_uc = basename.upper()
                ext = basename_uc[-4:] if len(basename) >= 4 else ''
                if ext in (".LBL", ".FMT"):     # these can't have labels
                    continue

                abspath = os.path.join(root, basename)
                if abspath in label_dict:
                    continue                    # label already found

                # Maybe we already know the label is missing
                test = KNOWN_MISSING_LABELS.first(abspath)
                if test == 'unneeded':
                    logger.debug('Label is not neeeded', abspath)
                    continue

                if test == 'missing':
                    logger.debug('Label is known to be missing', abspath)
                    continue

                # Determine if a label is required
                label_is_required = (ext not in EXTS_WO_LABELS)

                # Get the list of candidate labels in this directory
                candidates = candidate_labels.get(basename, [])

                # Determine if the obvious label file exists
                label_guess_uc = basename_uc.partition('.')[0] + '.LBL'
                if label_guess_uc in local_basenames_uc:
                    k = local_basenames_uc.index(label_guess_uc)
                    obvious_label_basename = local_basenames[k]
                else:
                    obvious_label_basename = ''

                # Simplest case...
                if obvious_label_basename in candidates:
                    if not label_is_required:
                        logger.debug('Unnecessary label found', abspath, force=True)

                    label_dict[abspath] = os.path.join(root, obvious_label_basename)
                    continue

                # More cases...
                if not label_is_required:
                    continue                # leave abspath out of label_dict

                # Report a phantom label
                if obvious_label_basename:
                    logger.error('Label %s does not point to file' %
                                 local_basenames[k], abspath)

                if len(candidates) == 1:
                    logger.debug('Label found as ' + candidates[0], abspath,
                                 force=True)
                    label_dict[abspath] = os.path.join(root, candidates[0])
                    continue

                # or errors...
                label_dict[abspath] = ""
                if len(candidates) == 0:
                    logger.error('Label is missing', abspath)
                else:
                    logger.error('Ambiguous label found as %s' % candidates[0],
                                 abspath, force=True)
                    for candidate in candidates[1:]:
                        logger.debug('Alternative label found as %s' % candidate,
                                     abspath, force=True)

        # Merge the dictionaries
        # There are cases where a file can have both a list of links and a label.
        # This occurs when a .TXT or .CAT file has a label, even though it didn't
        # need one. In the returned dictionary, link lists take priority.
        link_dict = {}
        for key in abspaths:
            if key in linkinfo_dict:
                # If this is a new entry, it's a list of LinkInfo objects
                # If this was copied from old_links, it's already a list of tuples
                values = linkinfo_dict[key]
                if isinstance(values, list):
                    # Normalize to (recno, basename, abspath)
                    new_list = []
                    for item in values:
                        if isinstance(item, _linkshelf_common.LinkInfo):
                            new_list.append((item.recno, item.linktext, item.target))
                        else:
                            new_list.append(item)
                    link_dict[key] = new_list
                else:
                    link_dict[key] = values
            elif key in label_dict:
                link_dict[key] = label_dict[key]
            else:
                link_dict[key] = ''

        dt = datetime.datetime.fromtimestamp(latest_mtime)
        logger.info('Lastest holdings file modification date',
                    dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

        return (link_dict, latest_mtime)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################
# Executable program
################################################################################

def link_targets(pdsf, path):
    """Return the volume directories one command-line path names.

    This is the specification's ``expand_target``, and it exists to supply the
    specification to the shared expansion: ``_common.run_main()`` calls ``expand_target``
    with the PdsFile and the path alone, so the three-argument shared function cannot be
    named directly. It is the reason both link shelf tools carry a function of this name
    that does nothing else.

    Parameters:
        pdsf: The PdsFile the command-line path resolved to.
        path (str): The absolute path it resolved to, for the rejection messages.

    Returns:
        list: The volume directories to shelve, which is a volume set's directory
        children, the path itself if it is a directory, and nothing otherwise.

    Raises:
        SystemExit: from ``sys.exit()`` inside ``_linkshelf_common.link_targets()``, with
            status 1 if the path names checksum files or archive files.
    """

    return _linkshelf_common.link_targets(SPEC, pdsf, path)

SPEC = _common.ToolSpec(
    progname='pdslinkshelf',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds3File,
    unit='volume',
    holdings_sentinel='/holdings/',
    index_ext='.tab',
    file_log_level='info',
    description=_linkshelf_common.LINKSHELF_DESCRIPTION,
    task_help=_linkshelf_common.LINKSHELF_TASK_HELP,
    positional_help=_linkshelf_common.LINKSHELF_POSITIONAL_HELP,
    log_path_method=_shelf_common.UNIT_LOG_PATH_METHOD,
    log_suffix='_links',
    expand_target=link_targets,
    handler_factories=(pdslogger.error_handler,),
    generate_links=generate_links,
    link_target_regex=TARGET_REGEX1)

TASKS = _linkshelf_common.link_tasks(SPEC)

# The task functions, under the names this module carries them as a library.
# Each is the shared task with this tool's spec bound in; re_validate reaches
# validate() through this name.
initialize = TASKS['initialize']
reinitialize = TASKS['reinitialize']
validate = TASKS['validate']
repair = TASKS['repair']
update = TASKS['update']

def main():
    """Run the tool: hand this module's specification and tasks to the generic driver.

    This is the ``pdslinkshelf`` console script's entry point. It does not return: the
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
