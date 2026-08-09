#!/usr/bin/env python3
################################################################################
# pdsfile/holdings_maintenance/pds3/pdsdependency.py
################################################################################

"""Check that every file a PDS3 volume implies exists, and is no older than its source.

The other maintenance tools each own one kind of derived file and check it against what
it describes. This one owns the relationships between them: given a volume, it works out
what else the holdings tree ought to contain -- checksums, archives, shelves, previews,
diagrams, calibrated images, metadata tables and the cumulative versions of those tables
-- and reports whatever is missing or stale. It creates nothing and repairs nothing. What
it produces instead is a list of the commands an operator would have to type, printed
under "Steps required" at the end of a run.

Run it as::

    pdsdependency volume_path [volume_path ...]

Each path names a volume or a volume set, and a volume set is expanded into its volumes.
Checksum and archive directories are refused, because the dependencies are stated from
the volume's side.

**What is checked is decided by the volume's path, not by its contents.** Two tables do
that. ``TESTS`` maps a path to the names of the test suites that apply to it, so a path
under ``COISS_2xxx`` picks up the Cassini imaging suites and one under ``VGISS_7xxx``
picks up the Voyager-at-Uranus ones; every volume picks up ``general``, which is the
suite of derived files every volume has regardless of what is in it. Each suite is then a
list of ``PdsDependency`` objects, each of which is one rule: a glob that finds the files
the rule is about, a regular expression that takes such a file apart, and one or more
substitutions that name the files that must exist because of it.

A rule can also require the derived file to be no older than its source. That is the
majority of them, and it is what ``--timeless`` in ``re_validate`` turns off, through the
``check_newer`` argument threaded down from ``test()``. Modification times of directories
are taken recursively, over every file below them, and cached.

``TESTS`` has 49 rows and names 41 suites between them, and a volume picks up as many of
them as its path matches. The rules themselves are the documentation of what each suite
requires: every one carries a title, a run's log is organized by those titles, and a
rule that finds nothing to test says nothing at all.

Nothing here is imported by another tool except ``re_validate``, which calls ``test()``
as the last of its five per-volume validations.
"""

import argparse
import glob
import os
import re
import sys

import pdslogger
import translator

import pdsfile
from pdsfile.holdings_maintenance import _common

LOGNAME = 'pds.validation.dependencies'
LOGROOT_ENV = 'PDS_LOG_ROOT'

BACKUP_FILENAME = re.compile(r'.*[-_](20\d\d-\d\d-\d\dT\d\d-\d\d-\d\d'
                             r'|backup|original)\.[\w.]+$')

################################################################################
# Translator for tests to apply
#
# Each path to a volume is compared against each regular expression. For those
# regular expressions that match, the associated suite of tests is performed.
# Note that 'general' tests are performed for every volume.
################################################################################

TESTS = translator.TranslatorByRegex([
    ('.*',                          0, ['general']),
    ('.*/COCIRS_0xxx(|_v[3-9])/COCIRS_0[4-9].*',
                                    0, ['cocirs01']),
    ('.*/COCIRS_1xxx(|_v[3-9]).*',  0, ['cocirs01']),
    ('.*/COCIRS_[56]xxx/.*',        0, ['cocirs56']),
    ('.*/COISS_[12]xxx/.*',         0, ['coiss12', 'metadata', 'inventory',
                                        'rings', 'moons' ,'cumindex999']),
    ('.*/COISS_100[1-7]/.*',        0, ['jupiter']),
    ('.*/COISS_100[89]/.*',         0, ['saturn']),
    ('.*/COISS_2xxx/.*',            0, ['saturn']),
    ('.*/COISS_3xxx.*',             0, ['coiss3']),
    ('.*/COUVIS_0xxx/.*',           0, ['couvis', 'metadata', 'supplemental',
                                        'cumindex999']),
    ('.*/COUVIS_0xxx/COUVIS_0006.*',     0, ['saturn', 'rings']),
    ('.*/COUVIS_0xxx/COUVIS_000[7-9].*', 0, ['saturn', 'rings', 'moons']),
    ('.*/COUVIS_0xxx/COUVIS_00[1-9].*',  0, ['saturn', 'rings', 'moons']),
    ('.*/COVIMS_0.*',               0, ['covims', 'metadata', 'cumindex999']),
    ('.*/COVIMS_000[4-9].*',        0, ['saturn', 'rings', 'moons']),
    ('.*/COVIMS_00[1-9].*',         0, ['saturn', 'rings', 'moons']),
    ('.*/CO.*_8xxx/.*',             0, ['metadata', 'supplemental', 'profile']),
    ('.*/CORSS_8xxx/.*',            0, ['corss_8xxx']),
    ('.*/COUVIS_8xxx/.*',           0, ['couvis_8xxx']),
    ('.*/COVIMS_8xxx/.*',           0, ['covims_8xxx']),
    ('.*/EBROCC_xxx/.*',            0, ['ebrocc_xxxx', 'metadata',
                                        'supplemental', 'profile']),
    ('.*/GO_0xxx/GO_00(?!01).*',    0, ['metadata', 'cumindex999',
                                        'go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5', 'supplemental',
                                        'inventory', 'sky']),
    ('.*/GO_0xxx/GO_00[2-689].*',   0, ['body']),
    ('.*/GO_0xxx/GO_00[12][0-9].*', 0, ['body']),
    ('.*/GO_0xxx/GO_0016.*',        0, ['sl9']),
    ('.*/GO_0xxx_v1/GO_000[2-9].*', 0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    ('.*/GO_0xxx_v1/GO_00[12].*',   0, ['go_previews2', 'go_previews3',
                                        'go_previews4', 'go_previews5']),
    (r'.*/JNOJIR_xxxx(|_v[\d.]+)/JNOJIR_(?!(1059|2059|2060)).*',
                                    0, ['metadata', 'cumindex999']),
    ('.*/JNOJNC_0xxx/.*',           0, ['metadata', 'cumindex999']),
    ('.*/JNOSRU_xxxx/.*',           0, ['metadata', 'cumindex999', 'jnosru']),
    ('.*/HST.x_xxxx/.*',            0, ['hst', 'metadata', 'cumindex9_9999']),
    ('.*/NH..(LO|MV)_xxxx/.*',      0, ['metadata', 'supplemental', 'cumindexNH']),
    ('.*/NH(JU|LA)LO_[12]00.*',     0, ['jupiter', 'rings', 'moons', 'inventory']),
    ('.*/NHP.LO_[12]00.*',          0, ['pluto', 'rings', 'moons', 'inventory']),
    ('.*/NH[LPK].LO_[12]00.*',      0, ['nhbrowse']),
    ('.*(?<!_v[12])/NHJULO_100.*',  0, ['nhbrowse']),       # not NHJULO_1001 _v1-2
    ('.*(?<!_v[123])/NHJULO_200.*', 0, ['nhbrowse']),       # not NHJULO_2001 _v1-3
    ('.*/NH[PK].MV_[12]00.*',       0, ['nhbrowse']),
    ('.*(?<!_v1)/NHLAMV_[12]00.*',  0, ['nhbrowse_vx']),    # not NHLAMV _v1
    ('.*/NHJUMV_100.*',             0, ['nhbrowse_vx']),
    ('.*(?<!_v1)/NHJUMV_200.*',     0, ['nhbrowse_vx']),    # not NHJUMV_2001 _v1
    ('.*/RPX_xxxx/.*',              0, ['metadata']),
    ('.*/RPX_xxxx/RPX_000.*',       0, ['obsindex', 'cumindex99']),
    ('.*/VGISS_[5678]xxx/.*',       0, ['vgiss', 'metadata', 'raw_image',
                                        'supplemental', 'cumindex999']),
    ('.*/VGISS_5(10[4-9]|20[5-9]|11|21)/.*',
                                    0, ['jupiter', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_6(10|11[0-5]|2)/.*', 0, ['saturn', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_7xxx/.*',            0, ['uranus', 'inventory', 'rings',
                                        'moons']),
    ('.*/VGISS_8xxx/.*',            0, ['neptune', 'inventory', 'rings',
                                        'moons']),
    ('.*/VG_28xx/.*',               0, ['metadata', 'vg_28xx']),
])

################################################################################
# Class definition
################################################################################

class PdsDependency:

    """One rule saying which files a volume must hold because it holds some other file.

    A rule is a glob, a regular expression and a list of substitutions. The glob, once
    the volume set and volume name have been substituted into it, finds the files the
    rule is about. Each is then matched against the regular expression, and each
    substitution turns that match into the path of a file that must exist. So one rule
    can name several required files per file found -- four preview sizes for one image,
    a pickle and its sidecar for one shelf -- and a rule finding nothing to match tests
    nothing and logs nothing.

    Every rule constructed at import time registers itself in a named suite, and the
    class holds those suites. Nothing outside this module constructs one: the module
    body builds all of them, ``TESTS`` decides which suites a volume reaches, and
    ``test_suite()`` runs a suite by name.

    Three pieces of state are the class's rather than an instance's, and all three
    outlive a single test:

      * ``DEPENDENCY_SUITES`` maps a suite name to the rules registered under it, in
        construction order, which is the order they run in.
      * ``MODTIME_DICT`` caches the recursive modification time of every directory
        looked at, so that a directory scanned for one rule is not walked again for the
        next. ``purge_cache()`` empties it and nothing calls it.
      * ``COMMANDS_TO_TYPE`` accumulates the repair commands a run has worked out, in
        first-seen order and without duplicates. It is never emptied, so a process that
        tests several volumes prints one combined list covering all of them.
    """

    DEPENDENCY_SUITES = {}
    MODTIME_DICT = {}
    COMMANDS_TO_TYPE = []

    def __init__(self, title, glob_pattern, regex, sublist, messages=[],
                 suite=None, newer=True, func=None, args=(), exceptions=[]):
        """Build one rule and register it in its suite.

        Registration is the constructor's real work: an instance is appended to its
        suite's list and the caller has no further use for the object, which is why
        every construction in this module assigns to a throwaway name.

        Parameters:
            title (str): A short description of what the rule requires, used as the
                heading of the rule's own log section. A title beginning "Newer " is
                rewritten when a run is not checking modification dates, so titles
                should be written for the checking case.
            glob_pattern (str): The pattern that finds the files this rule is about,
                relative to the holdings root. Its first "$" is replaced by the volume
                set directory name, and a second "$" by the volume name, so a pattern
                names neither. A pattern with one "$" is deliberate rather than
                incomplete: it is how a rule is written to cover a whole volume set at
                once.
            regex (str or re.Pattern): What each file found is matched against, as a
                path relative to the holdings root. A string is anchored at both ends
                and compiled case-insensitively; a compiled pattern is taken as it is,
                anchors and flags included.
            sublist (str or list): One or more replacement templates. Each is applied to
                the match to name a file that must exist, so the count of required files
                is the count of templates, not one.
            messages (str or list): One or more command lines an operator would type to
                supply what is missing. Four markers are substituted: "[c]" becomes
                "initialize" for a missing file and "repair" for a stale one, "[C]"
                becomes "initialize" for a missing file and "reinitialize" for a stale
                one, "[d]" becomes the holdings root, and "[x]" marks a truncation
                point. The message is cut at "[x]" in every case except a stale file
                whose message carries "[C]", where the marker is removed and the rest of
                the line kept. Group references are substituted first, so a marker can
                follow one.
            suite (str): The name of the suite to register in. A rule with no suite is
                registered nowhere and can never run.
            newer (bool): Whether the required file must also be no older than the file
                that implies it. False checks existence alone.
            func (collections.abc.Callable): An optional transformation of the volume
                name, applied before the name is substituted into the glob. This is how
                a rule about cumulative indexes is written: the rule is registered
                against the volumes it is triggered by, and ``func`` turns a volume name
                into the name of the cumulative volume the requirement is about.
            args (tuple): Further arguments for ``func``, after the volume name.
            exceptions (list): Regular expressions for files this rule does not apply
                to. Each is compiled case-insensitively and matched against the whole
                absolute path, so a pattern has to account for the holdings root, which
                is why every one of them begins with a wildcard.
        """

        self.glob_pattern = glob_pattern

        if isinstance(regex, str):
            self.regex = re.compile('^' + regex + '$', re.I)
        else:
            self.regex = regex

        self.regex_pattern = self.regex.pattern
        self.sublist = [sublist] if isinstance(sublist, str) else sublist

        if suite is not None:
            if suite not in PdsDependency.DEPENDENCY_SUITES:
                PdsDependency.DEPENDENCY_SUITES[suite] = []

            PdsDependency.DEPENDENCY_SUITES[suite].append(self)

        self.title = title
        self.suite = suite
        self.messages = [messages] if isinstance(messages, str) else messages
        self.newer = newer
        self.func = func
        self.args = args
        self.exceptions = [re.compile(pattern, re.I) for pattern in exceptions]

    @staticmethod
    def purge_cache():
        """Empty the cache of directory modification times.

        The cache is a class attribute and lives for the life of the process, so a
        program that tests a volume, changes the tree and tests it again would read the
        first pass's times in the second. Nothing in this repository calls this, because
        nothing changes the tree between tests: the tool reports what to do and does not
        do it.
        """

        PdsDependency.MODTIME_DICT = {}

    @staticmethod
    def get_modtime(abspath, logger):
        """Return one path's modification time, recursively for a directory.

        A file's time is its own. A directory's is the newest among everything below it,
        found by walking the whole subtree, and is cached under the directory's path so
        that the walk happens once per run however many rules ask for it.

        Two kinds of file are logged and left out of the comparison. A ``.DS_Store`` is
        logged at debug level, so it does not affect the run's status. A dot-underscore
        file is logged at error level, so **one of them anywhere below a directory gives
        the whole run a nonzero exit status**, whatever the dependencies turn out to be.
        Nothing else is excluded: backup and " copy" files date a directory exactly as
        their originals do.

        Parameters:
            abspath (str): The file or directory to time. A path that is neither an
                existing file nor a listable directory reaches the listing and fails
                there.
            logger: Where the two excluded kinds are logged. It is
                used for nothing else and is not optional.

        Returns:
            float: The Unix modification time in seconds. An empty directory, and one
            holding nothing but the two excluded kinds, gives -1.0e99, which compares
            older than any real time; the value is cached like any other.

        Raises:
            OSError: from the ``listdir()`` of a path that is not an existing file and
                cannot be listed, which includes a path that does not exist at all and a
                symbolic link with nothing at the end of it.
        """

        if os.path.isfile(abspath):
            return os.path.getmtime(abspath)

        if abspath in PdsDependency.MODTIME_DICT:
            return PdsDependency.MODTIME_DICT[abspath]

        modtime = -1.e99
        files = os.listdir(abspath)
        for file in files:
            absfile = os.path.join(abspath, file)

            if file == '.DS_Store':     # log .DS_Store files; ignore dates
                logger.ds_store('.DS_Store ignored', absfile)
                continue

            if '/._' in absfile:        # log dot-underscore files; ignore dates
                logger.dot_underscore('._* file ignored', absfile)
                continue

                if BACKUP_FILENAME.match(file) or ' copy' in file:
                    logger.error('Backup file skipped', abspath)
                    continue

            modtime = max(modtime, PdsDependency.get_modtime(absfile, logger))

        PdsDependency.MODTIME_DICT[abspath] = modtime
        return modtime

    def test1(self, dirpath, check_newer=True, logger=None, limits={}):
        """Apply this one rule to one volume and log what it finds.

        The glob is built first, from the holdings root of the volume named, and if it
        matches nothing the call returns at once having logged nothing at all -- not
        even the rule's title. That is the usual outcome for most rules on most volumes,
        and it is what keeps a log about the dependencies a volume actually has.

        Every file the glob matched is then taken through every substitution, in that
        order: the outer loop is over the substitutions and the inner over the files, so
        a rule requiring four preview sizes reports all the missing thumbnails together
        rather than all four sizes of one image together. Each required file is logged
        as one of four things:

          * skipped, if the file that implies it matches one of the rule's exceptions;
          * an invalid test, if the rule's regular expression does not match the file
            the rule's own glob found. This is an error rather than a skip, because the
            two patterns disagreeing is a defect in the rule;
          * missing, if the required file does not exist;
          * out of date, if it exists and is older than its source, which is checked
            only when the rule asks for it and the run has not turned the check off;
          * confirmed otherwise.

        The last three are reported once per required path however many files imply it,
        so a rule over a thousand images that all require one metadata table reports
        that table once. The first two are not deduplicated: a skipped file is logged
        once for each substitution the rule carries, and so is an invalid test.

        A missing or stale file also contributes the rule's repair commands to the
        class-level list the run prints at the end. They differ between the two cases:
        the missing case asks for an initialize, the stale case for a repair or a
        reinitialize.

        Parameters:
            dirpath (str): The volume directory. It is made absolute, and everything
                else -- the holdings root, the volume set and the volume name -- is
                derived from it.
            check_newer (bool): Whether to check modification dates at all. False
                suppresses the check for every rule, including those that ask for it,
                and rewrites a title beginning "Newer " so the log does not claim a
                check that did not happen.
            logger: The logger to write to. Defaults to the named logger this module
                uses, which is what a caller running one rule on its own gets.
            limits (dict): Per-level message limits for this rule's log section, passed
                through to the logger.

        Returns:
            tuple: (critical count, error count, warning count, total messages), from
            closing this rule's own log section. All four are zero for a rule whose glob
            matched nothing, which is not the same as a rule that ran and found nothing
            wrong: that one confirms each required file and so has messages to report.
            The caller in this module discards the result.

        An exception is logged on the way out and re-raised rather than swallowed, and
        it is logged by each nesting level it passes: twice here, and again by the suite
        above, so one failure appears three times in the log.

        Raises:
            ValueError: from ``from_abspath()``, if the path given is not inside a
                holdings tree the current environment knows.
            OSError: from ``get_modtime()``, if a file disappears between the glob and
                the date check.
        """

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.Pds3File.from_abspath(dirpath)
        lskip_ = len(pdsdir.root_)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root([pdsdir.root_, pdsdir.disk_])

        # Don't log if the source directory doesn't exist
        pattern = pdsdir.root_ + self.glob_pattern
        pattern = pattern.replace('$', pdsdir.volset_[:-1], 1)
        if '$' in pattern:
            if self.func is None:
                volname = pdsdir.volname
            else:
                volname = self.func(pdsdir.volname, *self.args)
            pattern = pattern.replace('$', volname, 1)

        abspaths = glob.glob(pattern)
        if not abspaths:
            return (0, 0, 0, 0)

        # Remove "Newer" at beginning of title if check_newer is False
        if not check_newer and self.title.startswith('Newer '):
            title = self.title[6:].capitalize()
        else:
            title = self.title

        missing = set()         # prevent duplicated messages
        out_of_date = set()
        confirmed = set()

        logger.open(title, dirpath, limits=limits, force=True)
        try:
            for sub in self.sublist:
                try:
                    for abspath in abspaths:

                        # Check exception list
                        exception_identified = False
                        for regex in self.exceptions:
                            if regex.fullmatch(abspath):
                                logger.info('Test skipped', abspath)
                                exception_identified = True
                                break

                        if exception_identified:
                            continue

                        path = abspath[lskip_:]

                        (requirement, count) = self.regex.subn(sub, path)
                        absreq = (pdsdir.root_ + requirement)
                        if count == 0:
                            logger.error('Invalid test', absreq)
                            continue

                        if not os.path.exists(absreq):
                            if absreq in missing:
                                continue

                            logger.error('Missing file', absreq)
                            for message in self.messages:
                                cmd = self.regex.sub(message, path)
                                cmd = cmd.partition('[x]')[0]
                                cmd = cmd.replace('[c]', 'initialize')
                                cmd = cmd.replace('[C]', 'initialize')
                                cmd = cmd.replace('[d]', pdsdir.root_)
                                if cmd not in PdsDependency.COMMANDS_TO_TYPE:
                                    PdsDependency.COMMANDS_TO_TYPE.append(cmd)

                            missing.add(absreq)
                            continue

                        if self.newer and check_newer:
                            source_modtime = PdsDependency.get_modtime(abspath,
                                                                       logger)
                            requirement_modtime = PdsDependency.get_modtime(absreq,
                                                                            logger)

                            if requirement_modtime < source_modtime:
                                if absreq in out_of_date:
                                    continue

                                logger.error('File out of date', absreq)
                                for message in self.messages:
                                    cmd = self.regex.sub(message, path)
                                    if '[C]' in cmd:
                                        cmd = cmd.replace('[x]', '')
                                    else:
                                        cmd = cmd.partition('[x]')[0]
                                    cmd = cmd.replace('[c]', 'repair')
                                    cmd = cmd.replace('[C]', 'reinitialize')
                                    cmd = cmd.replace('[d]', pdsdir.root_)
                                    if cmd not in PdsDependency.COMMANDS_TO_TYPE:
                                        PdsDependency.COMMANDS_TO_TYPE.append(cmd)

                                out_of_date.add(absreq)
                                continue

                        if absreq in confirmed:
                            continue

                        logger.info('Confirmed', absreq)
                        confirmed.add(absreq)

                except (Exception, KeyboardInterrupt) as e:
                    logger.exception(e)
                    raise

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

    @staticmethod
    def test_suite(key, dirpath, check_newer=True, logger=None, limits={},
                   handlers=[]):
        """Run every rule of one suite against one volume, inside one log section.

        The rules run in the order they were constructed in, and a rule that fails does
        not stop the suite only in the sense that a failed dependency is a logged error
        rather than an exception; anything that does raise is logged and re-raised, and
        the rest of the suite does not run.

        Parameters:
            key (str): The suite's name, which must be one a rule registered under.
            dirpath (str): The volume directory, passed to each rule.
            check_newer (bool): Whether to check modification dates, passed to each
                rule.
            logger: The logger to write to. Defaults to the named logger this module
                uses.
            limits (dict): Per-level message limits, applied to this section and to each
                rule's section inside it.
            handlers (list): Extra log handlers for the duration of this section, which
                is how a run gets one log file per volume.

        Returns:
            tuple: (critical count, error count, warning count, total messages), from
            closing the suite's section. These cover every rule in the suite, since the
            rules' own sections are nested inside it.

        Raises:
            KeyError: from the ``__getitem__()`` that looks the name up in
                ``DEPENDENCY_SUITES``, for a suite no rule registered under. Every name
                ``TESTS`` produces is registered, so this reaches a caller that names
                its own suite and no other.
            ValueError: from ``from_abspath()``, if the path given is not inside a
                holdings tree the current environment knows.
        """

        dirpath = os.path.abspath(dirpath)
        pdsdir = pdsfile.Pds3File.from_abspath(dirpath)

        logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
        logger.replace_root(pdsdir.root_)
        logger.open('Dependency test suite "%s"' % key, dirpath, limits=limits,
                    force=True, handler=handlers)

        try:
            for dep in PdsDependency.DEPENDENCY_SUITES[key]:
                dep.test1(dirpath, check_newer, limits=limits, logger=logger)

        except (Exception, KeyboardInterrupt) as e:
            logger.exception(e)
            raise

        finally:
            (fatal, errors, warnings, tests) = logger.close()

        return (fatal, errors, warnings, tests)

################################################################################
# General test suite
################################################################################

for thing in ['volumes', 'calibrated', 'diagrams', 'metadata', 'previews']:

    if thing == 'volumes':
        thing_ = ''
    else:
        thing_ = '_' + thing

    Thing = thing.capitalize()

    _ = PdsDependency(
        'Newer checksums for %s'             % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        r'checksums-%s/\1/\2%s_md5.txt'      % (thing, thing_),
        [r'pdschecksums --[c] [d]%s/\1/\2'   % thing,
         r'pdsinfoshelf --[C] [d]%s/\1/\2'   % thing],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer info shelf files for %s'      % thing,
        'checksums-%s/$/$%s_md5.txt'         % (thing, thing_),
        r'checksums-%s/(.*?)/(.*)%s_md5\.txt' % (thing, thing_),
        [r'_infoshelf-%s/\1/\2_info.pickle'  % thing,
         r'_infoshelf-%s/\1/\2_info.py'      % thing],
        r'pdsinfoshelf --[C] [d]%s/\1/\2'    % thing,
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer archives for %s'              % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        r'archives-%s/\1/\2%s.tar.gz'        % (thing, thing_),
        [r'pdsarchives --[c] [d]%s/\1/\2'    % thing,
         r'pdschecksums --[c] [d]archives-%s/\1[x]/\2%s.tar.gz' % (thing, thing_),
         r'pdsinfoshelf --[C] [d]archives-%s/\1[x]/\2%s.tar.gz' % (thing, thing_)],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer checksums for archives-%s'                       % thing,
        'archives-%s/$*/$%s.tar.gz'                             % (thing, thing_),
        r'archives-%s/(.*)/(.*)%s\.tar\.gz'                     % (thing, thing_),
        r'checksums-archives-%s/\1%s_md5.txt'                   % (thing, thing_),
        [r'pdschecksums --[c] [d]archives-%s/\1[x]/\2%s.tar.gz' % (thing, thing_),
         r'pdsinfoshelf --[C] [d]archives-%s/\1[x]/\2%s.tar.gz' % (thing, thing_)],
        suite='general', newer=True)

    _ = PdsDependency(
        'Newer info shelf files for archives-%s'                % thing,
        'checksums-archives-%s/$*%s_md5.txt'                    % (thing, thing_),
        r'checksums-archives-%s/(.*)%s_md5\.txt'                % (thing, thing_),
        [r'_infoshelf-archives-%s/\1_info.pickle'               % thing,
         r'_infoshelf-archives-%s/\1_info.py'                   % thing],
        r'pdsinfoshelf --[c] [d]archives-%s/\1'                 % thing,
        suite='general', newer=True)

for thing in ['volumes', 'metadata', 'calibrated']:

    _ = PdsDependency(
        'Newer link shelf files for %s'      % thing,
        '%s/$/$'                             % thing,
        r'%s/(.*?)/(.*)'                     % thing,
        [r'_linkshelf-%s/\1/\2_links.pickle' % thing,
         r'_linkshelf-%s/\1/\2_links.py'     % thing],
        r'pdslinkshelf --[C] [d]%s/\1/\2'    % thing,
        suite='general', newer=True)

################################################################################
# Metadata tests
################################################################################

# General metadata including *_index.tab
_ = PdsDependency(
    'Metadata index table for each volume',
    'volumes/$/$',
    r'volumes/([^/]+?)(?:|_v[\d.]+)/(.*?)',
    r'metadata/\1/\2/\2_index.tab',
    [r'cp [d]volumes/\1/\2/index/index.tab [d]metadata/\1/\2/\2_index.tab',
     r'<EDIT> [d]metadata/\1/\2/\2_index.tab'],
    suite='metadata', newer=False)

_ = PdsDependency(
    'Label for every metadata table',
    'metadata/$*/$/*.[tc][as][bv]',
    r'metadata/(.*)\.(...)',
    r'metadata/\1.lbl',
    r'<LABEL> [d]metadata/\1.\2',
    suite='metadata', newer=False)

_ = PdsDependency(
    'Newer index shelf for every metadata table',
    'metadata/$*/$/*.tab',
    r'metadata/(.*)\.tab',
    [r'_indexshelf-metadata/\1.pickle',
     r'_indexshelf-metadata/\1.py'],
    r'pdsindexshelf --[C] [d]metadata/\1.tab',
    suite='metadata', newer=True,
    exceptions=[r'.*GO_0xxx_v1.*', r'.*_inventory\.tab'])

# More metadata suites
for (name, suffix, newer) in [
            ('supplemental'  , 'supplemental_index.tab' , True),
            ('inventory'     , 'inventory.csv'          , False),
            ('jupiter'       , 'jupiter_summary.tab'    , False),
            ('saturn'        , 'saturn_summary.tab'     , False),
            ('uranus'        , 'uranus_summary.tab'     , False),
            ('neptune'       , 'neptune_summary.tab'    , False),
            ('pluto'         , 'pluto_summary.tab'      , False),
            ('pluto'         , 'charon_summary.tab'     , False),
            ('rings'         , 'ring_summary.tab'       , False),
            ('moons'         , 'moon_summary.tab'       , False),
            ('sky'           , 'sky_summary.tab'        , False),
            ('body'          , 'body_summary.tab'       , False),
            ('raw_image'     , 'raw_image_index.tab'    , False),
            ('profile'       , 'profile_index.tab'      , False),
            ('obsindex'      , 'obsindex.tab'           , False),
            ('sl9'           , 'sl9_mosaic_index.tab'   , False)]:

    _ = PdsDependency(
        name.capitalize() + ' metadata required',
        'volumes/$/$',
        r'volumes/([^/]+?)(?:|_v[\d.]+)/(.*?)',
        r'metadata/\1/\2/\2_' + suffix,
        r'<METADATA> [d]volumes/\1/\2 -> [d]metadata/\1/\2/\2_' + suffix,
        suite=name, newer=newer)

################################################################################
# Cumulative index tests where the suffix is "99", "999", or "9_9999"
################################################################################

def cumname(volname, nines):
    """Return the name of the cumulative volume a volume's tables are gathered into.

    A cumulative index gathers the tables of a group of volumes under one volume name
    whose numeric part is all nines. Which digits are replaced is what ``nines`` says:
    its length is the number of trailing characters of the volume name that the nines
    stand in for, so "999" turns COISS_1010 into COISS_1999 and "99" turns RPX_0001 into
    RPX_0099.

    The New Horizons volumes are the exception, and their name is assembled from fixed
    positions rather than by counting from the end: "NHxx", then the volume name's fifth
    through eighth characters, then "999". So NHJULO_1001 becomes NHxxLO_1999 -- the two
    characters naming the target replaced, the instrument and mission phase kept, the
    last three digits replaced. That form is selected by passing "NH" rather than a run
    of nines, and it is right only for a name of the length these volumes have.

    Parameters:
        volname (str): The volume name, which is not checked. The nines case reads its
            last characters and the New Horizons case its fifth through eighth.
        nines (str): Either a run of nines, optionally with an underscore in it, or the
            literal "NH". The choice is made on the first character alone.

    Returns:
        str: The cumulative volume's name.
    """

    if nines[0] == '9':
        return volname[:-len(nines)] + nines
    return 'NHxx' + volname[4:8] + '999'

for nines in ('99', '999', '9_9999'):

    digits = nines.replace('9', r'\d')
    if nines == '9_9999':
        questions = '[01]_????'
    else:
        questions = nines.replace('9', '?')
    name = 'cumindex' + nines

    _ = PdsDependency(
        'Cumulative version of every metadata table',
        'metadata/$/$/*.[tc][as][bv]',
        rf'metadata/(.*?)/(.*){digits}/\2{digits}(_.*?)\.(tab|csv)',
        rf'metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4',
        [(rf'cat [d]metadata/\1/\2{questions}/\2{questions}\3.\4 '
          rf'> [d]metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4'),
          rf'<LABEL> [d]metadata/\1/\g<2>{nines}/\g<2>{nines}\3.\4'],
        suite=name, newer=True, exceptions=[r'.*_sl9_.*\.tab'])

_ = PdsDependency(
    'Cumulative version of every metadata table',
    'metadata/$/$/*.[tc][as][bv]',
    r'metadata/(.*?)/NH(..)(..)_([12])(\d\d\d)/NH\2\3_\4\5(_.*?)\.(tab|csv)',
    r'metadata/\1/NHxx\3_\g<4>999/NHxx\3_\g<4>999\6.\7',
    (r'cat [d]metadata/\1/NH??\3_\4???/NH??\3_\4???\6.\7 '
     r'> [d]metadata/\1/NHxx\3_\g<4>999/NHxx\3_\g<4>999\6.\7'),
    suite='cumindexNH', newer=True)

for nines in ('99', '999', '9_9999', 'NH'):
    name = 'cumindex' + nines

    _ = PdsDependency(
        'Label for every cumulative metadata table',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'metadata/\1/\2/\2\3.lbl',
        r'<LABEL> [d]metadata/\1/\2/\2\3.\4',
        suite=name, newer=False, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer checksums for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'checksums-metadata/\1/\2_metadata_md5.txt',
        [r'pdschecksums --[c] [d]metadata/\1/\2',
         r'pdsinfoshelf --[C] [d]metadata/\1/\2'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer info shelf files for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        [r'_infoshelf-metadata/\1/\2_info.pickle',
         r'_infoshelf-metadata/\1/\2_info.py'],
        r'pdsinfoshelf --[C] [d]metadata/\1/\2',
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer index shelf files for cumulative metadata',
        'metadata/$/$/*.tab',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.tab',
        [r'_indexshelf-metadata/\1/\2/\2\3.pickle',
         r'_indexshelf-metadata/\1/\2/\2\3.py'],
        r'pdsindexshelf --[C] [d]metadata/\1/\2/\2\3.tab',
        suite=name, newer=True, func=cumname, args=(nines,),
        exceptions=[r'.*_inventory\.tab'])

    _ = PdsDependency(
        'Newer link shelf files for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        [r'_linkshelf-metadata/\1/\2_links.pickle',
         r'_linkshelf-metadata/\1/\2_links.py'],
        r'pdslinkshelf --[C] [d]metadata/\1/\2',
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer archives for cumulative metadata',
        'metadata/$/$/*.[tc][as][bv]',
        r'metadata/(.*?)/(.*?)/\2(_.*?)\.(tab|csv)',
        r'archives-metadata/\1/\2_metadata.tar.gz',
        [r'pdsarchives --[c] [d]metadata/\1/\2',
         r'pdschecksums --[c] [d]archives-metadata/\1[x]/\2_metadata.tar.gz',
         r'pdsinfoshelf --[C] [d]archives-metadata/\1[x]/\2_metadata.tar.gz'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer checksums for cumulative archives-metadata',
        'archives-metadata/$/$_metadata.tar.gz',
        r'archives-metadata/(.*?)/(.*)_metadata.tar.gz',
        r'checksums-archives-metadata/\1_metadata_md5.txt',
        [r'pdschecksums --[c] [d]archives-metadata/\1[x]/\2_metadata.tar.gz',
         r'pdsinfoshelf --[C] [d]archives-metadata/\1[x]/\2_metadata.tar.gz'],
        suite=name, newer=True, func=cumname, args=(nines,))

    _ = PdsDependency(
        'Newer info shelf files for cumulative archives-metadata',
        'archives-metadata/$/$_metadata.tar.gz',
        r'archives-metadata/(.*?)/(.*)_metadata.tar.gz',
        r'checksums-archives-metadata/\1_metadata_md5.txt',
        r'pdsinfoshelf --[C] [d]archives-metadata/\1[x]/\2_metadata.tar.gz',
        suite=name, newer=True, func=cumname, args=(nines,))

################################################################################
# Preview tests
################################################################################

# For COCIRS_0xxx and COCIRS_1xxx
_ = PdsDependency(
    'Preview versions of every cube file',
    'volumes/$/$/EXTRAS/CUBE_OVERVIEW/*/*.JPG',
    r'volumes/(.*)/EXTRAS/CUBE_OVERVIEW/(.*)\.JPG',
    [r'previews/\1/DATA/CUBE/\2_thumb.jpg',
     r'previews/\1/DATA/CUBE/\2_small.jpg',
     r'previews/\1/DATA/CUBE/\2_med.jpg',
     r'previews/\1/DATA/CUBE/\2_full.jpg'],
    (r'<PREVIEW> [d]volumes/\1/EXTRAS/CUBE_OVERVIEW/(.*)\.JPG '
     r'-> [d]previews/\1/DATA/CUBE/\2_*.jpg'),
    suite='cocirs01', newer=True)

# For COCIRS_5xxx and COCIRS_6xxx
_ = PdsDependency(
    'Diagrams for every interferogram file',
    'volumes/$/$/BROWSE/*/*.PNG',
    r'volumes/(.*)/BROWSE/(.*?)\.PNG',
    [r'diagrams/\1/BROWSE/\2_thumb.jpg',
     r'diagrams/\1/BROWSE/\2_small.jpg',
     r'diagrams/\1/BROWSE/\2_med.jpg',
     r'diagrams/\1/BROWSE/\2_full.jpg'],
    r'<DIAGRAM> [d]volumes/\1/BROWSE/\2.PNG -> [d]diagrams/\1/BROWSE/*/\2_.jpg',
    suite='cocirs56', newer=False)

# For COISS_1xxx and COISS_2xxx
_ = PdsDependency(
    'Previews of every COISS image file',
    'volumes/$/$/data/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.png'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1*.jpg',
    suite='coiss12', newer=False)

_ = PdsDependency(
    'Calibrated versions of every COISS image file',
    'volumes/$/$/data/*/*.IMG',
    r'volumes/(.*)\.IMG',
    r'calibrated/\1_CALIB.IMG',
    r'<CALIBRATE> [d]volumes/\1.IMG -> [d]calibrated/\1_CALIB.IMG',
    suite='coiss12', newer=False)

# For COISS_3xxx
_ = PdsDependency(
    'Previews of every COISS derived map image',
    'volumes/$/$/data/images/*.IMG',
    r'volumes/(.*?)/data/images/(.*)\.IMG',
    [r'previews/\1/data/images/\2_thumb.jpg',
     r'previews/\1/data/images/\2_small.jpg',
     r'previews/\1/data/images/\2_med.jpg',
     r'previews/\1/data/images/\2_full.jpg'],
    r'<PREVIEW> [d]volumes/\1/data/images/\2.IMG -> [d]previews/\1/data/images/\2*.jpg',
    suite='coiss3', newer=True)

_ = PdsDependency(
    'Previews of every COISS derived map PDF',
    'volumes/$/$/data/maps/*.PDF',
    r'volumes/(.*?)/data/maps/(.*)\.PDF',
    [r'previews/\1/data/maps/\2_thumb.png',
     r'previews/\1/data/maps/\2_small.png',
     r'previews/\1/data/maps/\2_med.png',
     r'previews/\1/data/maps/\2_full.png'],
    r'<PREVIEW> [d]volumes/\1/data/maps/\2.PDF -> [d]previews/\1/data/maps/\2*.png',
    suite='coiss3', newer=True)

# For COUVIS_0xxx
_ = PdsDependency(
    'Previews of every COUVIS data file',
    'volumes/$/$/DATA/*/*.DAT',
    r'volumes/COUVIS_0xxx(|_v[\.\d]+)/(.*)\.DAT',
    [r'previews/COUVIS_0xxx/\2_thumb.png',
     r'previews/COUVIS_0xxx/\2_small.png',
     r'previews/COUVIS_0xxx/\2_med.png',
     r'previews/COUVIS_0xxx/\2_full.png'],
    r'<PREVIEW> [d]volumes/COUVIS_0xxx\1/\2.DAT -> [d]previews/COUVIS_0xxx/\2_*.png',
    suite='couvis', newer=False)

# For COVIMS_0xxx
_ = PdsDependency(
    'Previews of every COVIMS cube',
    'volumes/$/$/data/*/*.qub',
    r'volumes/(.*)\.qub',
    [r'previews/\1_thumb.png',
     r'previews/\1_small.png',
     r'previews/\1_med.png',
     r'previews/\1_full.png'],
    r'<PREVIEW> [d]volumes/\1.qub -> [d]previews/\1_*.png',
    suite='covims', newer=False)

# For CORSS_8xxx
_ = PdsDependency(
    'Previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1 -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'GEO previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_GEO_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1/\2_\3/ -> [d]previews/CORSS_8xxx/\1/\2_\3/\3_GEO_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'TAU previews for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_thumb.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_small.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_med.jpg',
     r'previews/CORSS_8xxx/\1/\2_\3/\3_TAU_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1/\2_\3/ -> [d]previews/CORSS_8xxx/\1/\2_\3/\3_TAU_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Diagrams for every CORSS_8xxx data directory',
    'volumes/$/$/data/Rev*/Rev*/*',
    r'volumes/CORSS_8xxx[^/]*/(CORSS_8001/data/Rev.../Rev.....?)/(Rev.....?)_(RSS_...._..._..._.)',
    [r'diagrams/CORSS_8xxx/\1_\3_thumb.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_small.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_med.jpg',
     r'diagrams/CORSS_8xxx/\1_\3_full.jpg'],
    r'<DIAGRAM> [d]volumes/CORSS_8xxx*/\1 -> [d]diagrams/CORSS_8xxx/\1_\3_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx browse PDF',
    'volumes/$/$/browse/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx Rev PDF',
    'volumes/$/$/data/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every CORSS_8xxx data PDF',
    'volumes/$/$/data/Rev*/Rev*/Rev*/*.pdf',
    r'volumes/CORSS_8xxx[^/]*/(.*)\.pdf',
    [r'previews/CORSS_8xxx/\1_thumb.jpg',
     r'previews/CORSS_8xxx/\1_small.jpg',
     r'previews/CORSS_8xxx/\1_med.jpg',
     r'previews/CORSS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/CORSS_8xxx/\1.pdf -> [d]previews/CORSS_8xxx/\1_*.jpg',
    suite='corss_8xxx', newer=False)

# For COUVIS_8xxx
_ = PdsDependency(
    'Previews of every COUVIS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COUVIS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COUVIS_8xxx/\1_thumb.jpg',
     r'previews/COUVIS_8xxx/\1_small.jpg',
     r'previews/COUVIS_8xxx/\1_med.jpg',
     r'previews/COUVIS_8xxx/\1_full.jpg',
     r'diagrams/COUVIS_8xxx/\1_thumb.jpg'],
    r'<PREVIEW> [d]volumes/COUVIS_8xxx/\1_TAU01KM.TAB -> [d]previews/COUVIS_8xxx/\1_*.jpg',
    suite='couvis_8xxx', newer=False,
    exceptions=['.*2005_139_PSICEN_E.*',
                '.*2005_139_THEHYA_E.*',
                '.*2007_038_SAO205839_I.*',
                '.*2010_148_LAMAQL_E.*'])

_ = PdsDependency(
    'Diagrams of every COUVIS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COUVIS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'diagrams/COUVIS_8xxx/\1_thumb.jpg',
     r'diagrams/COUVIS_8xxx/\1_small.jpg',
     r'diagrams/COUVIS_8xxx/\1_med.jpg',
     r'diagrams/COUVIS_8xxx/\1_full.jpg'],
    r'<DIAGRAM> [d]volumes/COUVIS_8xxx/\1_TAU01KM.TAB -> [d]diagrams/COUVIS_8xxx/\1_*.jpg',
    suite='couvis_8xxx', newer=False,
    exceptions=['.*2005_139_PSICEN_E.*',
                '.*2005_139_THEHYA_E.*',
                '.*2007_038_SAO205839_I.*',
                '.*2010_148_LAMAQL_E.*'])

# For COVIMS_8xxx
_ = PdsDependency(
    'Previews of every COVIMS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COVIMS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/COVIMS_8xxx/\1_TAU01KM.TAB -> [d]previews/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

_ = PdsDependency(
    'Diagrams of every COVIMS_8xxx profile',
    'volumes/$/$/data/*_TAU01KM.TAB',
    r'volumes/COVIMS_8xxx[^/]*/(.*)_TAU01KM\.TAB',
    [r'diagrams/COVIMS_8xxx/\1_thumb.jpg',
     r'diagrams/COVIMS_8xxx/\1_small.jpg',
     r'diagrams/COVIMS_8xxx/\1_med.jpg',
     r'diagrams/COVIMS_8xxx/\1_full.jpg'],
    r'<DIAGRAM> [d]volumes/COVIMS_8xxx/\1_TAU01KM.TAB -> [d]diagrams/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

_ = PdsDependency(
    'Previews of every COVIMS_8xxx PDF',
    'volumes/$/$/browse/*.PDF',
    r'volumes/COVIMS_8xxx[^/]*/(.*)\.PDF',
    [r'previews/COVIMS_8xxx/\1_thumb.jpg',
     r'previews/COVIMS_8xxx/\1_small.jpg',
     r'previews/COVIMS_8xxx/\1_med.jpg',
     r'previews/COVIMS_8xxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/COVIMS_8xxx/\1.PDF -> [d]previews/COVIMS_8xxx/\1_*.jpg',
    suite='covims_8xxx', newer=False)

# For EBROCC_xxxx
_ = PdsDependency(
    'Previews of every EBROCC browse PDF',
    'volumes/$/$/BROWSE/*.PDF',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.PDF',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/EBROCC_xxxx/\1.PDF -> [d]previews/EBROCC_xxxx/\1_*.jpg',
    suite='ebrocc_xxxx', newer=False)

_ = PdsDependency(
    'Previews of every EBROCC profile',
    'volumes/$/$/data/*/*.TAB',
    r'volumes/EBROCC_xxxx[^/]*/(.*)\.TAB',
    [r'previews/EBROCC_xxxx/\1_thumb.jpg',
     r'previews/EBROCC_xxxx/\1_small.jpg',
     r'previews/EBROCC_xxxx/\1_med.jpg',
     r'previews/EBROCC_xxxx/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/EBROCC_xxxx/\1.TAB -> [d]previews/EBROCC_xxxx/\1_*.jpg',
    suite='ebrocc_xxxx', newer=False)

# For GO_xxxx
_ = PdsDependency(
    'Previews of every GO image file, depth 2',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews2', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 3',
    'volumes/$/$/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews3', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 4',
    'volumes/$/$/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews4', newer=True)

_ = PdsDependency(
    'Previews of every GO image file, depth 5',
    'volumes/$/$/*/*/*/*.IMG',
    r'volumes/(.*)\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.IMG -> [d]previews/\1_*.jpg',
    suite='go_previews5', newer=True)

# For HST*x_xxxx
_ = PdsDependency(
    'Previews of every HST image label',
    'volumes/$/$/data/*/*.LBL',
    r'volumes/(HST.._....)(|_v[\.\d]+)/(HST.*)\.LBL',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1/\3.LBL -> [d]previews/\1/\3_*.jpg',
    suite='hst', newer=False)

# For JNOSRU_xxxx
_ = PdsDependency(
    'Previews of every JNOSRU image file',
    'volumes/$/$/DATA/*/*/*/*.FIT',
    r'volumes/(.*)\.FIT',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1.FIT -> [d]previews/\1*.jpg',
    suite='jnosru', newer=False)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, stripping version number if present
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[\.\d]+)/(NH\w+/data/\w+/\w{24})(|_[0-9]+)\.fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1\2/\3\4.fit -> [d]previews/\1/\3_*.jpg',
    suite='nhbrowse', newer=False)

# For NHxxLO_xxxx and NHxxMV_xxxx browse, retaining version number
_ = PdsDependency(
    'Previews of every NH image file',
    'volumes/$/$/data/*/*.fit',
    r'volumes/(NHxx.._....)(|_v[\.\d]+)/(NH.*?)\.fit',
    [r'previews/\1/\3_thumb.jpg',
     r'previews/\1/\3_small.jpg',
     r'previews/\1/\3_med.jpg',
     r'previews/\1/\3_full.jpg'],
    r'<PREVIEW> [d]volumes/\1\2/\3.fit -> [d]previews/\1/\3_*.jpg',
    suite='nhbrowse_vx', newer=False)

# For VGISS_[5678]xxx
_ = PdsDependency(
    'Previews of every VGISS image file',
    'volumes/$/$/data/*/*RAW.IMG',
    r'volumes/(.*)_RAW\.IMG',
    [r'previews/\1_thumb.jpg',
     r'previews/\1_small.jpg',
     r'previews/\1_med.jpg',
     r'previews/\1_full.jpg'],
    r'<PREVIEW> [d]volumes/\1_RAW.IMG -> [d]previews/\1_*.jpg',
    suite='vgiss', newer=True)

# For VG_28xxx
_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_280[12]/*DATA/*/[PU][SUN][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/([PUR][SUN]\d)(...)(\w+)\.LBL',
    [r'previews/\1/\2/\4xxx\6_preview_thumb.png',
     r'previews/\1/\2/\4xxx\6_preview_small.png',
     r'previews/\1/\2/\4xxx\6_preview_med.png',
     r'previews/\1/\2/\4xxx\6_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5\6.* -> [d]previews/\1/\2/\4xxx\6_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_2803/*RINGS/*DATA/*/R[SUN][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/([PUR][SUN])(\d..)(\w+)\.LBL',
    [r'previews/\1/\2/\4xxx\6_preview_thumb.png',
     r'previews/\1/\2/\4xxx\6_preview_small.png',
     r'previews/\1/\2/\4xxx\6_preview_med.png',
     r'previews/\1/\2/\4xxx\6_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5\6.* -> [d]previews/\1/\2/\4xxx\6_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

_ = PdsDependency(
    'Previews of every VG_28xx data file',
    'volumes/$/VG_2810/DATA/IS[0-9]_P[0-9][0-9][0-9][0-9]*.LBL',
    r'volumes/([^/]+)/([^/]+)(.*)/(IS\d_P\d\d\d\d)(.*)\.LBL',
    [r'previews/\1/\2/\4_preview_thumb.png',
     r'previews/\1/\2/\4_preview_small.png',
     r'previews/\1/\2/\4_preview_med.png',
     r'previews/\1/\2/\4_preview_full.png'],
    r'<PREVIEW> [d]volumes/\1/\2\3/\4\5.* -> [d]previews/\1/\2/\4_preview_*.png',
    suite='vg_28xx', newer=True, exceptions=[r'.*/[PUR].*[01]\d\.LBL'])

################################################################################
################################################################################

def test(pdsdir, logger=None, limits={}, check_newer=True, handlers=[]):
    """Run every suite one volume's path selects, in the order the table lists them.

    This is the library entry point, and the one ``re_validate`` calls. It is the only
    place the path-to-suite table is consulted: a caller that already knows which suite
    it wants goes to ``PdsDependency.test_suite()`` instead.

    Each suite gets its own log section, and the results of each are discarded here.
    What a run found is read off the logger by the caller, or off the class-level list
    of repair commands, rather than returned.

    Parameters:
        pdsdir: The volume. Only its absolute path is used, both to select the suites
            and as each suite's target.
        logger: The logger to write to. Defaults to the named logger this module
            uses.
        limits (dict): Per-level message limits, passed to each suite.
        check_newer (bool): Whether to check modification dates. ``re_validate`` passes
            False for its ``--timeless`` option.
        handlers (list): Extra log handlers, passed to each suite, which is how a run
            gets one log file per volume.

    Raises:
        ValueError: from ``test_suite()``, if the path is not inside a holdings tree the
            current environment knows.
    """

    logger = logger or pdslogger.PdsLogger.get_logger(LOGNAME)
    path = pdsdir.abspath
    for suite in TESTS.all(path):
        _ = PdsDependency.test_suite(suite, path, check_newer=check_newer,
                                     limits=limits, logger=logger,
                                     handlers=handlers)

################################################################################
################################################################################

def main():
    """Check every volume named on the command line and print what would repair it.

    The command line is read from ``sys.argv`` directly rather than through a parameter,
    so this takes no arguments and a caller wanting to drive it has to set ``sys.argv``.

    Everything is validated before anything is tested, and each failure ends the run
    with a message and status 1: a path that is neither a volume nor a volume set
    directory, one outside ``volumes/``, one that does not exist, one under a checksum
    or archive category, and a volume whose name is not a volume ID. A volume set is
    expanded into its volumes at that point, so what is tested is always volumes.

    The run's own log is opened once and each volume's log file is attached for the
    duration of that volume, so a volume's findings are in its own file as well as in
    the run's. The repair commands are printed at the end, after the log is closed,
    across every volume of the run and in the order they were first worked out.

    Where ``--log`` goes when it is not given is worked out here rather than through the
    shared helper the other tools call, against a copy of the environment variable's
    name that this module declares for itself. The behavior is the same one: the
    variable if it is set, and no duplicate log tree if it is not.

    Raises:
        SystemExit: from ``sys.exit()``, with status 1 for any of the rejected command
            lines above, status 2 from ``parse_args()`` for one argparse cannot classify
            and 0 for ``--help``, and at the end of a completed run with status 1 if
            anything was logged as critical or as an error and 0 if nothing was. **A
            missing or stale dependency is an error, so a run that finds work to do
            exits 1.**
        ValueError: from ``from_abspath()``, for a path no holdings tree the current
            environment contains.
        Exception: whatever ``test()`` raises escapes, after being logged and after the
            log is closed and the repair commands printed. The status assigned in the
            handler is not reached, because the exception propagates instead of the
            function returning to its ``sys.exit()``.
    """

    # Set up parser
    parser = argparse.ArgumentParser(
        description='pdsdependency: Check all required files associated with ' +
                    'with a volume, confirming that they exist and that '      +
                    'their creation dates are consistent.')

    parser.add_argument('volume', nargs='+', type=str,
                        help='The path to the root directory of a volume or '  +
                             'a volume set.')

    parser.add_argument('--log', '-l', type=str, default='',
                        help='Optional root directory for a duplicate of the ' +
                             'log files. If not specified, the value of '      +
                             'environment variable "%s" ' % LOGROOT_ENV        +
                             'is used. In addition, individual logs are '      +
                             'written into the "logs" directory parallel to '  +
                             '"holdings". Logs are created inside the '        +
                             '"pdsdependency" subdirectory of each log root '  +
                             'directory.'
                             )

    parser.add_argument('--quiet', '-q', action='store_true',
                        help='Do not also log to the terminal.')

    # Parse and validate the command line
    args = parser.parse_args()

    status = 0

    # Define the logging directory
    if args.log == '':
        try:
            args.log = os.environ[LOGROOT_ENV]
        except KeyError:
            args.log = None

    # Validate the paths
    for path in args.volume:
        path = os.path.abspath(path)
        pdsdir = pdsfile.Pds3File.from_abspath(path)
        if not pdsdir.is_volume_dir and not pdsdir.is_volset_dir:
            print('pdsdependency error: '
                  'not a volume or volume set directory: ' + pdsdir.logical_path)
            sys.exit(1)

        if pdsdir.category_ != 'volumes/':
            print('pdsdependency error: '
                  'not a volume or volume set directory: ' + pdsdir.logical_path)
            sys.exit(1)

    # Initialize the logger
    logger = pdslogger.PdsLogger(LOGNAME)
    pdsfile.Pds3File.set_log_root(args.log)

    if not args.quiet:
        logger.add_handler(pdslogger.stdout_handler)

    if args.log:
        path = os.path.join(args.log, 'pdsdependency')
        error_handler = pdslogger.error_handler(path)
        logger.add_handler(error_handler)

    # Generate a list of file paths before logging
    paths = []
    for path in args.volume:

        if not os.path.exists(path):
            print('No such file or directory: ' + path)
            sys.exit(1)

        path = os.path.abspath(path)
        pdsf = pdsfile.Pds3File.from_abspath(path)

        if pdsf.checksums_:
            print('No pdsdependency for checksum files: ' + path)
            sys.exit(1)

        if pdsf.archives_:
            print('No pdsdependency for archive files: ' + path)
            sys.exit(1)

        if pdsf.is_volset_dir:
            paths += [os.path.join(path, c) for c in pdsf.childnames]

        else:
            paths.append(os.path.abspath(path))

    # Check for valid volume IDs
    for path in paths:
        basename = os.path.basename(path)
        if not pdsfile.Pds3File.VOLNAME_REGEX_I.match(basename):
            print('Invalid volume ID: ' + path)
            sys.exit(1)

    # Only show paths starting with "holdings/"
    roots = set()
    for path in paths:
        parts = path.partition('/holdings/')
        if parts[1]:
            roots.add(parts[0] + parts[1])

    logger.add_root(*roots)

    # Loop through paths...
    args = list(sys.argv)
    args[0] = args[0].rpartition('/')[-1]
    logger.open(' '.join(args))
    try:
        for path in paths:
            pdsdir = pdsfile.Pds3File.from_abspath(path)

            # Save logs in up to two places
            logfiles = _common.log_paths_for(pdsdir, 'log_path_for_volume',
                                             '_dependency', dir='pdsdependency')

            # Create all the handlers for this level in the logger
            local_handlers = []
            for logfile in logfiles:
                logfile = logfile.replace('/volumes/', '/')
                local_handlers.append(pdslogger.file_handler(logfile))
                logdir = os.path.split(logfile)[0]

                # These handlers are only used if they don't already exist
                error_handler = pdslogger.error_handler(logdir)
                local_handlers += [error_handler]

            try:
                for logfile in logfiles:
                    logger.info('Log file', logfile)

                test(pdsdir, logger=logger, handlers=local_handlers)

            except (Exception, KeyboardInterrupt) as e:
                logger.exception(e)
                raise

    except (Exception, KeyboardInterrupt) as e:
        logger.exception(e)
        status = 1
        raise

    finally:
        (fatal, errors, _warnings, _tests) = logger.close()
        if fatal or errors:
            status = 1

        if PdsDependency.COMMANDS_TO_TYPE:
            print('Steps required:')
            for cmd in PdsDependency.COMMANDS_TO_TYPE:
                print('  ', cmd)

    sys.exit(status)

if __name__ == '__main__':
    main()
