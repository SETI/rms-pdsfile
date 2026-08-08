##########################################################################################
# pdsfile/_derived_paths.py
##########################################################################################

"""The paths a PdsFile derives from its own path.

A holdings tree keeps several parallel copies of the same structure. Alongside
``volumes/`` there is a ``checksums-volumes/`` holding one MD5 file per bundle and an
``archives-volumes/`` holding one ``.tar.gz`` per bundle, and the same pair exists for
every other category except ``documents``, which gets neither. So a file below a bundle
has a checksum file that covers it and an archive file that contains it, and each of
those has a directory it was made from; a file at bundle-set level has a checksum file
but no archive, because an archive is made of a bundle. Working out those paths is
arithmetic on the parts of a path -- the holdings root, the category, the bundle set, the
bundle name -- and that arithmetic is what ``_DerivedPathsMixin`` holds.

The log paths are the same kind of derivation aimed at a different tree. A maintenance
tool writes its log where the file it worked on says to, under a log root that is either
set on the class or taken to be a ``logs`` directory beside ``holdings``, and the log
basename carries a time tag so that two runs do not overwrite each other.
``_pinned_log_timetag()`` fixes that tag for the duration of a block, so that a tool
writing one run's log to two places dates both copies alike.
"""

import contextlib
import datetime


##########################################################################################
# Derived paths mixin
##########################################################################################
class _DerivedPathsMixin:
    """Builders for the paths PdsFile derives from its own path.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Three groups. The checksum group says where the MD5 file that covers this
    file lives, and which directory a checksum file was made from. The archive
    group asks the same two questions of a .tar.gz. The log group builds the path
    of a log file written about this file, and owns the two class attributes that
    decide where logs go and how they are time-stamped.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, datetime and contextlib methods are
    not in scope::

      class attributes read       LOGFILE_TIME_FMT, LOG_ROOT_, _LOG_TIMETAG, and
                                  the one the interpreter supplies, __dict__
      class attributes WRITTEN    LOG_ROOT_ by set_log_root, _LOG_TIMETAG by
                                  _pinned_log_timetag, each onto the class the
                                  call was made on rather than onto PdsFile
      core properties read        is_bundle_dir, is_bundleset_dir
      lazy properties read        is_index
      instance attributes read    archives_, basename, bundlename, bundleset,
                                  bundleset_, bundletype_, category_, checksums_,
                                  disk_, interior, logical_path, root_, suffix
      instance attributes WRITTEN archives_, category_ and checksums_, none of
                                  them on self: archive_logpath writes them on a
                                  copy it makes and discards
      other methods called        copy

    All of those are defined on PdsFile. One more comes from a sibling mixin:
    checksum_path_if_exact and archive_path_if_exact reach _LocalFsMixin's
    os_path_exists. Every one of these is an attribute lookup on self or on
    type(self) at run time, not an import, which is what lets the halves live in
    different modules.
    """

    ############################################################################
    # Checksum path associations
    ############################################################################

    def checksum_path_and_lskip(self):
        """Return the checksum file covering this one, and where its basename starts.

        The checksum file lives in the ``checksums-`` parallel of this file's own
        category, and what it covers depends on what this file is. For an archive file,
        one checksum file covers the whole bundle set. For anything with a bundle name,
        one covers that bundle. For the three kinds of directory that sit under a bundle
        set without being a bundle -- a name starting ``checksums_``, a name starting
        ``superseded``, or a name ending ``_support`` -- one covers that directory.

        The basename carries the volume type when there is one to carry: a file under
        ``volumes/`` or ``bundles/`` gets none, and anything else gets its own bundle
        type without the trailing slash, so a metadata bundle yields
        ``..._metadata_md5.txt``. The bundle type is not the category, and the two part
        company on an archive file, whose category carries an ``archives-`` prefix its
        bundle type does not: an archive of a metadata bundle still yields
        ``..._metadata_md5.txt`` and not ``..._archives-metadata_md5.txt``.

        The second value is a character count into the returned path: everything from it
        onward is the checksum file's basename.

        Returns:
            tuple: the absolute path of the checksum file, and the offset at which its
            basename begins.

        Raises:
            ValueError: if this is itself a checksum file, or if it is none of the kinds
                of file above and so has nothing a checksum file could be named after.
        """

        if self.checksums_:
            raise ValueError('No checksums of checksum files: ' +
                             self.logical_path)

        if self.bundletype_ == 'volumes/' or self.bundletype_ == 'bundles/':
            suffix = ''
        else:
            suffix = '_' + self.bundletype_[:-1]

        if self.archives_:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset, self.suffix, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_))

        elif self.bundlename:
            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset_, self.bundlename, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_) +
                     len(self.bundleset_))

        # for non bundle directories under a bundleset
        elif (self.basename.startswith('checksums_') or
              self.basename.startswith('superseded') or
              self.basename.endswith('_support')):

            abspath = ''.join([self.root_, 'checksums-', self.category_,
                               self.bundleset_, self.basename, suffix, '_md5.txt'])
            lskip = (len(self.root_) + len('checksums_') + len(self.category_) +
                     len(self.bundleset_))
        else:
            raise ValueError('Missing volume name for checksum file: ' +
                             self.logical_path)

        return (abspath, lskip)

    def checksum_path_if_exact(self):
        """Return the checksum file whose contents exactly cover this directory.

        A checksum file covers a whole bundle, or a whole bundle set of archives. Only
        two kinds of object are therefore an exact match for one: a bundle directory,
        and an archive file's bundle set directory. Everything else -- a file inside a
        bundle, a category directory, a checksum file itself -- gets an empty string,
        because the checksum file that covers it also covers other things.

        An exact match still has to exist. The path is checked against the filesystem,
        so a bundle whose checksum file has not been written yet also gets an empty
        string. The check is made even when there was no candidate, in which case it is
        an existence test on the empty path.

        A caller can use the result to decide whether to offer a checksum download for
        what it is showing.

        Returns:
            str: the absolute path of the checksum file, or an empty string.
        """

        if self.checksums_:
            return ''

        cls = type(self)

        path_if_exact = ''
        if self.archives_ and self.is_bundleset_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if self.is_bundle_dir:
            path_if_exact = self.checksum_path_and_lskip()[0]

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_checksum(self):
        """Return the directory a checksum file covers, and the prefix its rows omit.

        Each row of a checksum file names a file by a path relative to somewhere, and
        the prefix is that somewhere: prepending it to a row's path gives an absolute
        path. For a checksum file over archives, the directory is the bundle set's
        archive directory and the prefix is that same directory with a trailing slash.
        For a checksum file over a bundle, the directory is the bundle and the prefix is
        the bundle set above it, so the rows carry the bundle name.

        Nothing here tests that this object is a checksum file. Called on one that is
        not, it still computes a pair, from that object's own category and bundle names.

        Returns:
            tuple: the absolute path of the directory, and the prefix, which ends in a
            slash.
        """

        if self.archives_:
            dirpath = (f'{self.root_}{self.archives_}{self.bundletype_}' +
                       f'{self.bundleset}{self.suffix}')
            prefix_ = f'{dirpath}/'
        else:
            dirpath = (f'{self.root_}{self.archives_}{self.bundletype_}' +
                       f'{self.bundleset_}{self.bundlename}')
            prefix_ = f'{self.root_}{self.bundletype_}{self.bundleset_}'

        return (dirpath, prefix_)

    ############################################################################
    # Archive path associations
    ############################################################################

    def archive_path_and_lskip(self):
        """Return the archive file containing this one, and the archived directory's
        prefix length.

        One archive file holds one bundle, so the path is the bundle's own name under
        the ``archives-`` parallel of this file's category, with ``.tar.gz`` on the end
        and, for anything outside ``volumes/`` and ``bundles/``, the volume type before
        it.

        The second value is a character count, and **it does not index the path this
        returns**. It is the length of the prefix of the *archived directory's* path
        that ends before the bundle name, which is what a caller strips to get the name
        each entry should have inside the archive. Sliced off the returned archive path
        instead it lands in the middle of the bundle set name, because that path carries
        an extra ``archives-`` the count does not account for.

        Returns:
            tuple: the absolute path of the archive file, and the length of the archived
            directory's prefix.

        Raises:
            ValueError: if this is a checksum file or is already an archive file, since
                neither is archived; or if it has no bundle name, since an archive is
                made of a bundle.
        """

        if self.checksums_:
            raise ValueError('No archives for checksum files: ' +
                             self.logical_path)

        if self.archives_:
            raise ValueError('No archives for archive files: ' +
                             self.logical_path)

        if self.bundletype_ == 'volumes/' or self.bundletype_ == 'bundles/':
            suffix = ''
        else:
            suffix = '_' + self.bundletype_[:-1]

        if not self.bundlename:
            raise ValueError('Archives require bundle names: ' +
                              self.logical_path)

        abspath = ''.join([self.root_, 'archives-', self.category_,
                           self.bundleset_, self.bundlename, suffix, '.tar.gz'])
        lskip = len(self.root_) + len(self.category_) + len(self.bundleset_)

        return (abspath, lskip)

    def archive_path_if_exact(self):
        """Return the archive file whose contents exactly cover this directory.

        One archive holds one bundle, so an exact match means a bundle directory: a file
        or directory inside a bundle has a non-empty interior path and gets an empty
        string, as do checksum files and archive files themselves. So does anything the
        archive path cannot be worked out for, and anything whose archive file has not
        been written yet, because the path is checked against the filesystem.

        Returns:
            str: the absolute path of the archive file, or an empty string.
        """

        if self.checksums_ or self.archives_:
            return ''

        if self.interior:
            return ''

        try:
            path_if_exact = self.archive_path_and_lskip()[0]
        except ValueError:
            return ''

        cls = type(self)

        if cls.os_path_exists(path_if_exact):
            return path_if_exact

        return ''

    def dirpath_and_prefix_for_archive(self):
        """Return the directory an archive file was made from, and its parent.

        Both are in the tree the archive was made from rather than in the archive tree,
        because they are built from this object's bundle type rather than its category:
        an object for ``archives-volumes/SET/BUNDLE.tar.gz`` yields the ``volumes``
        directory for that bundle and the bundle set above it.

        The parent ends in a slash, so it can be prepended to a path relative to the
        bundle set.

        Returns:
            tuple: the absolute path of the archived directory, and the absolute path of
            its parent.
        """

        dirpath = f'{self.root_}{self.bundletype_}{self.bundleset_}{self.bundlename}'
        parent  = f'{self.root_}{self.bundletype_}{self.bundleset_}'

        return (dirpath, parent)

    def archive_logpath(self, task):
        """Return the log file path for the archiving of this file.

        The log goes under an ``archives`` subdirectory of the log root, and below that
        it is filed by category, bundle set and bundle name. A copy of this object is
        made with its checksum marker cleared, and, if it is an archive file, with its
        archive marker cleared and its category replaced by its bundle type, so an object
        for an archive of a volume logs under ``archives/volumes/...``. Only the second
        of those rewrites reaches the answer, because the category is the only one of the
        three the log path reads: clearing the checksum marker leaves the category as it
        was, so a checksum file logs under ``archives/checksums-volumes/...`` rather than
        under ``archives/volumes/...``. The copy is discarded; this object is not
        changed.

        The basename ends in ``_targz``, then the time tag, then the task if one was
        given.

        Parameters:
            task (str): a word for what the run was doing, appended to the basename. An
                empty string appends nothing.

        Returns:
            str: the absolute path of the log file.
        """

        this = self.copy()
        this.checksums_ = ''
        if this.archives_ == 'archives-':
            this.archives_ = ''
            this.category_ = this.bundletype_

        return this.log_path_for_bundle('_targz', task=task, dir='archives')

    ############################################################################
    # Log path associations
    ############################################################################

    @classmethod
    def set_log_root(cls, root=None):
        """Set the default root directory for log files.

        The value is written onto the class this is called on, so calling it on a
        subclass leaves the others alone. A root is stored with exactly one trailing
        slash, however many it was given, so an empty string is stored as ``/`` and every
        log path is then built at the filesystem root. Only None asks for the default
        described below, so a caller that treats an empty string as "unset" has to
        convert it first.

        None means there is no default, and every log path is then built under a
        ``logs`` directory beside the holdings directory the file itself is in, so
        different files can log to different disks.

        Parameters:
            root (str): the directory log paths are built under, or None for the
                ``logs`` directory beside holdings.
        """

        if root is None:
            cls.LOG_ROOT_ = None
        else:
            cls.LOG_ROOT_ = root.rstrip('/') + '/'

    @classmethod
    @contextlib.contextmanager
    def _pinned_log_timetag(cls):
        """Give every log path built inside the block one time tag.

        A tool writes one run's log in up to two places and builds the two paths
        with two calls. The time tag has one-second resolution, so two calls that
        straddle a second boundary date the two copies of one log a second apart and
        they stop naming one run. Reading the clock once, on the way into the block,
        makes every path built inside it agree.

        The pin is a class attribute, like the log root. On the way out the class
        dictionary is put back exactly as it was found -- restored if the class had
        its own value, deleted if the value was inherited -- so a block that raises
        leaves nothing behind, nesting is safe, and a class that has been pinned
        once does not stop inheriting a pin taken on a base class.

        Yields:
            None: once, with the pin in place. The pin is removed when the block ends,
            however it ends.
        """

        had_own = '_LOG_TIMETAG' in cls.__dict__
        previous = cls.__dict__.get('_LOG_TIMETAG')
        cls._LOG_TIMETAG = cls._log_timetag()
        try:
            yield
        finally:
            if had_own:
                cls._LOG_TIMETAG = previous
            else:
                del cls._LOG_TIMETAG

    @classmethod
    def _log_timetag(cls):
        """Return a log file name's time tag, read from the clock now.

        The format is the class's ``LOGFILE_TIME_FMT``, which gives one-second
        resolution, so two calls in the same second agree and two calls that straddle a
        second boundary do not. That is what ``_pinned_log_timetag()`` exists to avoid.

        Returns:
            str: the time tag.
        """

        return datetime.datetime.now().strftime(cls.LOGFILE_TIME_FMT)

    def _log_path_for(self, target, suffix, task, subdir, place):
        """Return a complete log file path, given the parts that name what is logged.

        The three log_path_for_* methods differ in three ways: in the parts that
        name their target, in whether they accept a suffix, and in what their
        subdirectory defaults to, which is "index" for log_path_for_index and
        nothing for the other two. Everything else -- resolving the log root, the
        optional subdirectory, the time tag, the task tag and the ".log" extension
        -- is the same for all three and is done here.

        The assembled path is::

            <log root><subdir/><target parts>[_<suffix>]_<time tag>[_<task>].log

        The time tag is the pinned one if a block has pinned it, and the clock read now
        if not.

        Parameters:
            target: a callable returning the parts naming what is being logged,
                appended after the optional subdirectory. It is called here rather than
                evaluated by the caller, so the attributes it reads are read after the
                place option has been validated.
            suffix (str): the suffix of the log file. An empty string appends nothing,
                which is what log_path_for_index passes because it takes no suffix. A
                leading underscore is stripped, so exactly one separates it.
            task (str): part of the log basename. An empty string appends nothing.
            subdir (str): the directory of the log file. An empty string appends
                nothing, and a trailing slash is normalized to one. This is the
                log_path_for_* methods' "dir" argument under a name that does not shadow
                the builtin; theirs stays "dir" because callers pass it by that keyword.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to ignore that root and build under a "logs" directory beside the
                holdings directory this file is in. 'default' also falls back to the
                latter when no log root has been set.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: if the place option is neither of the two.
        """

        cls = type(self)

        # This option provides for a temporary override of the default log root
        if place == 'default':
            temporary_log_root = cls.LOG_ROOT_
        elif place == 'parallel':
            temporary_log_root = None
        else:
            raise ValueError('unrecognized place option: ' + place)

        if temporary_log_root is None:
            parts = [self.disk_, 'logs/']
        else:
            parts = [temporary_log_root]

        if subdir:
            parts += [subdir.rstrip('/'), '/']

        parts += target()

        if suffix:
            parts += ['_', suffix.lstrip('_')]  # exactly one "_" before suffix

        parts += ['_', cls._LOG_TIMETAG or cls._log_timetag()]

        if task:
            parts += ['_', task]

        parts += ['.log']

        return ''.join(parts)

    def log_path_for_bundle(self, suffix='', task='', dir='', place='default'):
        """Return the log file path for this file's bundle.

        The path is ``[dir/]category/bundleset/bundlename[_suffix]_time[_task].log``
        below the log root, so every file in one bundle logs to one place regardless of
        where in the bundle it sits.

        Parameters:
            suffix (str): the suffix of the log file basename. An empty string appends
                nothing.
            task (str): part of the log basename. An empty string appends nothing.
            dir (str): a subdirectory of the log root. An empty string appends nothing.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to build under a "logs" directory beside this file's holdings directory.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: raised by ``_log_path_for()`` if the place option is neither of
                the two.
        """

        return self._log_path_for(lambda: [self.category_, self.bundleset_,
                                           self.bundlename],
                                  suffix=suffix, task=task, subdir=dir, place=place)

    def log_path_for_bundleset(self, suffix='', task='', dir='', place='default'):
        """Return the log file path for this file's bundle set.

        The path is ``[dir/]category/bundleset<version>[_suffix]_time[_task].log`` below
        the log root. The version part is this file's own bundle set suffix, which is
        not the ``suffix`` argument: the argument goes after it, and either can be
        empty.

        Parameters:
            suffix (str): the suffix of the log file basename. An empty string appends
                nothing.
            task (str): part of the log basename. An empty string appends nothing.
            dir (str): a subdirectory of the log root. An empty string appends nothing.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to build under a "logs" directory beside this file's holdings directory.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: raised by ``_log_path_for()`` if the place option is neither of
                the two.
        """

        return self._log_path_for(lambda: [self.category_, self.bundleset, self.suffix],
                                  suffix=suffix, task=task, subdir=dir, place=place)

    def log_path_for_index(self, task='', dir='index', place='default'):
        """Return the log file path for this index file.

        The path is ``[dir/]<this file's logical path without its extension>_time
        [_task].log`` below the log root, so an index logs beside where it sits in the
        holdings tree rather than at bundle granularity. There is no suffix argument,
        because the logical path already identifies the file.

        The subdirectory defaults to ``index`` rather than to nothing, so index logs are
        kept apart from the rest unless a caller asks otherwise.

        Parameters:
            task (str): part of the log basename. An empty string appends nothing.
            dir (str): a subdirectory of the log root. An empty string appends nothing.
            place (str): 'default' to build under the class's log root, or 'parallel'
                to build under a "logs" directory beside this file's holdings directory.

        Returns:
            str: the absolute path of the log file.

        Raises:
            ValueError: if this file is not an index file. That check runs before the
                place option is looked at, so a non-index file is reported as such even
                when the place option is also wrong.
        """

        # This check precedes the place option's validation, so a non-index file
        # reports that before an unrecognized place
        if not self.is_index:
            raise ValueError('Not an index file: ' + self.logical_path)

        return self._log_path_for(lambda: [self.logical_path.rpartition('.')[0]],
                                  suffix='', task=task, subdir=dir, place=place)
