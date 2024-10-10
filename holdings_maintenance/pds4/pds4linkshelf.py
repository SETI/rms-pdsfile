#!/usr/bin/env python3
################################################################################
# # pdslinkshelf.py library and main program
#
# Syntax:
#   pdslinkshelf.py --task path [path ...]
#
# Enter the --help option to see more information.
################################################################################

import argparse
import datetime
import glob
import os
import pickle
import re
import shutil
import sys

import pdslogger
import pdsfile
import translator

LOGNAME = 'pds.validation.links'
LOGROOT_ENV = 'PDS_LOG_ROOT'

# Holds log file directories temporarily, used by move_old_links()
LOGDIRS = []

REPAIRS = translator.TranslatorByRegex([])

KNOWN_MISSING_LABELS = translator.TranslatorByRegex([])

# Match pattern for any file name, but possibly things that are not file names
PATTERN = r'\'?\"?([A-Z0-9][-\w]*\.[A-Z0-9][-\w\.]*)\'?\"?'

# Match pattern for the file name in anything of the form "keyword = filename"
TARGET_REGEX1 = re.compile(r'^ *\^?\w+ *= *\(?\{? *' + PATTERN, re.I)

# Match pattern for a file name on a line by itself
TARGET_REGEX2 = re.compile(r'^ *,? *' + PATTERN, re.I)

# Match pattern for one or more file names embedded in a row of a text file.
# A file name begins with a letter, followed by any number of letters, digits,
# underscore or dash. Unless the name is "Makefile", it must have one or more
# extensions, each containing one or more characters. It can also have any
# number of directory prefixes separate by slashes.

LINK_REGEX = re.compile(r'(?:|.*?[^/@\w\.])/?(?:\.\./)*(([A-Z0-9][-\w]+/)*' +
                        r'(makefile\.?|[A-Z0-9][\w-]*(\.[\w-]+)+))', re.I)

EXTS_WO_LABELS = set(['.XML', '.CAT', '.FMT', '.SFD'])

################################################################################

class LinkInfo(object):
    """Used internally to describe a link within a specified record of a file.
    """

    def __init__(self, recno, linkname, is_target):

        self.recno = recno          # record number
        self.linktext = linkname    # substring within this record that looks
                                    # like a link.
        self.linkname = linkname    # link text after possible repair for known
                                    # errors.
        self.is_target = is_target  # True if, based on the local context, this
                                    # might be a target of a label file
        self.target = ''            # abspath to target of link, if any.
                                    # If not blank, this file must exist.

    def remove_path(self):
        """Remove any leading directory path from this LinkInfo object."""

        if '/' in self.linktext:
            self.linktext = self.linktext.rpartition('/')[2]
            self.linkname = self.linktext

    def __str__(self):
        return ('%d %s %s %s' % (self.recno, self.linktext, str(self.is_target),
                                 self.target or '[' + self.linkname + ']'))

def generate_links(dirpath, old_links={},
                   limits={'info':-1, 'debug':500, 'ds_store':10}, logger=None):
    """Generate a dictionary keyed by the absolute file path for files in the
    given directory tree, which must correspond to a volume.

    Keys ending in .XML, .CAT and .TXT return a list of tuples
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

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds4File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    logger.open('Finding link shelf files', dirpath, limits)

    try:

      linkinfo_dict = old_links.copy()      # abspath: list of LinkInfo objects
      label_dict = {k:v for k,v in old_links.items() if isinstance(v,str)}
                                            # abspath: label for this file
      abspaths = []                         # list of all abspaths

      latest_mtime = 0.

      # Walk the directory tree, one subdirectory "root" at a time...
      for (root, dirs, files) in os.walk(dirpath):

        # skip ring_models dirctory
        # if 'ring_models' in root:
        #     continue

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

            # Only check XML, CAT, TXT, etc.
            ext = basename_uc[-4:] if len(basename) >= 4 else ''
            if ext not in EXTS_WO_LABELS:
                continue

            # Get list of link info for all possible linked filenames
            logger.debug('*** REVIEWING', abspath)
            linkinfo_list = read_links(abspath, logger=logger)

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
                        nonlocal_target = locate_link_with_path(abspath,
                                                                info.linkname)
                    else:
                        nonlocal_target = locate_nonlocal_link(abspath,
                                                               info.linkname)

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
                if ext != '.XML':       # nope
                    continue

                # If names match up to '.XML', then yes
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
            if ext in (".XML", ".FMT"):     # these can't have labels
                continue

            abspath = os.path.join(root, basename)

            # linkinfo_dict: a dictionary with the abspath of a label file as the key and
            # a list of its corresponding files (LinkInfo objects) under file_name tags as
            # the value.
            # label_dict: a dictionary with the abspath of a file as the key and the
            # abspath of its corresponding label as the value.
            # At the current directory, if a file basename is in the list of a label's
            # (in same directory) file_name tags in linkinfo_dict, create an entry of
            # that file basename in label_dict. This will make sure the file is pointing
            # to it's correct corresponding label.
            for label_abspath, link_info_list in linkinfo_dict.items():
                for info in link_info_list:
                    if info.linktext == basename and abspath not in label_dict:
                        label_dict[abspath] = label_abspath
                        break

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
            label_guess_uc = basename_uc.partition('.')[0] + '.XML'
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
                new_list = []
                for item in values:
                  if isinstance(item, LinkInfo):
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

def read_links(abspath, logger=None):
    """Return a list of LinkInfo objects for anything linked or labeled by this
    file.
    """

    with open(abspath, 'r', encoding='latin-1') as f:
        recs = f.readlines()

    links = []
    multiple_targets = False
    for recno,rec in enumerate(recs):

        while True:

            # Search for the target of a link
            is_target = True
            matchobj = TARGET_REGEX1.match(rec)
            if matchobj:
                subrec = rec[:matchobj.end()]
                if '(' in subrec or '{' in subrec:
                    multiple_targets = True

            # ... on the same line or the next line
            elif multiple_targets:
                matchobj = TARGET_REGEX2.match(rec)

            # If not found, search for any other referenced file name or path
            if not matchobj:
                if ')' in rec or '}' in rec:
                    multiple_targets = False

                is_target = False
                matchobj = LINK_REGEX.match(rec)
                if matchobj:
                    multiple_targets = False

            # No more matches in this record
            if not matchobj:
                break

            # if 'u0_kao_91cm_734nm_ring_beta_ingress_sqw' in abspath:
            #     print('readdddd')
            #     print(rec)
            #     print(matchobj.group(1))


            linktext = matchobj.group(1)
            links.append(LinkInfo(recno, linktext, is_target))

            rec = rec[matchobj.end():]

    return links

def locate_nonlocal_link(abspath, filename):
    """Return the absolute path associated with a link in a PDS file. This is
    done by searching up the tree and also by looking inside the LABEL,
    CATALOG and INCLUDE directories if they exist."""

    filename_uc = filename.upper()

    parts = abspath.split('/')[:-1]

    # parts are [..., 'holdings', 'volumes', volset, volname, ...]
    # Therefore, if 'holdings' is in parts[:-3], then there's a volname in this
    # path.
    while 'pds4-holdings' in parts[:-3]:
        testpath = '/'.join(parts)
        basenames = os.listdir(testpath)
        basenames_uc = [b.upper() for b in basenames]
        try:
            k = basenames_uc.index(filename_uc)
            return testpath + '/' + basenames[k]
        except ValueError:
            pass

        for dirname in ['LABEL', 'CATALOG', 'INCLUDE', 'INDEX', 'DOCUMENT',
                        'DATA', 'CALIB', 'EXTRAS', 'SOFTWARE']:
            try:
                k = basenames_uc.index(dirname)
                subnames = os.listdir(testpath + '/' + basenames[k])
                subupper = [s.upper() for s in subnames]
                try:
                    kk = subupper.index(filename_uc)
                    return testpath + '/' + basenames[k] + '/' + subnames[kk]
                except ValueError:
                    pass
            except ValueError:
                pass

        parts = parts[:-1]

    return ''

def locate_link_with_path(abspath, filename):
    """Return the absolute path associated with a link that contains a leading
    directory path.
    """

    parts = filename.split('/')
    link_path = locate_nonlocal_link(abspath, parts[0])
    if not link_path:
        return ''

    for part in parts[1:]:
        basenames = os.listdir(link_path)
        if part in basenames:
            link_path += '/' + part
        else:
            basenames_uc = [b.upper() for b in basenames]
            part_uc = part.upper()
            if part_uc in basenames_uc:
                k = basenames_uc.index(part_uc)
                link_path += '/' + basenames[k]
            else:
                return ''

    return link_path

################################################################################

def load_links(dirpath, limits={}, logger=None):
    """Load link dictionary from a shelf file, converting interior paths to
    absolute paths."""

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds4File.from_abspath(dirpath)

    dirpath_ = dirpath.rstrip('/') + '/'

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    logger.open('Reading link shelf file for', dirpath, limits)

    try:
        (link_path, lskip) = pdsdir.shelf_path_and_lskip('link')
        prefix_ = pdsdir.volume_abspath() + '/'

        logger.info('Link shelf file', link_path)

        if not os.path.exists(link_path):
            raise IOError('File not found: ' + link_path)

        # Read the shelf file and convert to a dictionary
        with open(link_path, 'rb') as f:
            interior_dict = pickle.load(f)

        # Convert interior paths to absolute paths
        link_dict = {}
        for (key, values) in interior_dict.items():
            long_key = dirpath_ + key

            if isinstance(values, list):
                new_list = []
                for (recno, basename, interior_path) in values:
                    abspath = dirpath_ + str(interior_path)
                    if '../' in abspath:
                        abspath = os.path.abspath(abspath)

                    new_list.append((recno, str(basename), abspath))

                link_dict[long_key] = new_list
            else:
                values = str(values)
                if values == '':
                    link_dict[long_key] = ''
                else:
                    link_dict[long_key] = dirpath_ + values

        return link_dict

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def write_linkdict(dirpath, link_dict, limits={}, logger=None):
    """Write a new link shelf file for a directory tree."""

    # Initialize
    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds4File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    logger.open('Writing link shelf file for', dirpath, limits)

    try:
        (link_path, lskip) = pdsdir.shelf_path_and_lskip('link')
        logger.info('Link shelf file', link_path)

        # Create a dictionary using interior paths instead of absolute paths
        interior_dict = {}
        prefix = (dirpath + '/')[:lskip]
        for (key, values) in link_dict.items():
            if isinstance(values, list):
                new_list = []
                for (basename, recno, link_abspath) in values:
                    if link_abspath[:lskip] == prefix:
                        new_list.append((basename, recno, link_abspath[lskip:]))
                    else:      # link outside this volume
                        link = pdsfile.Pds4File.from_abspath(link_abspath)
                        if (link.category_ == pdsdir.category_ and
                            link.bundleset == pdsdir.bundleset and
                            link.suffix == pdsdir.suffix):
                            link_relpath = '../' + link.bundlename_ + link.interior
                        elif link.category_ == pdsdir.category_:
                            link_relpath = ('../../' + link.bundleset_ +
                                            link.bundlename_ + link.interior)
                        else:
                            link_relpath = ('../../../' + link.category_ +
                                            link.bundleset_ +
                                            link.bundlename_ + link.interior)
                        new_list.append((basename, recno, link_relpath))

                interior_dict[key[lskip:]] = new_list
            else:
                interior_dict[key[lskip:]] = values[lskip:]

        # Create parent directory if necessary
        parent = os.path.split(link_path)[0]
        if not os.path.exists(parent):
            logger.normal('Creating directory', parent)
            os.makedirs(parent)

        # Write the shelf
        with open(link_path, 'wb') as f:
            pickle.dump(interior_dict, f)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

    logger.open('Writing Python dictionary', dirpath)
    try:
        # Determine the maximum length of the file path and basename
        len_key = 0
        len_base = 0
        for (key, value) in interior_dict.items():
            len_key = max(len_key, len(key))
            if isinstance(value, list):
                tuples = value
                for (recno, basename, interior_path) in tuples:
                    len_base = max(len_base, len(basename))

        len_key = min(len_key, 60)

        # Write the python dictionary version
        python_path = link_path.rpartition('.')[0] + '.py'
        name = os.path.basename(python_path)
        parts = name.split('_')
        name = '_'.join(parts[:2]) + '_links'
        keys = list(interior_dict.keys())
        keys.sort()

        with open(python_path, 'w', encoding='latin-1') as f:
            f.write(name + ' = {\n')
            for valtype in (list, str):
              for key in keys:
                if not isinstance(interior_dict[key], valtype): continue

                f.write('  "%s"' % key)
                if len(key) < len_key:
                    f.write((len_key - len(key)) * ' ')
                f.write(': ')
                tuple_indent = max(len(key),len_key) + 7

                values = interior_dict[key]
                if isinstance(values, str):
                    f.write('"%s",\n' % values)
                elif len(values) == 0:
                    f.write('[],\n')
                else:
                    f.write('[')
                    for k in range(len(values)):
                        (recno, basename, interior_path) = values[k]
                        f.write('(%4d, ' % recno)
                        f.write('"%s, ' % (basename + '"' +
                                           (len_base-len(basename)) * ' '))
                        f.write('"%s")' % interior_path)

                        if k < len(values) - 1:
                            f.write(',\n' + tuple_indent * ' ')
                        else:
                            f.write('],\n')

            f.write('}\n\n')

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        _ = logger.close()

################################################################################

def validate_links(dirpath, dirdict, shelfdict, limits={}, logger=None):

    dirpath = os.path.abspath(dirpath)
    pdsdir = pdsfile.Pds4File.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    logger.replace_root(pdsdir.root_)
    logger.open('Validating link shelf file for', dirpath, limits=limits)

    try:
        keys = list(dirdict.keys())
        for key in keys:
            if key in shelfdict:
                dirinfo = dirdict[key]
                shelfinfo = shelfdict[key]

                if type(dirinfo) == list:
                    dirinfo.sort()

                if type(shelfinfo) == list:
                    shelfinfo.sort()

                if dirinfo != shelfinfo:
                    logger.error('Link target mismatch', key)

                del shelfdict[key]
                del dirdict[key]

        keys = list(dirdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Missing link shelf file entry for', key)

        keys = list(shelfdict.keys())
        keys.sort()
        for key in keys:
            logger.error('Link shelf file entry found for missing file', key)

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        raise

    finally:
        return logger.close()

################################################################################

def move_old_links(shelf_file, logger=None):
    """Move a file to the /logs/ directory tree and append a time tag."""

    if not os.path.exists(shelf_file): return

    shelf_basename = os.path.basename(shelf_file)
    (shelf_prefix, shelf_ext) = os.path.splitext(shelf_basename)

    if logger is None:
        logger = pdslogger.PdsLogger.get_logger(LOGNAME)

    from_logged = False
    for log_dir in LOGDIRS:
        dest_template = log_dir + '/' + shelf_prefix + '_v???' + shelf_ext
        version_paths = glob.glob(dest_template)

        max_version = 0
        lskip = len(shelf_ext)
        for version_path in version_paths:
            version = int(version_path[-lskip-3:-lskip])
            max_version = max(max_version, version)

        new_version = max_version + 1
        dest = dest_template.replace('???', '%03d' % new_version)
        shutil.copy(shelf_file, dest)

        if not from_logged:
            logger.info('Link shelf file moved from: ' + shelf_file)
            from_logged = True

        logger.info('Link shelf file moved to ' + dest)

        python_src = shelf_file.rpartition('.')[0] + '.py'
        python_dest = dest.rpartition('.')[0] + '.py'
        shutil.copy(python_src, python_dest)

        pickle_src = shelf_file.rpartition('.')[0] + '.pickle'
        pickle_dest = dest.rpartition('.')[0] + '.pickle'
        shutil.copy(pickle_src, pickle_dest)

################################################################################
# Simplified functions to perform tasks
################################################################################

def initialize(pdsdir, logger=None):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file does not exist
    if os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Link shelf file already exists', link_path)
        return

    # Generate link info
    (link_dict, _) = generate_links(pdsdir.abspath, logger=logger)

    # Move old file if necessary
    if os.path.exists(link_path):
        move_old_links(link_path, logger=logger)

    # Save link files
    write_linkdict(pdsdir.abspath, link_dict, logger=logger)

def reinitialize(pdsdir, logger=None):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Warn if shelf file does not exist
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warn('Link shelf file does not exist; initializing', link_path)
        initialize(pdsdir, logger=logger)
        return

    # Generate link info
    (link_dict, _) = generate_links(pdsdir.abspath, logger=logger)

    # Move old file if necessary
    if os.path.exists(link_path):
        move_old_links(link_path, logger=logger)

    # Save link files
    write_linkdict(pdsdir.abspath, link_dict, logger=logger)

def validate(pdsdir, logger=None):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.error('Link shelf file does not exist', link_path)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger)

    # Generate link dict
    (dir_linkdict, _) = generate_links(pdsdir.abspath, logger=logger)

    # Validate
    validate_links(pdsdir.abspath, dir_linkdict, shelf_linkdict, logger=logger)

def repair(pdsdir, logger=None):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warn('Link shelf file does not exist; initializing', link_path)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger)

    # Generate link dict
    (dir_linkdict, latest_mtime) = generate_links(pdsdir.abspath, logger=logger)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)

        link_pypath = link_path.replace('.pickle', '.py')
        link_mtime = min(os.path.getmtime(link_path),
                         os.path.getmtime(link_pypath))
        if latest_mtime > link_mtime:
            logger.info('!!! Link shelf file content is up to date',
                        link_path, force=True)

            dt = datetime.datetime.fromtimestamp(latest_mtime)
            logger.info('!!! Latest holdings file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            dt = datetime.datetime.fromtimestamp(link_mtime)
            logger.info('!!! Link shelf file modification date',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)

            delta = latest_mtime - link_mtime
            if delta >= 86400/10:
                logger.info('!!! Link shelf file is out of date %.1f days' %
                            (delta / 86400.), force=True)
            else:
                logger.info('!!! Link shelf file is out of date %.1f minutes' %
                            (delta / 60.), force=True)

            dt = datetime.datetime.now()
            os.utime(link_path)
            os.utime(link_pypath)
            logger.info('!!! Time tag on link shelf files set to',
                        dt.strftime('%Y-%m-%dT%H-%M-%S'), force=True)
        else:
            logger.info(f'!!! Link shelf file is up to date; repair canceled',
                        link_path, force=True)
        return

    # Move files and write new links
    move_old_links(link_path, logger=logger)
    write_linkdict(pdsdir.abspath, dir_linkdict, logger=logger)

def update(pdsdir,  logger=None):

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure link shelf file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.warn('Link shelf file does not exist; initializing', link_path)
        initialize(pdsdir, logger=logger)
        return

    # Read link shelf file
    shelf_linkdict = load_links(pdsdir.abspath, logger=logger)

    # Generate link dict
    (dir_linkdict,
     latest_mtime) = generate_links(pdsdir.abspath, shelf_linkdict,
                                                    logger=logger)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.info('!!! Link shelf file content is complete; update canceled',
                    link_path, force=True)
        return

    # Move files and write new links
    move_old_links(link_path, logger=logger)
    write_linkdict(pdsdir.abspath, dir_linkdict, logger=logger)

################################################################################

def main():

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdslinkshelf: Create, maintain and validate shelves of '  +
                    'links between files.')

    parser.add_argument('--initialize', '--init', const='initialize',
                        default='', action='store_const', dest='task',
                        help='Create a link shelf file for a volume. Abort '   +
                             'if the checksum file already exists.')

    parser.add_argument('--reinitialize', '--reinit', const='reinitialize',
                        default='', action='store_const', dest='task',
                        help='Create a link shelf file for a volume. Replace ' +
                             'the file if it already exists.')

    parser.add_argument('--validate', const='validate',
                        default='', action='store_const', dest='task',
                        help='Validate every link in a volume directory tree ' +
                             'against its link shelf file.')

    parser.add_argument('--repair', const='repair',
                        default='', action='store_const', dest='task',
                        help='Validate every link in a volume directory tree ' +
                             'against its link shelf file. If any '            +
                             'disagreement  is found, replace the shelf '      +
                             'file; otherwise leave it unchanged. If any of '  +
                             'the files checked are newer than the link shelf '+
                             'file, update shelf file\'s modification date')

    parser.add_argument('--update', const='update',
                        default='', action='store_const', dest='task',
                        help='Search a directory for any new files and add '   +
                             'their links to the link shelf file. Links of '   +
                             'pre-existing files are not checked.')

    parser.add_argument('bundle', nargs='+', type=str,
                        help='The path to the root directory of a bundle.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdslinkshelf" subdirectory of each log root '   +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    if not args.task:
        print('pdslinkshelf error: Missing task')
        sys.exit(1)

    status = 0

    # Define the logging directory
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.Pds4File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdslinkshelf')
        warning_handler = pdslogger.warning_handler(path)
        logger.add_handler(warning_handler)

        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of file paths before logging
    paths = []
    for path in args.bundle:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.Pds4File.from_abspath(path)

        if pdsf.checksums_:
            print('No link shelf files for checksum files: ' + path)
            sys.exit(1)

        if pdsf.archives_:
            print('No link shelf files for archive files: ' + path)
            sys.exit(1)

        if pdsf.is_bundleset_dir:
            paths += [os.path.join(path, c) for c in pdsf.childnames]

        else:
            paths.append(os.path.abspath(path))

    # Loop through tuples...
    logger.open(' '.join(sys.argv))
    try:
        for path in paths:

            pdsdir = pdsfile.Pds4File.from_abspath(path)
            # skip volset-level readme files and *_support dirctiory
            # if not pdsdir.isdir or '_support' in pdsdir.abspath:
            if not pdsdir.isdir:
                continue

            # Save logs in up to two places
            logfiles = set([pdsdir.log_path_for_bundle('_links',
                                                       task=args.task,
                                                       dir='pdslinkshelf'),
                            pdsdir.log_path_for_bundle('_links',
                                                       task=args.task,
                                                       dir='pdslinkshelf',
                                                       place='parallel')])

            # Create all the handlers for this level in the logger
            local_handlers = []
            LOGDIRS = []            # used by move_old_links()
            for logfile in logfiles:
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]
                LOGDIRS.append(os.path.split(logfile)[0])

                # These handlers are only used if they don't already exist
                warning_handler = pdslogger.warning_handler(logdir)
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [warning_handler, error_handler]

            # Open the next level of the log
            if len(paths) > 1:
                logger.blankline()

            logger.open('Task "' + args.task + '" for', path,
                        handler=local_handlers)

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                if args.task == 'initialize':
                    initialize(pdsdir)

                elif args.task == 'reinitialize':
                    reinitialize(pdsdir)

                elif args.task == 'validate':
                    validate(pdsdir)

                elif args.task == 'repair':
                    repair(pdsdir)

                else:       # update
                    update(pdsdir)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

            finally:
                _ = logger.close()

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, warnings, tests) = logger.close()
        if fatal or errors: status = 1

    sys.exit(status)

if __name__ == '__main__':
    main()
