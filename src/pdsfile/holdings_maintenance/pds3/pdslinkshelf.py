#!/usr/bin/env python3
################################################################################
# # pdslinkshelf.py library and main program
#
# Syntax:
#   pdslinkshelf.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

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
    """Generate a dictionary keyed by the absolute file path for files in the
    given directory tree, which must correspond to a volume.

    Keys ending in .LBL, .CAT and .TXT return a list of tuples
        (recno, link, target)
    for each link found. Here,
        recno = record number in file;
        link = the text of the link;
        target = absolute path to the target of the link.

    Other keys return a single string, which indicates the absolute path to the
    label file describing this file.

    Unlabeled files not ending in .LBL, .CAT or .TXT return an empty string.

    Also return the latest modification date among all the files checked.
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
    """Return the volume directories one command-line path names."""

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
    _common.run_main(SPEC, TASKS, sys.argv)

if __name__ == '__main__':
    main()
