##########################################################################################
# pdsfile/holdings_maintenance/_linkshelf_common.py
##########################################################################################

"""What the two link shelf tools share.

These shelve, for every file in a unit, either the list of links found inside it or the
label that describes it. Finding the links is where the two flavors differ -- a PDS3
label and a PDS4 label say different things in different syntax -- so each tool keeps
its own ``generate_links()`` and names it in its spec; everything that reads, writes,
compares or drives is here. The driver is ``_common.run_main()``.

A link shelf is a pickled dictionary written beside a readable ``.py`` file of the same
mapping, in the ``_linkshelf-<category>/`` tree. Its keys are the files of one unit and
its values are of two kinds, which is what most of the reading and writing code here has
to account for:

  * a **list** of ``(record number, basename, path)`` triples, for a file that points at
    others: a label, a catalog file, an index or a document;
  * a **string**, for a file that is pointed at, naming the label that describes it, and
    the empty string for a file no label claims.

The paths in a shelf file are stored relative to the unit and made absolute again when
it is read, so a holdings tree can be moved without rewriting its link shelves. A link
that leaves the unit is stored with as many leading ``../`` as it takes to reach the
nearest directory the two paths share.

Inside a run a link is a ``LinkInfo`` object; read back from a shelf it is the plain
tuple that was pickled. An update sees both kinds in one dictionary, which is why
``link_text_of()`` exists.

The five task functions are here because none of them differs between PDS3 and PDS4:
each calls the spec's ``generate_links``, and everything it then does with the result is
shared. ``link_tasks()`` binds a spec into all five and returns the table the driver
takes.
"""

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
    """One thing that looks like a link, found in one record of one file.

    An object is made for every match a scan finds, before anything decides whether the
    match is real. The scan then fills in what it learns: a repair may rewrite the name,
    and resolving the link fills in the file it points at. A match that resolves to
    nothing keeps an empty target and is dropped by the caller rather than here.

    ``linktext`` and ``linkname`` start out the same and separate only if a repair
    applies. The distinction is what lets a repair be looked up by the text that was
    actually written in the file while the shelf records the name that works.

    Attributes:
        recno: The record number the match was found in, counting from zero.
        linktext: The substring of that record that looks like a link, as written.
        linkname: The same text after any repair. A repair to the empty string is how
            a known-bad link is marked to be ignored.
        is_target: True if the local context suggests this names the file a label
            describes, rather than an incidental mention of a file name.
        target: The absolute path of the file this resolves to, or the empty string
            while it is unresolved. A non-empty value names a file that exists.
    """

    def __init__(self, recno, linkname, is_target):
        """Record one match, with its name not yet repaired and its target not resolved.

        Both ``linktext`` and ``linkname`` are set to the argument, so they agree until
        a repair separates them.

        Parameters:
            recno (int): The record number the match was found in, counting from zero.
            linkname (str): The text of the match, which becomes both the text and the
                name.
            is_target (bool): True if the local context suggests this is the target of
                a label.
        """

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
        """Cut this link's text back to its basename, in place.

        A repair table is keyed by the text a file was expected to carry, so a link
        written with a directory in front of it finds no entry. Dropping the directory
        gives the lookup a second chance at the same table.

        Both the text and the name are set to the basename, so any repair already
        applied is discarded. Text with no slash in it is left alone, and nothing is
        returned either way.
        """

        if '/' in self.linktext:
            self.linktext = self.linktext.rpartition('/')[2]
            self.linkname = self.linktext

    def __str__(self):
        """Return the record number, the text, the target flag and the resolution.

        The last field is the resolved target where there is one, and the link's name
        in square brackets where there is not, so an unresolved link reads differently
        from a resolved one at a glance.

        Returns:
            str: the four fields, separated by spaces.
        """

        return (f'{self.recno:d} {self.linktext} {self.is_target!s} '
                + (self.target or '[' + self.linkname + ']'))


def link_text_of(info):
    """Return the link text of one shelved link, however it is carried.

    A link generated in this run is a LinkInfo object; one read back from an
    existing shelf is the plain tuple that was pickled, (recno, linktext, target).
    An update sees both in the same dictionary.

    The tuple's second element is the text rather than the repaired name, so both forms
    report what the file was written with. Nothing else about a LinkInfo survives the
    pickling, which is why this is the only accessor the two forms share.

    Parameters:
        info: A LinkInfo or a (recno, linktext, target) tuple.

    Returns:
        str: The text of the link.

    Raises:
        IndexError: from the item read ``__getitem__()``, for a sequence shorter than
            two elements that is not a LinkInfo.
    """

    if isinstance(info, LinkInfo):
        return info.linktext

    return info[1]


def read_links(spec, abspath, logger=None):
    """Return everything in one file that looks like a link, in the order found.

    The file is read whole, as latin-1 text, and every record is searched repeatedly:
    each match consumes the text up to its end and the remainder is searched again, so
    one record can contribute several links.

    Three patterns are tried in a fixed order, and which one matched is what sets a
    LinkInfo's ``is_target``:

      * the spec's ``link_target_regex``, which recognizes a label naming the file it
        describes. A match sets ``is_target``, and a match containing an opening bracket
        or brace also opens a multiple-target list;
      * where that fails and a multiple-target list is open, the continuation pattern,
        which recognizes a bare file name on a line of its own. It sets ``is_target``
        too;
      * where both fail, the general pattern, which recognizes any file name embedded in
        a record. It clears ``is_target``, and a match closes the multiple-target list.

    The multiple-target state carries across records rather than resetting at each one,
    which is what lets a target list spread over several lines. A closing bracket or
    brace in a record that neither of the first two patterns matched closes it.

    Nothing here decides whether a match is real or resolves it to a file: every match
    becomes a LinkInfo with an empty target, and the caller filters, repairs and
    resolves them.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its link_target_regex is read.
        abspath (str): The file to read.
        logger: Accepted and not used. This function logs nothing; its callers pass a
            logger because every other helper here takes one.

    Returns:
        list: The LinkInfo objects, in the order the records were read.

    Raises:
        OSError: raised by ``open()`` if the file cannot be read. Nothing here catches
            it.
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
    """Return the file one link names, searching up the tree from where it was found.

    The search starts in the directory holding the file the link was found in and walks
    upward one directory at a time. At each level it looks for the name directly, and
    then inside nine conventional subdirectories -- LABEL, CATALOG, INCLUDE, INDEX,
    DOCUMENT, DATA, CALIB, EXTRAS and SOFTWARE -- in that order. The first hit wins, so
    a name present at two levels resolves to the deeper one.

    **The walk stops at the unit directory** and does not rise above it: the loop
    continues only while the spec's holdings component still has three components after
    it, which are the category, the unit set and the unit. A link is therefore never
    resolved to a file in another unit by this search.

    Every comparison is case-insensitive, on both the file name and the nine directory
    names, and the path returned carries the case the filesystem actually has.

    Parameters:
        spec (ToolSpec): The tool's specification. Only its holdings_sentinel is read,
            stripped of its slashes, and it is what tells the walk where to stop.
        abspath (str): The file the link was found in. Its directory is where the
            search starts.
        filename (str): The name to look for, without a directory.

    Returns:
        str: The absolute path of the file, or the empty string if the search reached
        the unit directory without finding it.

    Raises:
        OSError: raised by ``listdir()``. A directory the walk passes through that
            cannot be read fails the whole search, and so does an entry whose name
            matches one of the nine but which is a file rather than a directory.
    """

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
    """Return the file one link names, where the link carries a directory path.

    The first component is resolved by the same upward search a bare name gets, which
    fixes where the rest of the path is anchored; from there each remaining component is
    matched inside the directory the previous one found. A component is tried exactly
    first and case-insensitively second, so a path that is exactly right resolves even
    where a case-insensitive match would be ambiguous.

    Any component that matches nothing ends the search, so the answer is the whole path
    or nothing.

    Parameters:
        spec (ToolSpec): The tool's specification, passed on to the search for the
            first component.
        abspath (str): The file the link was found in. Its directory is where the
            search for the first component starts.
        filename (str): The link's text, with its components separated by slashes.

    Returns:
        str: The absolute path of the file, or the empty string if any component
        matched nothing.

    Raises:
        OSError: raised by ``listdir()`` on a component that resolved to something
            other than a readable directory, and by the search for the first component
            on the same terms.
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
    """Return one unit's shelved links, with every stored path made absolute again.

    The shelf stores paths relative to the unit, so reading it is the inverse of what
    write_linkdict() does: each key gets the unit's directory put back in front of it,
    and so does each stored path. A stored path that climbs out of the unit is
    normalized, so the ``../`` segments a link to another unit carries are resolved
    rather than left in the result.

    Both kinds of value are handled: a list of triples becomes a list of triples with
    absolute paths, and a string naming a label becomes an absolute path, with the empty
    string left empty because it means "no label" rather than "the unit directory".

    The pickle is read straight from disk rather than through the PdsFile shelf cache,
    so what comes back is what the file holds now.

    Parameters:
        spec (ToolSpec): The tool's specification. Its pdsfile_cls resolves the unit
            and its logname is the fallback logger's name.
        dirpath (str): The unit directory whose shelf is to be read.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

    Returns:
        dict: The links, keyed by absolute path. A file that points at others maps to a
        list of (record number, basename, absolute path) triples; a file that is
        pointed at maps to the absolute path of its label, or to the empty string.

    Raises:
        OSError: raised here if there is no shelf file for the unit, and raised by
            ``open()`` if there is one that cannot be read. Either is logged through
            ``exception()`` and re-raised, as is anything else the read raises.
    """

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
    """Write a new link shelf file, and its Python sidecar, for one unit.

    Every absolute path is turned back into a path the shelf can store. A path inside
    the unit becomes the part of itself below the unit directory. A path outside it
    becomes a relative path with as many leading ``../`` as the two have to climb to
    meet, and how many that is depends on what the two share:

      * the same category, bundle set and version suffix, meaning another unit of the
        same set: one level, ``../<bundlename>/<interior>``;
      * the same category only: two, ``../../<bundleset>/<bundlename>/<interior>``;
      * neither: three, with the category in front as well.

    A string value is trimmed by the same count as a key rather than tested against the
    prefix first, so the three-way choice above is made for a list value only and a
    label outside the unit would be trimmed as though it were inside.

    Two files are written, under two log levels: the pickle at the unit's link shelf
    path, and a readable ``.py`` beside it. In the sidecar the keys are padded to a
    common width capped at 60 characters, the basenames inside each triple are padded
    to their own common width, entries with a list value are written before entries
    with a string value, and the dictionary is named for the first two underscore-
    separated parts of the file's basename with "_links" appended. The parent directory
    is created if it is not there.

    Neither file is versioned here; a caller that wants the old one kept calls
    _shelf_common.move_old() first.

    Parameters:
        spec (ToolSpec): The tool's specification. Its pdsfile_cls resolves the unit
            and every outside link, its file_log_level names the method a created
            directory is reported through, and its logname is the fallback logger's
            name.
        dirpath (str): The unit directory the shelf covers.
        link_dict (dict): The links, keyed by absolute path, as generate_links() built
            them.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for the first of the two scopes, merged over the
            defaults. The Python sidecar's scope takes none.

    Raises:
        OSError: raised by ``open()`` or ``makedirs()`` if either file cannot be
            written. It is logged through ``exception()`` and re-raised, as is anything
            else either write raises.
    """

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

    A list value in either dictionary is sorted in place before the two are compared, so
    two links recorded in a different order are not a disagreement, and both callers'
    lists come back sorted whether or not anything was reported. That is the opposite of
    ``_indexshelf_common.validate_indexdict()``, which compares its lists as they are.

    Every disagreement is its own error line and the walk continues, so one call reports
    all of them.

    Parameters:
        spec (ToolSpec): The tool's specification. Its pdsfile_cls resolves the unit,
            for the root the logger reports paths relative to, and its logname is the
            fallback logger's name.
        dirpath (str): The unit the links were found in.
        dirdict (dict): The links a fresh scan found. Emptied.
        shelfdict (dict): The links the shelf file holds. Emptied.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits for this scope, merged over the defaults.

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
    """Shelve one unit's links, refusing to replace a shelf that is already there.

    A shelf file already in place is logged as an error and the unit is not scanned, so
    this is the one task of the five that never rewrites a shelf. It is also the only
    one that writes without versioning first, because it only runs where there is
    nothing to version.

    Parameters:
        spec (ToolSpec): The tool's specification. Its generate_links is what scans the
            unit.
        pdsdir: The unit directory.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the scan and the write.
    """

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
    """Shelve one unit's links, versioning and replacing whatever shelf is there.

    A unit with no shelf is a warning rather than an error, and is handed to
    link_initialize(). Otherwise the unit is scanned from scratch, ignoring what the
    shelf already holds, the old shelf is copied into the run's log directories, and the
    new one is written.

    The scan happens before the versioning, so a scan that fails leaves the old shelf
    both in place and unversioned.

    Parameters:
        spec (ToolSpec): The tool's specification. Its generate_links is what scans the
            unit.
        pdsdir: The unit directory.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the scan and the write.
    """

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
    """Report every way one unit's links and its shelf disagree.

    A missing shelf file is an error and stops the task. Otherwise the shelf is read and
    the unit is scanned from scratch, and the two are compared.

    Nothing is written whatever the answer. Both dictionaries are emptied by the
    comparison, but neither is used again.

    Parameters:
        spec (ToolSpec): The tool's specification. Its generate_links is what scans the
            unit.
        pdsdir: The unit directory.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the scan and the
            comparison.
    """

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
    """Rewrite one unit's link shelf if it disagrees, or re-date it if it does not.

    Where the shelved links and a fresh scan differ, the old shelf is versioned into the
    run's log directories and a new one is written. Where they agree, the content is
    right and only the dates can be wrong, so the shelf is compared against the newest
    file the scan read:

      * The shelf's age is the **older** of the pickle's and the sidecar's modification
        times, so a pair with one stale half is treated as stale.
      * If the holdings are newer, both files are touched to now and the run reports how
        far behind they were. The report is in days at or above a tenth of a day, which
        is 8,640 seconds, and in minutes below that.
      * If the holdings are not newer, the repair is canceled and nothing is touched.
        Equal times take this branch, since the test is strict.

    The comparison that decides this is between whole dictionaries and is made before
    validate_links() would empty them, so it is an equality test and not a report: a
    repair says what it did, not what was wrong.

    A unit with no shelf is a warning and is handed to link_initialize().

    Parameters:
        spec (ToolSpec): The tool's specification. Its generate_links is what scans the
            unit.
        pdsdir: The unit directory.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the scan and the write.
    """

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
    """Add the links of any file the shelf does not already carry.

    This is the one task that hands the shelved links to the scan. The scan takes them
    as its starting point and skips every file already accounted for, so what comes back
    is the old entries unchanged plus an entry for each file that has appeared since.
    An entry for a file that has since been deleted is therefore kept, and a file whose
    links have changed is not re-read.

    Where the scan returns exactly what the shelf held, the update is canceled and
    nothing is written or touched, and that is reported at info level rather than as a
    warning. Otherwise the old shelf is versioned and the merged one is written.

    A unit with no shelf is a warning and is handed to link_initialize().

    Parameters:
        spec (ToolSpec): The tool's specification. Its generate_links is what scans the
            unit.
        pdsdir: The unit directory.
        logger: The logger to report through. Defaults to the tool's own.
        limits (dict): Message limits, passed on to the read, the scan and the write.
    """

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

    Each entry is a partial over the shared task with the spec already supplied, so what
    a driver calls takes the unit and the keyword arguments and nothing more. That is
    what lets both tools share one set of five task functions.

    A fresh dictionary is built on every call, so a tool that alters its own table
    afterwards does not alter the other's.

    Parameters:
        spec (ToolSpec): The tool's specification, bound into each task.

    Returns:
        dict: The task functions, keyed by task name, each taking one unit.
    """

    return {name: functools.partial(task, spec) for name, task in _LINK_TASKS.items()}


def link_targets(spec, pdsf, path):
    """Return the unit directories one command-line path names.

    A unit set expands to the unit directories inside it; anything else that is not
    a directory is skipped, which is what leaves a unit set's readme file out.

    Each link shelf tool wraps this in a two-argument function of the same name and
    names the wrapper as its spec's expand_target, since ``_common.run_main()`` calls
    expand_target with the PdsFile and the path alone. The wrapper supplies the spec.

    A path that is neither a unit set nor a directory contributes nothing and is not
    reported, so a command line naming a single file inside a unit runs to completion
    having done nothing for it. Link shelves are written per unit, and there is no
    selection mechanism here of the kind the checksum and info shelf tools have.

    Parameters:
        spec (ToolSpec): Accepted and not used. It is taken so that the two tools'
            wrappers can pass their spec through uniformly; nothing below needs it.
        pdsf: The PdsFile the path resolved to.
        path (str): The absolute path the command line resolved to, for the messages.

    Returns:
        list: The PdsFile objects to shelve, which is the unit directories of a unit
        set, the path itself if it is a directory, and nothing otherwise.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 if the path names checksum or
            archive files.
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
