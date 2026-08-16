#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds4/pds4linkshelf.py
################################################################################

"""pds4linkshelf: find the links inside a PDS4 bundle's files, and shelve them.

A link shelf records, for every file in a bundle, either the list of files that file
points at or the label that describes it. What is here is the scan that finds them, which
is the largest of the things the two flavors of this tool do differently, because a PDS4
label names the file it describes in a ``<file_name>`` element and a PDS3 label in
``KEYWORD = FILENAME`` syntax. Everything that reads, writes, compares or drives a link
shelf is in ``_linkshelf_common``, and so are all five tasks; the driver is
``_common.run_main()``.

Four tables here say what the scan means by a link, and two of them are empty:

  * ``TARGET_REGEX1`` recognizes a label naming the file it describes, and is what the
    specification carries as ``link_target_regex``. It is the shared file-name pattern
    wrapped in a ``<file_name>`` element, matched case-insensitively.
  * ``EXTS_WO_LABELS`` is the five extensions a file is searched for links in --
    ``.XML``, ``.LBLX``, ``.CAT``, ``.FMT`` and ``.SFD`` -- and is at the same time the
    set of extensions a file does not need a label of its own for.
  * ``REPAIRS`` is an **empty** translator. One lookup is made per file scanned and it
    matches nothing, so the loop over the matched entries, which sits inside the loop over
    the file's links, never has a body to run and no link is ever looked up or repaired.
    That is why there is no counterpart here to the PDS3 tool's ``linkshelf_repairs``
    module: the machinery is in place and the table is empty.
  * ``KNOWN_MISSING_LABELS`` is empty for the same reason, so no file is excused from the
    label search on the strength of being known to have none.

What takes their place is the collection inventory. A PDS4 collection lists its members in
a ``collection*.csv`` file, and this scan reads every such file it walks past and keeps
the last component of each listed identifier. Before reporting that a file has no label at
all or an ambiguous one, it asks whether a collection file whose path begins with that
file's own directory or the one above it lists the file, and **a file no such collection
lists is passed over**: an errata file or a checksum manifest is not part of the archive
and is not expected to be labeled. It is passed over rather than passed over silently --
the question itself is logged for every file that reaches it, and the separate "does not
point to file" error for a mismatched label is raised before the question is asked.

The other thing this scan does that the PDS3 one does not is credit a label by what it
says rather than by what it is called: a file whose name appears anywhere in a label in
the same directory is shelved as described by that label. It is a fallback and not a first
resort, because the name-matching credit is settled in the earlier pass and this one
skips any file already credited there. **It is the label's own text and not its**
``<file_name>`` **elements** that this matches against, even though the log line
calls it a file_name tag: the comparison runs over every link the label yielded, and
the general pattern's matches are among them.

The specification names ``_shelf_common.UNIT_LOG_PATH_METHOD`` as its log path method and
'_links' as its log suffix. Ten fields of this specification differ from the PDS3 tool's,
and one of the ten is read nowhere a run of this tool reaches: ``index_ext``, which only
the index shelf tools' target expansion reads. Three of the other nine are worth naming
because what they reach is not obvious from the name. ``holdings_sentinel`` is where the
upward search for a non-local link stops. ``file_log_level`` is the method a created
directory is reported through when a shelf is written. And ``handler_factories`` adds a
warning handler ahead of the error handler, so a run leaves a warning file in each of its
log directories that a PDS3 run does not. The remaining six are ``progname``, which the
paragraph below covers, and ``pdsfile_cls``, ``unit``, ``expand_target``,
``generate_links`` and ``link_target_regex``, which are what makes this the PDS4 tool at
all.

``progname`` is this module's own name, as it is for all five PDS4 tools: it is what the
``--help`` description and the "Missing task" error call the tool, and it names the
subdirectory of every log root, so each flavor writes into a directory of its own. What
they do share is the logger name 'pds.validation.links', which is what stops the two from
being driven from a single process.

The five shared tasks are bound to this module's own names with this specification
supplied. Nothing in this package calls them that way.
"""

import csv
import datetime
import os
import re
import sys

import pdslogger
import translator

import pdsfile
from pdsfile.holdings_maintenance import _common, _linkshelf_common, _shelf_common

LOGNAME = _shelf_common.LINKSHELF_LOGNAME

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

REPAIRS = translator.TranslatorByRegex([])

KNOWN_MISSING_LABELS = translator.TranslatorByRegex([])

# Match pattern for the file name in anything of the form
# "<file_name>file name</file_name>" in the PDS4 label
TARGET_REGEX1 = re.compile(r'^ *\<file_name\>' + _linkshelf_common.LINK_NAME_PATTERN +
                           r'\<\/file_name\>', re.I)

EXTS_WO_LABELS = {'.XML', '.LBLX', '.CAT', '.FMT', '.SFD'}

################################################################################

def generate_links(dirpath, old_links=None, *, logger=None, limits=None):
    """Return what every file in one bundle points at, or what points at it.

    This is the specification's ``generate_links``, and the five shared tasks call nothing
    else to learn what a bundle holds. It walks the bundle once and does two passes over
    each directory: the first reads every file with one of the five link-bearing
    extensions and resolves what it names, and the second decides which label, if any,
    describes each of the remaining files. **An extension here is what follows the last
    dot**, so a five-character one such as ``.LBLX`` is recognized; the PDS3 tool takes
    the last four characters instead.

    **Resolving a link is a search, and it can end four ways.** A name matching a file in
    the same directory resolves there, case-insensitively, and the shelved name takes the
    case the filesystem has. A name that matches nothing local is discarded if it parses
    as a float or as a Fortran format code such as ``F10.3``, and only then searched up
    the tree. A search that fails is an error for a ``.FMT`` or a ``.CAT`` name and a
    debug line for anything else, on the reasoning that most unresolved candidates are not
    links at all. The repair table is consulted once per file before any of that, matches
    nothing, and so never reaches a link.

    **A label is credited to a file on one of three grounds, in this order.** First, in
    the earlier pass, a label that mentioned the file and whose own name matches the
    file's up to the extension. Second, in the later pass and only for a file the first
    left uncredited, **any** label in the same directory that mentioned the file, whatever
    that label is called; the PDS3 tool has no equivalent of this one. Third, the only
    label in the directory that mentioned the file **in a target position**. Failing all
    three, the file is reported as having a missing or an ambiguous label -- but only if
    the collection inventory lists it.

    Only the third ground asks how the mention was matched. The first two accept any link
    the scan found in the label, so a file named in a comment credits the label as surely
    as one named in a ``<file_name>`` element does, although the log line for the second
    calls it a file_name tag.

    **The second ground is case-sensitive at both ends.** The labels of a directory are
    collected by testing each basename for the literal '.xml' or '.lblx', so a label named
    in upper case is not among them; and the mention is compared to the file's basename
    exactly, so a label naming ``FOO.DAT`` does not credit a ``foo.dat``. The collection
    inventory is read and matched case-sensitively too. Everything to do with resolving a
    link, and the extension tests above, upper-case first.

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
        dirpath (str): The bundle directory to walk. A relative path is made absolute.
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
            the time it is measured, by ``read_links()`` on one that cannot be read, by
            the ``open()`` of a collection inventory, and by the ``listdir()`` calls
            inside the upward search. Each is logged through ``exception()`` and
            re-raised, as is anything else the scan raises.
        UnicodeDecodeError: raised by the ``reader()`` iteration over a collection
            inventory that is not decodable in the platform's default encoding, which is
            the one file this scan opens as text without naming an encoding.
    """

    if old_links is None:
        old_links = {}
    if limits is None:
        limits = {}

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds4File.from_abspath(dirpath)

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
        collection_basename_dict = {}
        # Walk the directory tree, one subdirectory "root" at a time...
        for (root, _dirs, files) in os.walk(dirpath):

            local_basenames = []            # Tracks the basenames in this directory
            local_basenames_uc = []         # Same as above, but upper case
            for basename in files:
                abspath = os.path.join(root, basename)
                latest_mtime = max(latest_mtime, os.path.getmtime(abspath))

                if basename == '.DS_Store':    # skip .DS_Store files
                    logger.ds_store('.DS_Store file skipped', abspath)
                    continue

                if basename.startswith('._'):   # skip dot_underscore files
                    logger.dot_underscore('dot_underscore file skipped',
                                        abspath)
                    continue

                if BACKUP_FILENAME.match(basename) or ' copy' in basename:
                    logger.error('Backup file skipped', abspath)
                    continue

                if basename.startswith('.'):    # skip invisible files
                    logger.invisible('Invisible file skipped', abspath)
                    continue

                # collection_basename_dict: a dictonary with the abspath of a collection
                # csv file as the key and the set of basenames of its corresponding
                # entries as the value.
                # Create collection_basename_dict and use it to check whether a file
                # is listed in the csv later.
                if (basename.startswith('collection') and
                    basename.endswith('.csv') and
                    abspath not in collection_basename_dict):
                    logger.debug('Construct collection basename dictionary from', abspath)
                    csv_basenames = set()
                    with open(abspath) as file:
                        csv_lines = csv.reader(file)
                        for line in csv_lines:
                            # skip the empty line
                            if not line:
                                continue
                            if '::' in line[-1]:
                                lid = line[-1].rpartition('::')[0]
                            else:
                                lid = line[-1]
                            csv_basename = lid.rpartition(':')[-1]
                            csv_basenames.add(csv_basename)

                    collection_basename_dict[abspath] = csv_basenames

                abspaths.append(abspath)
                local_basenames.append(basename)
                local_basenames_uc.append(basename.upper())

            local_labels = [f for f in local_basenames if '.xml' in f or '.lblx' in f]
            local_labels_abspath = [os.path.join(root, f) for f in local_labels]

            # Update linkinfo_dict, searching each relevant file for possible links.
            # If the linking file is a label and the target file has a matching
            # name, update the label_dict entry for the target.
            candidate_labels = {}       # {target: list of possible label basenames}
            for basename in local_basenames:

                abspath = os.path.join(root, basename)
                if abspath in linkinfo_dict:    # for update op, skip existing links
                    continue

                basename_uc = basename.upper()

                # Only check XML, CAT etc.
                _, is_ext_exists, ext = basename_uc.rpartition('.')
                ext = f'.{ext}' if is_ext_exists else ''
                if ext not in EXTS_WO_LABELS:
                    continue

                # Get list of link info for all possible linked filenames
                logger.info('*** Get link info and review', abspath)
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
                                logger.error('Target of repaired link is missing', target)

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
                    if ext != '.XML' and ext != '.LBLX':       # nope
                        continue

                    # If names match up to '.XML' or '.LBLX', then yes
                    if (len(linkname_uc) > ltest and
                        linkname_uc[:ltest] == baseroot_uc and
                        linkname_uc[ltest] == '.'):
                        label_dict[info.target] = abspath
                        logger.info('Label identified (by name) for %s' %
                                     info.linkname, abspath)
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

            parent_root = root.rpartition('/')[0]
            local_collection_csv_prefix = f'{root}/collection'
            parent_collection_csv_prefix = f'{parent_root}/collection'

            # Identify labels for files
            for basename in local_basenames:

                basename_uc = basename.upper()
                _, is_ext_exists, ext = basename_uc.rpartition('.')
                ext = f'.{ext}' if is_ext_exists else ''
                if ext in ('.XML', '.LBLX', '.FMT'):     # these can't have labels
                    continue

                abspath = os.path.join(root, basename)

                if abspath in label_dict:
                    logger.info('Label already found for %s' % abspath)
                    continue                    # label already found

                # linkinfo_dict: a dictionary with the abspath of a label file as the key
                # and a list of its corresponding files (LinkInfo objects) under file_name
                # tags as the value.
                # label_dict: a dictionary with the abspath of a file as the key and the
                # abspath of its corresponding label as the value.
                # At the current directory, if a file basename is in the list of a label's
                # (in same directory) file_name tags in linkinfo_dict, create an entry of
                # that file basename in label_dict. This will make sure the file is
                # pointing to its correct corresponding label.
                is_label_found = False
                for label_abspath, link_info_list in linkinfo_dict.items():

                    # if the label is not at the same directory, skip it.
                    if label_abspath not in local_labels_abspath:
                        continue

                    for info in link_info_list:
                        linktext = _linkshelf_common.link_text_of(info)
                        if linktext == basename and abspath not in label_dict:
                            label_dict[abspath] = label_abspath
                            logger.info('Label identified (by file_name tag) for %s' %
                                        linktext, label_abspath)
                            is_label_found = True
                            break
                    if is_label_found:
                        break

                # label found by searching linkinfo_dict
                if is_label_found:
                    continue

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
                lbl_ext = ('.XML', '.LBLX')
                label_guess_uc = [basename_uc.partition('.')[0] + ext for ext in lbl_ext]

                obvious_label_basename = None
                for guess in label_guess_uc:
                    if guess in local_basenames_uc:
                        k = local_basenames_uc.index(guess)
                        obvious_label_basename = local_basenames[k]
                        break

                if not obvious_label_basename:
                    obvious_label_basename = ''

                # Simplest case...
                if obvious_label_basename in candidates:
                    if not label_is_required:
                        logger.debug('Unnecessary label found', abspath, force=True)

                    label_abspath = os.path.join(root, obvious_label_basename)
                    label_dict[abspath] = label_abspath
                    logger.info('Label found for %s' % abspath, label_abspath)
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

                # Before raising an error, check this:
                # For files like errata.txt, or checksum files that don't exist in the
                # label nor exist in the csv, they are not part of the archive, so they
                # don't have labels
                is_basename_in_csv = False
                logger.info('Check if %s is in the collection csv' % basename)
                for col_abspath, csv_basenames in collection_basename_dict.items():
                    if ((col_abspath.startswith(parent_collection_csv_prefix) or
                         col_abspath.startswith(local_collection_csv_prefix)) and
                            basename.rpartition('.')[0] in csv_basenames):
                        is_basename_in_csv = True
                        break

                if not is_basename_in_csv:
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
    """Return the bundle directories one command-line path names.

    This is the specification's ``expand_target``, and it exists to supply the
    specification to the shared expansion: ``_common.run_main()`` calls ``expand_target``
    with the PdsFile and the path alone, so the three-argument shared function cannot be
    named directly. It is the reason both link shelf tools carry a function of this name
    that does nothing else.

    Parameters:
        pdsf: The PdsFile the command-line path resolved to.
        path (str): The absolute path it resolved to, for the rejection messages.

    Returns:
        list: The bundle directories to shelve, which is a bundle set's directory
        children, the path itself if it is a directory, and nothing otherwise.

    Raises:
        SystemExit: from ``sys.exit()`` inside ``_linkshelf_common.link_targets()``, with
            status 1 if the path names checksum files or archive files.
    """

    return _linkshelf_common.link_targets(SPEC, pdsf, path)

SPEC = _common.ToolSpec(
    progname='pds4linkshelf',
    logname=LOGNAME,
    pdsfile_cls=pdsfile.Pds4File,
    unit='bundle',
    holdings_sentinel='/pds4-holdings/',
    index_ext='.csv',
    file_log_level='normal',
    description=_linkshelf_common.LINKSHELF_DESCRIPTION,
    task_help=_linkshelf_common.LINKSHELF_TASK_HELP,
    positional_help=_linkshelf_common.LINKSHELF_POSITIONAL_HELP,
    log_path_method=_shelf_common.UNIT_LOG_PATH_METHOD,
    log_suffix='_links',
    expand_target=link_targets,
    handler_factories=(pdslogger.warning_handler, pdslogger.error_handler),
    generate_links=generate_links,
    link_target_regex=TARGET_REGEX1)

TASKS = _linkshelf_common.link_tasks(SPEC)

# The task functions, under the names this module carries them as a library.
# Each is the shared task with this tool's spec bound in.
initialize = TASKS['initialize']
reinitialize = TASKS['reinitialize']
validate = TASKS['validate']
repair = TASKS['repair']
update = TASKS['update']

def main():
    """Run the tool: hand this module's specification and tasks to the generic driver.

    This is the ``pds4linkshelf`` console script's entry point. It does not return: the
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
