##########################################################################################
# pdsfile/holdings_maintenance/_linkshelf_common.py
#
# What the two link shelf tools share.
#
# These shelve, for every file in a unit, either the list of links found inside it or
# the label that describes it. Finding the links is where the two flavors differ --
# a PDS3 label and a PDS4 label say different things in different syntax -- so each
# tool keeps its own generate_links() and names it in its spec; everything that
# reads, writes, compares or drives is here. The driver is _common.run_main.
##########################################################################################

import datetime
import functools
import os
import pickle
import re
import sys

import pdslogger

from pdsfile.holdings_maintenance import _shelf_common

LINKSHELF_DESCRIPTION = ('{progname}: Create, maintain and validate shelves of links '
                         'between files.')

LINKSHELF_TASK_HELP = {
    'initialize': 'Create a link shelf file for a {unit}. Abort if the checksum file '
                  'already exists.',
    'reinitialize': 'Create a link shelf file for a {unit}. Replace the file if it '
                    'already exists.',
    'validate': 'Validate every link in a {unit} directory tree against its link shelf '
                'file.',
    'repair': 'Validate every link in a {unit} directory tree against its link shelf '
              'file. If any disagreement  is found, replace the shelf file; otherwise '
              'leave it unchanged. If any of the files checked are newer than the link '
              "shelf file, update shelf file's modification date",
    'update': 'Search a directory for any new files and add their links to the link '
              'shelf file. Links of pre-existing files are not checked.',
}

LINKSHELF_POSITIONAL_HELP = 'The path to the root directory of a {unit}.'

# Default limits
GENERATE_LINKS_LIMITS = {'debug':200, 'ds_store':10}
LOAD_LINKS_LIMITS = {}
WRITE_LINKDICT_LIMITS = {}
VALIDATE_LINKS_LIMITS = {}

# Match pattern for any file name, but possibly things that are not file names. Each
# tool builds its own "this label points at that file" pattern around this one and
# names it in its spec, because what that looks like is what a PDS3 label and a PDS4
# label most differ about.
LINK_NAME_PATTERN = r'\'?\"?([A-Z0-9][-\w]*\.[A-Z0-9][-\w\.]*)\'?\"?'

# Match pattern for a file name on a line by itself, which is how a label continues a
# list of targets onto the following records
LINK_CONTINUATION_REGEX = re.compile(r'^ *,? *' + LINK_NAME_PATTERN, re.I)

# Match pattern for one or more file names embedded in a row of a text file.
# A file name begins with a letter, followed by any number of letters, digits,
# underscore or dash. Unless the name is "Makefile", it must have one or more
# extensions, each containing one or more characters. It can also have any
# number of directory prefixes separate by slashes.

LINK_REGEX = re.compile(r'(?:|.*?[^/@\w\.])/?(?:\.\./)*(([A-Z0-9][-\w]+/)*' +
                        r'(makefile\.?|[A-Z0-9][\w-]*(\.[\w-]+)+))', re.I)


class LinkInfo:
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
        return (f'{self.recno:d} {self.linktext} {self.is_target!s} '
                + (self.target or '[' + self.linkname + ']'))


def link_text_of(info):
    """Return the link text of one shelved link, however it is carried.

    A link generated in this run is a LinkInfo object; one read back from an
    existing shelf is the plain tuple that was pickled, (recno, linktext, target).
    An update sees both in the same dictionary.

    Args:
        info: A LinkInfo or a (recno, linktext, target) tuple.

    Returns:
        str: The text of the link.
    """

    if isinstance(info, LinkInfo):
        return info.linktext

    return info[1]


def read_links(spec, abspath, logger=None):
    """Return a list of LinkInfo objects for anything linked or labeled by this
    file.
    """

    with open(abspath, encoding='latin-1') as f:
        recs = f.readlines()

    links = []
    multiple_targets = False
    for recno,rec in enumerate(recs):

        while True:

            # Search for the target of a link
            is_target = True
            matchobj = spec.link_target_regex.match(rec)
            if matchobj:
                subrec = rec[:matchobj.end()]
                if '(' in subrec or '{' in subrec:
                    multiple_targets = True

            # ... on the same line or the next line
            elif multiple_targets:
                matchobj = LINK_CONTINUATION_REGEX.match(rec)

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

            linktext = matchobj.group(1)
            links.append(LinkInfo(recno, linktext, is_target))

            rec = rec[matchobj.end():]

    return links


def locate_nonlocal_link(spec, abspath, filename):
    """Return the absolute path associated with a link in a PDS file. This is
    done by searching up the tree and also by looking inside the LABEL,
    CATALOG and INCLUDE directories if they exist."""

    filename_uc = filename.upper()

    parts = abspath.split('/')[:-1]

    # parts are [..., holdings, category, unit set, unit, ...]
    # Therefore, if the holdings directory is in parts[:-3], then there's a unit
    # name in this path.
    holdings = spec.holdings_sentinel.strip('/')
    while holdings in parts[:-3]:
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


def locate_link_with_path(spec, abspath, filename):
    """Return the absolute path associated with a link that contains a leading
    directory path.
    """

    parts = filename.split('/')
    link_path = locate_nonlocal_link(spec, abspath, parts[0])
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


def load_links(spec, dirpath, *, logger=None, limits=None):
    """Load link dictionary from a shelf file, converting interior paths to
    absolute paths."""

    if limits is None:
        limits = {}

    dirpath = os.path.abspath(dirpath)
    pdsdir = spec.pdsfile_cls.from_abspath(dirpath)

    dirpath_ = dirpath.rstrip('/') + '/'

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsdir.root_)

    merged_limits = LOAD_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Reading link shelf file for', dirpath, limits=merged_limits)

    try:
        (link_path, _lskip) = pdsdir.shelf_path_and_lskip('link')

        logger.info('Link shelf file', link_path)

        if not os.path.exists(link_path):
            raise OSError('File not found: ' + link_path)

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


def write_linkdict(spec, dirpath, link_dict, *, logger=None, limits=None):
    """Write a new link shelf file for a directory tree."""

    if limits is None:
        limits = {}

    # Initialize
    dirpath = os.path.abspath(dirpath)
    pdsdir = spec.pdsfile_cls.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsdir.root_)
    file_log = getattr(logger, spec.file_log_level)

    merged_limits = WRITE_LINKDICT_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Writing link shelf file for', dirpath, limits=merged_limits)

    try:
        (link_path, lskip) = pdsdir.shelf_path_and_lskip('link')
        logger.info('Link shelf file', link_path)

        # Create a dictionary using interior paths instead of absolute paths
        interior_dict = {}
        prefix = (dirpath + '/')[:lskip]
        for (key, values) in link_dict.items():
            if isinstance(values, list):
                new_list = []
                for (recno, basename, link_abspath) in values:
                    if link_abspath[:lskip] == prefix:
                        new_list.append((recno, basename, link_abspath[lskip:]))
                    else:      # link outside this unit
                        link = spec.pdsfile_cls.from_abspath(link_abspath)
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
                        new_list.append((recno, basename, link_relpath))

                interior_dict[key[lskip:]] = new_list
            else:
                interior_dict[key[lskip:]] = values[lskip:]

        # Create parent directory if necessary
        parent = os.path.split(link_path)[0]
        if not os.path.exists(parent):
            file_log('Creating directory', parent)
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
                for (_recno, basename, _interior_path) in tuples:
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
                    if not isinstance(interior_dict[key], valtype):
                        continue

                    f.write(f'  "{key}"')
                    if len(key) < len_key:
                        f.write((len_key - len(key)) * ' ')
                    f.write(': ')
                    tuple_indent = max(len(key),len_key) + 7

                    values = interior_dict[key]
                    if isinstance(values, str):
                        f.write(f'"{values}",\n')
                    elif len(values) == 0:
                        f.write('[],\n')
                    else:
                        f.write('[')
                        for k in range(len(values)):
                            (recno, basename, interior_path) = values[k]
                            f.write(f'({recno:4d}, ')
                            f.write('"%s, ' % (basename + '"' +
                                               (len_base-len(basename)) * ' '))
                            f.write(f'"{interior_path}")')

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


def validate_links(spec, dirpath, dirdict, shelfdict, *, logger=None, limits=None):
    """Report every way the links found in a unit and the shelved links disagree.

    Both dictionaries are emptied as it goes: a key present in both is compared and
    then deleted from both, so what is left in each at the end is what the other
    lacks, and that is what the last two loops report. A caller that still needs
    either dictionary afterwards has to pass a copy.

    Args:
        spec: The tool's ToolSpec.
        dirpath: The unit the links were found in.
        dirdict: The links a fresh scan found. Emptied.
        shelfdict: The links the shelf file holds. Emptied.
        logger: The logger to report through. Defaults to the tool's own.
        limits: Message limits for this scope, merged over the defaults.

    Returns:
        tuple: What closing this scope's log level reported.
    """

    if limits is None:
        limits = {}

    dirpath = os.path.abspath(dirpath)
    pdsdir = spec.pdsfile_cls.from_abspath(dirpath)

    logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
    logger.replace_root(pdsdir.root_)

    merged_limits = VALIDATE_LINKS_LIMITS.copy()
    merged_limits.update(limits)
    logger.open('Validating link shelf file for', dirpath, limits=merged_limits)

    try:
        keys = list(dirdict.keys())
        for key in keys:
            if key in shelfdict:
                dirinfo = dirdict[key]
                shelfinfo = shelfdict[key]

                if isinstance(dirinfo, list):
                    dirinfo.sort()

                if isinstance(shelfinfo, list):
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
        result = logger.close()

    return result


##########################################################################################
# Link shelf tasks
##########################################################################################

def link_initialize(spec, pdsdir, *, logger=None, limits=None):
    """Shelve one unit's links, refusing to replace a shelf that is already there."""

    if limits is None:
        limits = {}

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file does not exist
    if os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.error('Link shelf file already exists', link_path)
        return

    # Generate link info
    (link_dict, _) = spec.generate_links(pdsdir.abspath, logger=logger, limits=limits)

    # Save link files
    write_linkdict(spec, pdsdir.abspath, link_dict, logger=logger, limits=limits)


def link_reinitialize(spec, pdsdir, *, logger=None, limits=None):
    """Shelve one unit's links, versioning and replacing whatever shelf is there."""

    if limits is None:
        limits = {}

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Warn if shelf file does not exist
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.warning('Link shelf file does not exist; initializing', link_path)
        link_initialize(spec, pdsdir, logger=logger, limits=limits)
        return

    # Generate link info
    (link_dict, _) = spec.generate_links(pdsdir.abspath, logger=logger, limits=limits)

    # Move old file if necessary
    if os.path.exists(link_path):
        _shelf_common.move_old(link_path, _shelf_common.LINK_SHELF, logger=logger)

    # Save link files
    write_linkdict(spec, pdsdir.abspath, link_dict, logger=logger, limits=limits)


def link_validate(spec, pdsdir, *, logger=None, limits=None):
    """Report every way one unit's links and its shelf disagree."""

    if limits is None:
        limits = {}

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.error('Link shelf file does not exist', link_path)
        return

    # Read link shelf file
    shelf_linkdict = load_links(spec, pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict, _) = spec.generate_links(pdsdir.abspath, logger=logger,
                                            limits=limits)

    # Validate
    validate_links(spec, pdsdir.abspath, dir_linkdict, shelf_linkdict, logger=logger,
                   limits=limits)


def link_repair(spec, pdsdir, *, logger=None, limits=None):
    """Rewrite one unit's link shelf if it disagrees, or re-date it if it does not."""

    if limits is None:
        limits = {}

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.warning('Link shelf file does not exist; initializing', link_path)
        link_initialize(spec, pdsdir, logger=logger, limits=limits)
        return

    # Read link shelf file
    shelf_linkdict = load_links(spec, pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict, latest_mtime) = spec.generate_links(pdsdir.abspath, logger=logger,
                                                       limits=limits)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)

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
            logger.info('!!! Link shelf file is up to date; repair canceled',
                        link_path, force=True)
        return

    # Move files and write new links
    _shelf_common.move_old(link_path, _shelf_common.LINK_SHELF, logger=logger)
    write_linkdict(spec, pdsdir.abspath, dir_linkdict, logger=logger, limits=limits)


def link_update(spec, pdsdir, *, logger=None, limits=None):
    """Add the links of any file the shelf does not already carry."""

    if limits is None:
        limits = {}

    link_path = pdsdir.shelf_path_and_lskip('link')[0]

    # Make sure link shelf file exists
    if not os.path.exists(link_path):
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.warning('Link shelf file does not exist; initializing', link_path)
        link_initialize(spec, pdsdir, logger=logger, limits=limits)
        return

    # Read link shelf file
    shelf_linkdict = load_links(spec, pdsdir.abspath, logger=logger, limits=limits)

    # Generate link dict
    (dir_linkdict,
     _latest_mtime) = spec.generate_links(pdsdir.abspath, shelf_linkdict,
                                          logger=logger, limits=limits)

    # Compare
    canceled = (dir_linkdict == shelf_linkdict)
    if canceled:
        logger = logger or pdslogger.PdsLogger.get_logger(spec.logname)
        logger.info('!!! Link shelf file content is complete; update canceled',
                    link_path, force=True)
        return

    # Move files and write new links
    _shelf_common.move_old(link_path, _shelf_common.LINK_SHELF, logger=logger)
    write_linkdict(spec, pdsdir.abspath, dir_linkdict, logger=logger, limits=limits)


_LINK_TASKS = {'initialize': link_initialize,
               'reinitialize': link_reinitialize,
               'validate': link_validate,
               'repair': link_repair,
               'update': link_update}


def link_tasks(spec):
    """Return one tool's link shelf task table, with its spec bound into each task.

    Args:
        spec: The tool's ToolSpec.

    Returns:
        dict: The task functions, keyed by task name, each taking one unit.
    """

    return {name: functools.partial(task, spec) for name, task in _LINK_TASKS.items()}


def link_targets(spec, pdsf, path):
    """Return the unit directories one command-line path names.

    A unit set expands to the unit directories inside it; anything else that is not
    a directory is skipped, which is what leaves a unit set's readme file out.

    Args:
        spec: The tool's ToolSpec.
        pdsf: The PdsFile the path resolved to.
        path: The absolute path the command line resolved to, for the messages.

    Returns:
        list: The PdsFile objects to shelve.

    Raises:
        SystemExit: With status 1 if the path names checksum or archive files.
    """

    if pdsf.checksums_:
        print('No link shelf files for checksum files: ' + path)
        sys.exit(1)

    if pdsf.archives_:
        print('No link shelf files for archive files: ' + path)
        sys.exit(1)

    if pdsf.is_bundleset_dir:
        children = [pdsf.child(c) for c in pdsf.childnames]
        return [c for c in children if c.isdir]
                # "if c.isdir" is False for unit set level readme files

    return [pdsf] if pdsf.isdir else []
