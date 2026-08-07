##########################################################################################
# tests/holdings_maintenance/support.py
#
# Shared machinery for the maintenance-tool tests: building a disposable holdings
# tree from a declared source subset, running a tool as a subprocess, applying the
# fixed corruption scenarios, and normalizing tool output for golden comparison.
#
# Nothing here compares raw bytes of a generated artifact. The tools write md5
# files in os.walk order and .tar.gz members in filesystem order, neither of which
# is portable; every comparison goes through one of the normalizers below.
##########################################################################################

import contextlib
import difflib
import hashlib
import importlib
import io
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

# Repository root: tests/holdings_maintenance/support.py -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Golden artifacts for these tests. The "full/" level matches the rest of the
# golden tree (tests/golden/full/pds3, .../pds4).
GOLDEN_DIR = REPO_ROOT / 'tests' / 'golden' / 'full' / 'holdings_maintenance'

# The tools, addressed as importable modules. Subprocesses run
# `python -m <module>`, which enters each tool through exactly the main() its
# console script calls, and which is also the invocation settled on for the three
# tools that will never get a console script.
TOOL_MODULES = {
    'crlf':           'pdsfile.holdings_maintenance.pds3.crlf',
    'pdsarchives':    'pdsfile.holdings_maintenance.pds3.pdsarchives',
    'pdschecksums':   'pdsfile.holdings_maintenance.pds3.pdschecksums',
    'pdsdependency':  'pdsfile.holdings_maintenance.pds3.pdsdependency',
    'pdsindexshelf':  'pdsfile.holdings_maintenance.pds3.pdsindexshelf',
    'pdsinfoshelf':   'pdsfile.holdings_maintenance.pds3.pdsinfoshelf',
    'pdslinkshelf':   'pdsfile.holdings_maintenance.pds3.pdslinkshelf',
    'pds4archives':   'pdsfile.holdings_maintenance.pds4.pds4archives',
    'pds4checksums':  'pdsfile.holdings_maintenance.pds4.pds4checksums',
    'pds4indexshelf': 'pdsfile.holdings_maintenance.pds4.pds4indexshelf',
    'pds4infoshelf':  'pdsfile.holdings_maintenance.pds4.pds4infoshelf',
    'pds4linkshelf':  'pdsfile.holdings_maintenance.pds4.pds4linkshelf',
    'shelf_consistency_check':
        'pdsfile.holdings_maintenance.pds3.shelf_consistency_check',
    'show_opus_products': 'pdsfile.tools.show_opus_products',
}

HOLDINGS_DIRNAME = {'pds3': 'holdings', 'pds4': 'pds4-holdings'}

# The tools that import no PdsFile class and read neither holdings root: they walk
# or read exactly the paths named on their command line. Only these may be driven
# by run_tool_in_process() or run_tool_without_holdings(). Every other tool builds
# PdsFile objects against a class-level cache keyed by logical path, and the test
# session preloads the real holdings tree, so an in-process call can resolve a
# temporary-tree path back to the real one.
HOLDINGS_FREE_TOOLS = frozenset({'crlf', 'shelf_consistency_check'})

# Tools that exit 0 even after logging ERRORs, because main() never feeds its
# failure flag to sys.exit -- a --validate that reports checksum mismatches still
# exits 0. That is a defect; it is pinned as current behavior here rather than
# fixed, so whichever change gives these two tools an exit status has to update
# these expectations deliberately.
TOOLS_WITHOUT_EXIT_STATUS = frozenset({'pdschecksums', 'pds4checksums'})

TOOL_TIMEOUT = 600      # seconds; every subset here runs in well under a second


def expected_error_exit_code(tool):
    """Return the exit code a tool uses today to report logged errors.

    Args:
        tool: A key of TOOL_MODULES.

    Returns:
        int: 1 for the nine tools that end in sys.exit(status), 0 for the two that
        do not.
    """

    return 0 if tool in TOOLS_WITHOUT_EXIT_STATUS else 1


def md5_of(path):
    """Return the hex md5 digest of a file.

    Args:
        path: Path to the file.

    Returns:
        str: The lowercase hex digest.
    """

    digest = hashlib.md5()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            digest.update(block)

    return digest.hexdigest()


def missing_sources(root, sources):
    """Return the reasons a declared source subset is unusable under a holdings root.

    A declared path that is absent, the wrong size, or has different content is
    treated identically: the module that declared it must skip, because its
    goldens were generated from specific bytes.

    Args:
        root: Path to the holdings root to check.
        sources: A sequence of (holdings-relative path, size, md5) tuples.

    Returns:
        dict[str, str]: A human-readable reason keyed by the relative path of each
        unusable file; empty if all are present and identical to what was declared.
    """

    reasons = {}
    for relpath, size, md5 in sources:
        abspath = Path(root) / relpath
        if not abspath.is_file():
            reasons[relpath] = f'{relpath}: missing'
            continue
        actual_size = abspath.stat().st_size
        if actual_size != size:
            reasons[relpath] = f'{relpath}: size {actual_size} != declared {size}'
            continue
        actual_md5 = md5_of(abspath)
        if actual_md5 != md5:
            reasons[relpath] = f'{relpath}: md5 {actual_md5} != declared {md5}'

    return reasons


class SourceStage:
    """A local, verified copy of the declared source files, shared by every module.

    Every module builds its own disposable tree, but they all draw on the same
    handful of source files. Reading and hashing those files straight from the
    holdings root once per module is expensive when the root is a network mount
    (measured at several minutes for the first module against the complete set),
    so each file is verified and staged locally the first time any module asks for
    it and copied from the stage thereafter.

    Attributes:
        directory: The staging directory for this flavor.
    """

    def __init__(self, directory):
        self.directory = Path(directory)
        self._verified = {}         # relpath -> None if usable, else the reason

    def ensure(self, root, sources):
        """Verify and stage a source table, returning the reasons any file is unusable.

        Args:
            root: The holdings root to read from.
            sources: A sequence of (holdings-relative path, size, md5) tuples.

        Returns:
            list[str]: One reason per unusable file; empty when all are staged.
        """

        pending = [entry for entry in sources if entry[0] not in self._verified]
        unusable = missing_sources(root, pending)
        for relpath, _, _ in pending:
            self._verified[relpath] = unusable.get(relpath)

        for relpath, _, _ in pending:
            if self._verified[relpath] is not None:
                continue
            target = self.directory / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(root) / relpath, target)

        return [self._verified[relpath] for relpath, _, _ in sources
                if self._verified[relpath] is not None]


class ToolTree:
    """A disposable holdings tree containing one declared source subset.

    Attributes:
        disk: The temporary directory that plays the role of the disk holding the
            tree. Both a `holdings/` and a `pds4-holdings/` directory live under
            it, and tool logs land in `logs/` beside them.
        holdings: The holdings root for this tree's flavor.
        flavor: 'pds3' or 'pds4'.
    """

    def __init__(self, disk, flavor, source_dir=None, paths=(), mtimes=None):
        self.disk = Path(disk)
        self.flavor = flavor
        self.holdings = self.disk / HOLDINGS_DIRNAME[flavor]
        self.source_dir = None if source_dir is None else Path(source_dir)
        self.paths = tuple(paths)
        self.mtimes = dict(mtimes or {})

    def reset(self):
        """Discard everything the tools wrote and rebuild the declared subset.

        Cheap (the sources are already staged locally), and it is what lets every
        test start from the same known tree instead of depending on the test
        before it.
        """

        assert self.source_dir is not None, 'this tree was not built from a source stage'
        for name in [*HOLDINGS_DIRNAME.values(), 'logs']:
            shutil.rmtree(self.disk / name, ignore_errors=True)
        _populate(self, self.source_dir)

    def path(self, relpath):
        """Return the absolute path of a holdings-relative path in this tree.

        Args:
            relpath: A holdings-relative path.

        Returns:
            pathlib.Path: The absolute path inside this tree.
        """

        return self.holdings / relpath

    @property
    def env(self):
        """Return the environment for a tool subprocess run against this tree.

        Both holdings env vars point inside the temporary tree, so a tool can
        never resolve a path back to the real holdings. PDS_LOG_ROOT is removed so
        logs land in `<disk>/logs/`, and TZ is pinned so that shelf sidecars --
        which format modification times in local time -- are reproducible.

        PYTHONPATH names this checkout's src/, so a tool subprocess runs the code
        these tests belong to. Without it the subprocess imports whichever pdsfile
        its interpreter resolves, which for an editable install is whatever tree
        was installed -- so a green run would say nothing about the tree it was
        started in, and a red one could be reporting a different tree's defects.
        To exercise another tree deliberately, run pytest from that tree.
        """

        env = dict(os.environ)
        env['PDS3_HOLDINGS_DIR'] = str(self.disk / 'holdings')
        env['PDS4_HOLDINGS_DIR'] = str(self.disk / 'pds4-holdings')
        env['TZ'] = 'UTC'
        env['PYTHONPATH'] = str(REPO_ROOT / 'src')
        for name in ('PDS_LOG_ROOT', 'PDSFILE_TEST_HOLDINGS', 'PDSFILE_TEST_DATA_DIR'):
            env.pop(name, None)

        return env


class ToolRun:
    """The result of one tool subprocess.

    Attributes:
        argv: The command line that was run.
        returncode: The tool's exit code.
        stdout: What the tool printed -- its logger output and its reports.
        stderr: Everything else the process wrote: tracebacks, and any warning an
            imported library chose to emit.
        output: stdout followed by stderr, for assertions that do not care which
            stream a message arrived on. The two are separated by a newline, so no
            match can span them: a tool whose last stdout line has no terminator
            would otherwise fuse it with stderr's first line and could satisfy --
            or wrongly break -- a substring assertion that neither stream alone
            does.
    """

    def __init__(self, argv, returncode, stdout, stderr):
        self.argv = argv
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        separator = '\n' if stdout and not stdout.endswith('\n') else ''
        self.output = stdout + separator + stderr

    def __repr__(self):
        return f'ToolRun(argv={self.argv!r}, returncode={self.returncode})'

    @property
    def error_lines(self):
        """Return the tool's log lines at ERROR or FATAL level.

        Parsed from stdout, where the tools' console logger writes; a stderr line
        that happened to contain the level marker is not a tool error.
        """

        return [line for line in self.stdout.splitlines()
                if '| ERROR |' in line or '| FATAL |' in line]

    def describe(self):
        """Return a message suitable for an assertion failure."""

        return (f'{self.argv}\nexit={self.returncode}\n'
                f'--- stdout ---\n{self.stdout}\n--- stderr ---\n{self.stderr}')


def run_tool(tree, tool, *args):
    """Run one maintenance tool as a subprocess against a temporary tree.

    Args:
        tree: The ToolTree to run against.
        tool: A key of TOOL_MODULES.
        *args: Command-line arguments, path-like or str.

    The two streams are captured separately. Anything a test compares against a
    golden must come from stdout: stderr carries whatever warnings the interpreter
    and the installed libraries feel like emitting, which varies by Python version
    and by dependency version and is no part of the tool's output.

    Returns:
        ToolRun: The exit code and both streams.
    """

    argv = [sys.executable, '-m', TOOL_MODULES[tool]] + [str(a) for a in args]
    proc = subprocess.run(argv, cwd=str(tree.disk), env=tree.env,
                          capture_output=True, timeout=TOOL_TIMEOUT, check=False)

    return ToolRun(argv, proc.returncode,
                   proc.stdout.decode('utf-8', errors='replace'),
                   proc.stderr.decode('utf-8', errors='replace'))


def no_holdings_env():
    """Return an environment with this checkout on the path and no holdings roots.

    One builder rather than one per caller: a second copy of the list of variables
    to remove is a second thing to keep current, and a variable missing from one
    copy is invisible -- the subprocess just quietly has a root it was meant not to
    have.

    Returns:
        dict[str, str]: A copy of os.environ, with PYTHONPATH naming this
        checkout's src/ and both holdings roots and the three test-selector
        variables removed.
    """

    env = dict(os.environ)
    env['PYTHONPATH'] = str(REPO_ROOT / 'src')
    for name in ('PDS3_HOLDINGS_DIR', 'PDS4_HOLDINGS_DIR', 'PDS_LOG_ROOT',
                 'PDSFILE_TEST_HOLDINGS', 'PDSFILE_TEST_DATA_DIR'):
        env.pop(name, None)

    return env


def run_tool_in_process(tool, *args):
    """Run one holdings-free tool by calling its main() in this process.

    Only the tools in HOLDINGS_FREE_TOOLS qualify; the assertion below is what
    keeps a tool that builds PdsFile objects from being driven this way.

    sys.argv is set to the command line for the duration of the call, because
    argparse takes the program name in its usage and error messages from
    sys.argv[0]; without it the messages would name pytest. It is restored
    afterwards.

    Third fidelity caveat, after the working directory and sys.argv: output is
    captured into io.StringIO, which has no encoding, where a real process writes
    through an encoded stream. A byte the subprocess's locale could not encode
    would raise there and cannot here. Neither tool driven this way can produce
    one -- they print paths the caller supplied and ASCII status words -- but a
    tool that formatted arbitrary file content would need the subprocess.

    Args:
        tool: A key of TOOL_MODULES that is also in HOLDINGS_FREE_TOOLS.
        *args: Command-line arguments, path-like or str. Give paths as absolute:
            this call inherits pytest's working directory rather than running in
            a tree of its own. A test that needs a relative path should set the
            working directory itself, with monkeypatch.chdir.

    Returns:
        ToolRun: main()'s return value as the exit code, and both streams. A
        SystemExit -- which is what argparse raises for --help and for a usage
        error -- is caught and its code reported, so those paths are readable
        here too. Any other exception propagates, which is what makes a crash
        visible as a test error rather than as an exit code.
    """

    assert tool in HOLDINGS_FREE_TOOLS, (
        f'{tool} is not holdings-free; drive it with run_tool() instead')

    module = importlib.import_module(TOOL_MODULES[tool])
    argv = [module.__file__] + [str(a) for a in args]
    out = io.StringIO()
    err = io.StringIO()
    saved_argv = sys.argv
    sys.argv = list(argv)
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                returncode = module.main(argv)
            except SystemExit as exc:
                returncode = 0 if exc.code is None else exc.code
    finally:
        sys.argv = saved_argv

    return ToolRun(argv, returncode, out.getvalue(), err.getvalue())


def run_tool_without_holdings(tool, *args, cwd=None):
    """Run one holdings-free tool as a subprocess, with neither holdings root set.

    What this pins that run_tool_in_process() cannot: that `python -m <module>`
    reaches main() at all -- an in-process call imports the module and calls the
    function by name, so it would pass just as well with no `__main__` block --
    and that the process exit code is main()'s return value. Dropping both
    holdings variables also pins that these tools need neither.

    Args:
        tool: A key of TOOL_MODULES that is also in HOLDINGS_FREE_TOOLS.
        *args: Command-line arguments, path-like or str.
        cwd: The working directory for the subprocess. Defaults to this process's.

    Returns:
        ToolRun: The exit code and both streams.
    """

    assert tool in HOLDINGS_FREE_TOOLS, (
        f'{tool} is not holdings-free; drive it with run_tool() instead')

    argv = [sys.executable, '-m', TOOL_MODULES[tool]] + [str(a) for a in args]
    proc = subprocess.run(argv, cwd=None if cwd is None else str(cwd),
                          env=no_holdings_env(), capture_output=True,
                          timeout=TOOL_TIMEOUT, check=False)

    return ToolRun(argv, proc.returncode,
                   proc.stdout.decode('utf-8', errors='replace'),
                   proc.stderr.decode('utf-8', errors='replace'))


def console_scripts(directory, *tools):
    """Write executable console scripts for some tools, and return the directory.

    An installed tool is reached through a small executable on PATH whose name is
    the tool's; `python -m <module>` reaches the same main() but leaves a module
    file path in argv[0]. pdschecksums --infoshelf builds the command for its
    chained run by rewriting its own argv[0], so it can only be exercised the first
    way. These scripts are what `pip install` would have put there.

    Args:
        directory: Where to write them. Created if it does not exist.
        *tools: Keys of TOOL_MODULES.

    Returns:
        pathlib.Path: The directory, so a caller can name a script inside it.
    """

    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    for tool in tools:
        script = directory / tool
        script.write_text(f'#!{sys.executable}\n'
                          f'import sys\n'
                          f'from {TOOL_MODULES[tool]} import main\n'
                          f'sys.exit(main())\n')
        script.chmod(0o755)

    return directory


def run_console_script(tree, script, *args):
    """Run one tool through its console script, the way an install invokes it.

    Args:
        tree: The ToolTree to run against.
        script: Path to a script console_scripts() wrote.
        *args: Command-line arguments, path-like or str.

    Returns:
        ToolRun: The exit code and both streams.
    """

    argv = [str(script)] + [str(a) for a in args]
    proc = subprocess.run(argv, cwd=str(tree.disk), env=tree.env,
                          capture_output=True, timeout=TOOL_TIMEOUT, check=False)

    return ToolRun(argv, proc.returncode,
                   proc.stdout.decode('utf-8', errors='replace'),
                   proc.stderr.decode('utf-8', errors='replace'))


def initialize(tree, tool, target):
    """Run a tool's --initialize task and assert it succeeded.

    Args:
        tree: The ToolTree to run against.
        tool: A key of TOOL_MODULES.
        target: The path to initialize.

    Returns:
        ToolRun: The completed run.
    """

    run = run_tool(tree, tool, '--initialize', target)
    assert run.returncode == 0, run.describe()

    return run


def build_tree(tmp_dir, root, flavor, paths, mtimes):
    """Copy a declared source subset into a fresh temporary holdings tree.

    The holdings layout is preserved exactly, and every copied file's modification
    time is pinned from the caller's table so that checksum, shelf and archive
    output is byte-for-byte reproducible.

    Args:
        tmp_dir: The temporary directory to build in.
        root: The holdings root to copy from.
        flavor: 'pds3' or 'pds4'.
        paths: The holdings-relative paths to copy.
        mtimes: Mapping of holdings-relative path to POSIX mtime.

    Returns:
        ToolTree: The populated tree.
    """

    tree = ToolTree(tmp_dir, flavor, source_dir=root, paths=paths, mtimes=mtimes)
    _populate(tree, root)

    return tree


def _populate(tree, root):
    """Create both holdings roots under a tree and copy its declared subset in."""

    for name in HOLDINGS_DIRNAME.values():
        (tree.disk / name).mkdir(parents=True, exist_ok=True)

    for relpath in tree.paths:
        target = tree.holdings / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(Path(root) / relpath, target)
        mtime = tree.mtimes[relpath]
        os.utime(target, (mtime, mtime))


def add_file(tree, relpath, contents, mtime):
    """Create a new file inside a temporary tree, with a pinned modification time.

    Args:
        tree: The ToolTree to write into.
        relpath: The holdings-relative path of the new file.
        contents: Bytes to write.
        mtime: POSIX modification time to pin.

    Returns:
        pathlib.Path: The path written.
    """

    target = tree.path(relpath)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(contents)
    os.utime(target, (mtime, mtime))

    return target


##########################################################################################
# Corruption verbs
#
# The per-module CORRUPTIONS tables name one of these verbs plus a fixed target;
# nothing is randomized and nothing is chosen at run time.
##########################################################################################

def overwrite_first_byte(path, value=0xFF):
    """Overwrite byte 0 of a file, leaving its length and mtime unchanged.

    Args:
        path: The file to damage.
        value: The byte value to write.
    """

    path = Path(path)
    stat = path.stat()
    with open(path, 'r+b') as f:
        f.write(bytes([value]))
    os.utime(path, (stat.st_atime, stat.st_mtime))


def truncate_file(path, nbytes):
    """Truncate a file to a fixed length, leaving its mtime unchanged.

    Args:
        path: The file to damage.
        nbytes: The length to truncate to.
    """

    path = Path(path)
    stat = path.stat()
    with open(path, 'r+b') as f:
        f.truncate(nbytes)
    os.utime(path, (stat.st_atime, stat.st_mtime))


def shift_mtime(path, seconds):
    """Move a file's modification time by a fixed number of seconds.

    Args:
        path: The file to touch.
        seconds: The offset to apply.
    """

    path = Path(path)
    mtime = path.stat().st_mtime + seconds
    os.utime(path, (mtime, mtime))


def replace_bytes(path, old, new):
    """Replace one fixed byte string in a file, leaving its length and mtime alone.

    Args:
        path: The file to damage.
        old: The byte string to replace; must occur exactly once.
        new: The replacement, which must be the same length as `old`.

    Raises:
        AssertionError: If the lengths differ or `old` does not occur exactly once,
            so a stale corruption table cannot pass silently.
    """

    assert len(old) == len(new), 'replacement must preserve the file length'
    path = Path(path)
    stat = path.stat()
    data = path.read_bytes()
    assert data.count(old) == 1, (
        f'expected exactly one occurrence of {old!r} in {path}, found {data.count(old)}')
    path.write_bytes(data.replace(old, new))
    os.utime(path, (stat.st_atime, stat.st_mtime))


def delete_md5_entry(md5_path, entry_suffix):
    """Delete the line for one file from an md5 checksum file.

    Args:
        md5_path: The `*_md5.txt` file to edit.
        entry_suffix: The trailing part of the path whose line is removed.

    Raises:
        AssertionError: If no line matched, so a stale table cannot pass silently.
    """

    md5_path = Path(md5_path)
    lines = md5_path.read_text(encoding='latin-1').splitlines(keepends=True)
    kept = [line for line in lines if not line.rstrip().endswith(entry_suffix)]
    assert len(kept) == len(lines) - 1, (
        f'expected exactly one md5 entry ending in {entry_suffix!r}, '
        f'removed {len(lines) - len(kept)}')
    md5_path.write_text(''.join(kept), encoding='latin-1')


##########################################################################################
# Normalizers: turn a generated artifact into stable, comparable text
##########################################################################################

def md5_file_text(path):
    """Return an md5 checksum file as sorted "<path> <md5>" text.

    The tools emit md5 files in os.walk order, which is not portable, so the
    mapping rather than the file is what gets compared.

    Args:
        path: The `*_md5.txt` file to read.

    Returns:
        str: One "<path> <md5>" line per entry, sorted by path.
    """

    entries = md5_file_mapping(path)

    return ''.join(f'{relpath} {entries[relpath]}\n' for relpath in sorted(entries))


def md5_file_mapping(path):
    """Return an md5 checksum file as a {path: md5} mapping.

    Args:
        path: The `*_md5.txt` file to read.

    Returns:
        dict[str, str]: Checksum by relative path.
    """

    entries = {}
    for line in Path(path).read_text(encoding='latin-1').splitlines():
        if not line.strip():
            continue
        checksum, _, relpath = line.partition(' ')
        entries[relpath.strip()] = checksum.strip()

    return entries


def sidecar_text(path):
    """Return a shelf `.py` sidecar as normalized text.

    The tools write sidecar entries in a deterministic, machine-independent order:
    sorted keys for info shelves, table-row order for index shelves, and for link
    shelves the list-valued entries before the str-valued ones with each group
    sorted. This strips trailing whitespace and normalizes line endings so the
    comparison does not depend on either.

    Args:
        path: The `*.py` sidecar to read.

    Returns:
        str: The normalized sidecar text.
    """

    lines = Path(path).read_text(encoding='latin-1').splitlines()

    return ''.join(line.rstrip() + '\n' for line in lines)


def tar_member_text(path):
    """Return a .tar.gz archive as sorted member tuples rendered as text.

    Archive bytes are not reproducible (gzip metadata, os.walk order), so archives
    are only ever compared by their members.

    Member modification times are reported for files only: file mtimes come from
    the pinned source table and are reproducible, while directory mtimes are set
    by the copy itself and are not.

    Args:
        path: The `.tar.gz` file to read.

    Returns:
        str: One "<name> <kind> <size> <mtime>" line per member, sorted by name.
    """

    with tarfile.open(path, 'r:gz') as tar:
        members = [(member.name, 'dir' if member.isdir() else 'file',
                    0 if member.isdir() else member.size,
                    0 if member.isdir() else int(member.mtime))
                   for member in tar.getmembers()]
    members.sort()

    return ''.join(f'{name} {kind} {size} {mtime}\n'
                   for name, kind, size, mtime in members)


def tar_member_names(path):
    """Return the sorted member names of a .tar.gz archive.

    Args:
        path: The `.tar.gz` file to read.

    Returns:
        list[str]: Member names, sorted.
    """

    with tarfile.open(path, 'r:gz') as tar:
        return sorted(tar.getnames())


##########################################################################################
# Golden comparison
##########################################################################################

def check_golden(name, text, update, *, unordered=False):
    """Compare normalized text against a committed golden artifact.

    Args:
        name: The golden's basename, without extension.
        text: The normalized text produced by the test.
        update: True to rewrite the golden instead of comparing (pytest --update).
        unordered: True to compare the lines as a sorted multiset instead of in
            order. Opt in **only** where the producing tool leaves the order
            genuinely unspecified -- it weakens the comparison, and for most of
            these artifacts (shelf sidecars, archive member tuples, the sorted md5
            mapping) the order is deterministic and worth pinning. The golden file
            itself is still written and kept in the tool's own order, so it stays
            readable; only the comparison ignores order.

    Raises:
        AssertionError: If the golden is absent (and update was not requested) or
            differs from the text.
    """

    path = GOLDEN_DIR / f'{name}.txt'
    if update:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return

    assert path.exists(), (
        f'missing golden {path}; regenerate the tool-test goldens with '
        f'`pytest tests/holdings_maintenance --update` against real holdings')

    # Compare line lists, never a joined string: joining sorted lines is not
    # injective on multisets when a side lacks a trailing newline, so 'b\na' and
    # 'ab\n' would compare equal.
    actual_lines = text.splitlines()
    expected_lines = path.read_text(encoding='utf-8').splitlines()
    if unordered:
        actual_lines, expected_lines = sorted(actual_lines), sorted(expected_lines)

    if actual_lines != expected_lines:
        ordering = 'sorted lines' if unordered else 'in order'
        diff = difflib.unified_diff(expected_lines, actual_lines,
                                    fromfile=f'{path.name} (golden)',
                                    tofile=f'{path.name} (produced)', lineterm='')
        # pytest shows no diff of its own once an assertion carries a message, so
        # the message has to carry one; a bare "golden mismatch" in a CI log leaves
        # the reader nothing to go on.
        raise AssertionError(f'golden mismatch ({ordering}): {path}\n'
                             + '\n'.join(diff))


def golden_lines(name):
    """Return a committed golden's lines, for assertions derived from it.

    Only for checks that compare something *derived* from the golden, such as an
    ordered subsequence of it. Whole-artifact comparisons go through check_golden,
    which also handles --update and produces a diff on failure.

    Args:
        name: The golden's basename, without extension.

    Returns:
        list[str]: The golden's lines, without terminators.
    """

    return (GOLDEN_DIR / f'{name}.txt').read_text(encoding='utf-8').splitlines()
