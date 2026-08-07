#!/usr/bin/env python3
################################################################################
# # pds4linkshelf.py library and main program
#
# Syntax:
#   pds4linkshelf.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

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
    """Generate a dictionary keyed by the absolute file path for files in the
    given directory tree, which must correspond to a bundle.

    Keys ending in .XML, .CAT, .FMT, .SFD return a list of tuples
        (recno, link, target)
    for each link found. Here,
        recno = record number in file;
        link = the text of the link;
        target = absolute path to the target of the link.

    Other keys return a single string, which indicates the absolute path to the
    label file describing this file.

    Unlabeled files not ending in .XML, .CAT or .TXT return an empty string.

    Also return the latest modification date among all the files checked.
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
#
# progname is 'pdslinkshelf', not this module's name: the tool announces itself,
# names its log directory and titles its --help output that way, and every one of
# those is part of what a run looks like today.
################################################################################

def link_targets(pdsf, path):
    """Return the bundle directories one command-line path names."""

    return _linkshelf_common.link_targets(SPEC, pdsf, path)

SPEC = _common.ToolSpec(
    progname='pdslinkshelf',
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

def main():
    _common.run_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
