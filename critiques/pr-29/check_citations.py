"""Check every reproducible number in PR-29's records against the tree.

PR-29's deliverable is prose, so its only defect mode is being wrong about the code. The
review rounds hunt for prose that misdescribes behavior; this gate covers the mechanical
half: every file-and-line citation in `critiques/pr-29-validation.md` and in PR-29's
block of `critiques/deferred-observations.md`, and every number in the record that can be
re-derived from the tree.

Each citation is checked by reading the cited line and requiring a token that identifies
what the prose says is there. A citation that has drifted by one line, or that names the
wrong file, fails.

What it cannot check: numbers that come from running something rather than from reading
the tree -- the suite id counts, the Sphinx warning counts, the base-tree measurements.
Those carry their command lines in the record instead.

Run from the repository root with the tree's own interpreter, which must be 3.11 or
newer, since it reads pyproject.toml through tomllib:

    python critiques/pr-29/check_citations.py

It prints one line per number that does not reproduce, and exits 1 if any does not.
"""

import ast
import pathlib
import re
import subprocess
import sys

import tomllib

SRC = pathlib.Path('src/pdsfile')
RECORD = pathlib.Path('critiques/pr-29-validation.md')
DEFERRED = pathlib.Path('critiques/deferred-observations.md')

IN_SCOPE = ('pdsfile.py', 'pdscache.py', 'pdsviewable.py', '__init__.py',
            'preload_and_cache.py')

# Every file-and-line citation the two documents make, with a token that must appear on
# the cited line. A range is checked at both ends.
CITATIONS = [
    ('src/pdsfile/pdscache.py', 60, 'MEMCACHED_LOADED = True'),
    ('src/pdsfile/pdscache.py', 139, 'self.keys = set()'),
    ('src/pdsfile/pdscache.py', 154, 'self.preload_eligible = True'),
    ('src/pdsfile/pdscache.py', 170, 'if len(self.keys) > self.limit + self.slop:'),
    ('src/pdsfile/pdscache.py', 171, 'expirations = [(self.dict[k][1], k)'),
    ('src/pdsfile/pdscache.py', 172, 'is not None]'),
    ('src/pdsfile/pdscache.py', 177, 'self.keys.remove(key)'),
    ('src/pdsfile/pdscache.py', 361, 'def get_multi'),
    ('src/pdsfile/pdscache.py', 381, 'value = self[key]'),
    ('src/pdsfile/pdscache.py', 446, 'if expiration:'),
    ('src/pdsfile/pdscache.py', 447, 'self.keys.add(key)'),
    ('src/pdsfile/pdscache.py', 530, 'del self.dict[key]'),
    ('src/pdsfile/pdscache.py', 550, 'del self.dict[key]'),
    ('src/pdsfile/pdscache.py', 570, 'del self.dict[key]'),
    ('src/pdsfile/pdscache.py', 591, 'self.keys = set()'),
    ('src/pdsfile/pdscache.py', 803, 'if blocking_pid in (0, self.pid):'),
    ('src/pdsfile/pdscache.py', 807, 'unblock_time = time.time() + MAX_BLOCK_SECONDS'),
    ('src/pdsfile/pdscache.py', 822, 'if test_pid != blocking_pid:'),
    ('src/pdsfile/pdscache.py', 828, 'broke a block'),
    ('src/pdsfile/pdscache.py', 889, 'was outraced by'),
    ('src/pdsfile/pdscache.py', 907, 'if not test_pid and self.logger:'),
    ('src/pdsfile/pdscache.py', 913, 'if test_pid != self.pid and self.logger:'),
    ('src/pdsfile/pdscache.py', 1111, 'keys = mydict.keys()'),
    ('src/pdsfile/pdscache.py', 1113, 'keys.sort()'),
    ('src/pdsfile/pdscache.py', 1121, 'len(self.local_keys_by_lifetime) - len(failures)'),
    ('src/pdsfile/pdscache.py', 1176, 'if key in self.permanent_values:'),
    ('src/pdsfile/pdscache.py', 1177, 'self._restore_permanent_to_cache()'),
    ('src/pdsfile/pdscache.py', 1213, 'def get_multi'),
    ('src/pdsfile/pdscache.py', 1265, 'for key in nonlocal_keys:'),
    ('src/pdsfile/pdscache.py', 1267, 'self._restore_permanent_to_cache()'),
    ('src/pdsfile/pdscache.py', 1268, 'break'),
    ('src/pdsfile/pdscache.py', 1461, 'if self.lifetime:'),
    ('src/pdsfile/pdscache.py', 1506, 'if key in self.permanent_values:'),
    ('src/pdsfile/pdscache.py', 1507, 'del self.permanent_values[key]'),
    ('src/pdsfile/pdscache.py', 1512, 'return status1 or status2'),
    ('src/pdsfile/pdscache.py', 1554, '_ = self.mc.del_multi(keys)'),
    ('src/pdsfile/pdscache.py', 1561, '_del_local'),
    ('src/pdsfile/pdscache.py', 1572, 'def _delete_local'),
    ('src/pdsfile/pdscache.py', 1569, 'count = len(self) - prev_len'),
    ('src/pdsfile/pdscache.py', 1630, "self.wait_for_unblock('clear')"),
    ('src/pdsfile/pdscache.py', 1632, "max(self.mc.get('$CLEAR_COUNT'), self.clear_count)"),
    ('src/pdsfile/pdscache.py', 1633, 'self.mc.flush_all()'),
    ('src/pdsfile/pdscache.py', 1678, 'lost from memcache'),
    ('src/pdsfile/pdscache.py', 1679, "self.mc.set('$CLEAR_COUNT', clear_count, time=0)"),
    ('src/pdsfile/pdscache.py', 1775, 'Permanent object is TooBig'),
    ('src/pdsfile/pdsviewable.py', 92, 'self.width_over_height = float'),
    ('src/pdsfile/pdsviewable.py', 93, 'self.height_over_width = float'),
    ('src/pdsfile/pdsviewable.py', 340, 'for sub_viewable in viewable.viewables:'),
    ('src/pdsfile/pdsviewable.py', 342, 'return'),
    ('src/pdsfile/pdsviewable.py', 344, 'self.viewables.add(viewable)'),
    ('src/pdsfile/pdsviewable.py', 347, 'if viewable.name:'),
    ('src/pdsfile/pdsviewable.py', 465, 'viewable.for_frame(200,200)'),
    ('src/pdsfile/pdsviewable.py', 482, 'viewable.for_frame(400,400)'),
    ('src/pdsfile/pdsviewable.py', 675, 'full_viewable = viewable'),
    ('src/pdsfile/pdsviewable.py', 677, 'viewables.append(viewable)'),
    ('src/pdsfile/pdsviewable.py', 835, "rpartition('/png-')"),
    ('src/pdsfile/pdsviewable.py', 837, "rpartition('/jpg-')"),
    ('src/pdsfile/pdsviewable.py', 853, "not in ('.png', 'jpg')"),
    ('src/pdsfile/pdsviewable.py', 861, 'except Image.UnidentifiedImageError:'),
    ('src/pdsfile/pdsviewable.py', 864, 'continue'),
    ('src/pdsfile/pdsviewable.py', 866, '(width, height) = im.size'),
    ('src/pdsfile/pdsviewable.py', 888, "key_base.replace('document_', '')"),
    ('src/pdsfile/pdsviewable.py', 889, "icon_name.replace('folder_', '')"),
    ('src/pdsfile/pdsviewable.py', 911, 'if (icon_name, True) not in ICON_SET_BY_TYPE:'),
    ('src/pdsfile/pdsviewable.py', 982, 'return ICON_SET_BY_TYPE[icon_type, is_open]'),
    ('src/pdsfile/pdsfile.py', 304, 'DICTIONARY_CACHE_LIMIT = 200000'),
    ('src/pdsfile/pdsfile.py', 1088, "return ''"),
    ('src/pdsfile/pdsfile.py', 1097, "return ''"),
    ('src/pdsfile/pdsfile.py', 1141, 'return None'),
    ('src/pdsfile/pdsfile.py', 1579, 'return cls.from_logical_path(logical_path,'),
    ('src/pdsfile/pdsfile.py', 1583, 'return cls.from_abspath(abspath,'),
    ('src/pdsfile/pdsfile.py', 1851, 'if len(parts) == 0:'),
    ('src/pdsfile/pdsfile.py', 1872, 'def _from_absolute_or_logical_path'),
    ('src/pdsfile/pdsfile.py', 1897, 'fix_case=False, must_exist=False,'),
    ('src/pdsfile/pdsfile.py', 1901, 'fix_case=False, must_exist=False,'),
    ('src/pdsfile/_preload.py', 60, 'DICTIONARY_CACHE_LIMIT = 200000'),
    ('src/pdsfile/_preload.py', 62, 'def cache_lifetime_for_class(arg, cls=None):'),
    ('src/pdsfile/_preload.py', 91, "get_now('$PRELOADING')"),
    ('src/pdsfile/pds3file/__init__.py', 59, 'DICTIONARY_CACHE_LIMIT = 200000'),
    ('src/pdsfile/pds4file/__init__.py', 48, 'DICTIONARY_CACHE_LIMIT = 200000'),
    ('scripts/automated_tests/pdsfile_main_test.sh', 75, '--mode s'),
    ('.gitignore', 132, '/venv'),
    ('.gitignore', 170, '_version.py'),
]

# Documents whose citations must all appear in CITATIONS. A citation that is not listed
# is reported, so a number added to a record later cannot go unchecked.
CITED_PATTERN = re.compile(
    r'`([A-Za-z0-9_./-]+\.(?:py|json|sh|md|toml)|\.gitignore):(\d+)(?:-(\d+))?`')
BARE_PATTERN = re.compile(r'`:(\d+)`')

# Prefixes that a bare `:NNN` citation may abbreviate, in the block where it appears.
BARE_PREFIXES = ('src/pdsfile/pdscache.py', 'src/pdsfile/pdsviewable.py',
                 'src/pdsfile/pdsfile.py')

# Citations the documents make against the base tree, which this tree cannot answer.
# Each is marked "at base" where it appears, and each is checked by hand once.
AT_BASE = {('preload_and_cache.py', 4)}
AT_BASE_FILES = {name for name, _ in AT_BASE}


def lines_of(path):
    """Return one file's lines, without their endings.

    Parameters:
        path (str): the file to read.

    Returns:
        list: the lines.
    """

    return pathlib.Path(path).read_text().split('\n')


def check_citations(problems):
    """Verify that every listed citation points at a line carrying its token.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    for path, number, token in CITATIONS:
        text = lines_of(path)
        if number > len(text):
            problems.append(f'{path}:{number} is past the end of the file')
            continue
        if token not in text[number - 1]:
            problems.append(f'{path}:{number} does not carry {token!r}; it reads '
                            f'{text[number - 1].strip()!r}')


def check_every_citation_is_listed(problems):
    """Verify that the documents cite nothing that CITATIONS does not cover.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    listed = {(path, number) for path, number, _ in CITATIONS}
    listed_files = {path.rpartition('/')[2] for path, _, _ in CITATIONS}

    text = DEFERRED.read_text()
    block = text[text.index('## From PR-29 ('):]

    for label, document in (('deferred', block), ('record', RECORD.read_text())):
        for match in CITED_PATTERN.finditer(document):
            name = match.group(1)
            if name.rpartition('/')[2] in AT_BASE_FILES:
                continue
            if name.rpartition('/')[2] not in listed_files:
                problems.append(f'[{label}] cites {name}, which no entry covers')
                continue
            for number in (match.group(2), match.group(3)):
                if number is None or (name, int(number)) in AT_BASE:
                    continue
                if not any(path.endswith(name) and line == int(number)
                           for path, line in listed):
                    problems.append(f'[{label}] cites {name}:{number}, '
                                    'which no entry covers')

        for match in BARE_PATTERN.finditer(document):
            number = int(match.group(1))
            if not any((prefix, number) in listed for prefix in BARE_PREFIXES):
                problems.append(f'[{label}] cites a bare :{number}, '
                                'which no entry covers')


def docstring_counts(path):
    """Count the definitions and the documented definitions in one file.

    Parameters:
        path (pathlib.Path): the file to walk.

    Returns:
        tuple: the class count, the function count, and the parameter count excluding
        `self` and `cls`.
    """

    tree = ast.parse(path.read_text())
    classes = functions = parameters = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            args = node.args
            names = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
            if args.vararg:
                names.append(args.vararg.arg)
            if args.kwarg:
                names.append(args.kwarg.arg)
            parameters += sum(1 for n in names if n not in ('self', 'cls'))

    return classes, functions, parameters


def check_scope_table(problems):
    """Verify the record's scope table and its totals.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    # The record's scope table gives base line counts, which this tree cannot answer;
    # these are the head counts the same table carries.
    expected_lines = {'pdsfile.py': 2360, 'pdscache.py': 1780, 'pdsviewable.py': 984,
                      '__init__.py': 39, 'preload_and_cache.py': 46}
    classes = functions = parameters = 0
    for name in IN_SCOPE:
        path = SRC / name
        count = len(path.read_text().split('\n')) - 1
        if count != expected_lines[name]:
            problems.append(f'{name} has {count} lines at head, record says '
                            f'{expected_lines[name]}')
        c, f, p = docstring_counts(path)
        classes += c
        functions += f
        parameters += p

    for label, got, want in (('classes', classes, 6), ('functions', functions, 123),
                             ('parameters', parameters, 150)):
        if got != want:
            problems.append(f'in-scope {label}: {got}, record says {want}')

    total = 5 + classes + functions
    if total != 134:
        problems.append(f'in-scope docstrings: {total}, record says 134')

    # PR-29a's half.
    other = [p for p in sorted(SRC.glob('*.py')) if p.name not in IN_SCOPE]
    functions = parameters = 0
    for path in other:
        _, f, p = docstring_counts(path)
        functions += f
        parameters += p
    for label, got, want in (('PR-29a functions', functions, 156),
                             ('PR-29a parameters', parameters, 131)):
        if got != want:
            problems.append(f'{label}: {got}, record says {want}')


def check_head_docstrings(problems):
    """Verify that every in-scope definition is documented at head.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    for name in IN_SCOPE:
        tree = ast.parse((SRC / name).read_text())
        if ast.get_docstring(tree) is None:
            problems.append(f'{name} has no module docstring')
        kinds = (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        for node in ast.walk(tree):
            if isinstance(node, kinds) and ast.get_docstring(node) is None:
                problems.append(f'{name}: {node.name} has no docstring')


def check_ratchet(problems):
    """Verify the ruff ratchet numbers the record carries.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    with open('pyproject.toml', 'rb') as handle:
        config = tomllib.load(handle)
    ignores = config['tool']['ruff']['lint']['per-file-ignores']
    for label, got, want in (('per-file-ignores entries', len(ignores), 66),
                             ('code slots', sum(len(v) for v in ignores.values()), 180),
                             ('project.scripts', len(config['project']['scripts']), 11)):
        if got != want:
            problems.append(f'{label}: {got}, record says {want}')

    result = subprocess.run(
        ['ruff', 'check', '.', '--config', 'lint.per-file-ignores = {}'],
        capture_output=True, text=True, check=False)
    match = re.search(r'Found (\d+) errors', result.stdout)
    if not match:
        problems.append('could not read a finding count out of ruff')
    elif int(match.group(1)) != 2249:
        problems.append(f'ratchet findings: {match.group(1)}, record says 2249')


def check_frozen(problems):
    """Verify that the four frozen files are byte-identical to the base commit.

    Parameters:
        problems (list): the list that failures are appended to.
    """

    for name in ('tests/api/api_manifest.json', 'tests/api/manifest_allowlist.json',
                 'scripts/dump_public_api.py', 'tests/api/test_api_freeze.py'):
        result = subprocess.run(['git', 'diff', '--quiet', '4edc7d1', '--', name],
                                capture_output=True, check=False)
        if result.returncode != 0:
            problems.append(f'{name} differs from 4edc7d1')

    manifest = pathlib.Path('tests/api/api_manifest.json').read_text()
    if '__doc__' in manifest:
        problems.append('api_manifest.json mentions __doc__, which the record says it '
                        'does not')


def main():
    """Run every check and report what did not reproduce.

    Returns:
        int: 1 if anything failed, 0 otherwise.
    """

    problems = []
    check_citations(problems)
    check_every_citation_is_listed(problems)
    check_scope_table(problems)
    check_head_docstrings(problems)
    check_ratchet(problems)
    check_frozen(problems)

    for problem in problems:
        print('STALE:', problem)

    print()
    print(f'{len(problems)} stale')

    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
