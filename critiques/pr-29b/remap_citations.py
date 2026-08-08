"""Remap every citation from the tree at OLD to the working tree, and rewrite both the
checker's table and the documents that cite it."""
import difflib, importlib.util, pathlib, re, subprocess, sys

OLD = sys.argv[1]
CHECKER = pathlib.Path('critiques/pr-29/check_citations.py')
DOCS = ('critiques/pr-29-validation.md', 'critiques/deferred-observations.md')
FILES = ('src/pdsfile/pdsfile.py', 'src/pdsfile/pdsviewable.py',
         'src/pdsfile/_properties.py')

spec = importlib.util.spec_from_file_location('cc', CHECKER)
cc = importlib.util.module_from_spec(spec); spec.loader.exec_module(cc)

maps = {}
for path in FILES:
    a = subprocess.run(['git', 'show', f'{OLD}:{path}'], capture_output=True, text=True,
                       check=True).stdout.split('\n')
    b = pathlib.Path(path).read_text().split('\n')
    m = {}
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b,
                                                       autojunk=False).get_opcodes():
        if tag == 'equal':
            for k in range(i2 - i1):
                m[i1 + k + 1] = j1 + k + 1
    maps[path] = m

moves, bad = {}, []
for path, number, token in cc.CITATIONS:
    if path not in maps:
        continue
    new = maps[path].get(number)
    if new is None:
        bad.append((path, number, token, 'line not matched'))
        continue
    if token not in pathlib.Path(path).read_text().split('\n')[new - 1]:
        bad.append((path, number, token, f'token missing at {new}'))
        continue
    if new != number:
        moves.setdefault(path, {})[number] = new

if bad:
    for b in bad:
        print('UNRESOLVED:', b)
    raise SystemExit(1)

by_base = {p.rpartition('/')[2]: m for p, m in moves.items()}

lines = CHECKER.read_text().split('\n')
ENTRY = re.compile(r"^(\s*\('(?P<path>[^']+)', )(?P<num>\d+)(, .*)$")
n = 0
for k, line in enumerate(lines):
    mo = ENTRY.match(line)
    if mo and mo.group('path') in moves:
        new = moves[mo.group('path')].get(int(mo.group('num')))
        if new is not None:
            lines[k] = f"{mo.group(1)}{new}{mo.group(4)}"
            n += 1
CHECKER.write_text('\n'.join(lines))
print('checker table:', n, 'entries moved')

CITED = re.compile(r'`([A-Za-z0-9_./-]+\.py):(\d+)(?:-(\d+))?`')
BARE = re.compile(r'`:(\d+)`')
for doc in DOCS:
    q = pathlib.Path(doc)
    text, changed = q.read_text(), [0]
    def fix_named(mo):
        m = by_base.get(mo.group(1).rpartition('/')[2])
        if not m:
            return mo.group(0)
        a = m.get(int(mo.group(2)), int(mo.group(2)))
        changed[0] += a != int(mo.group(2))
        s = f'`{mo.group(1)}:{a}'
        if mo.group(3) is not None:
            b = m.get(int(mo.group(3)), int(mo.group(3)))
            changed[0] += b != int(mo.group(3))
            s += f'-{b}'
        return s + '`'
    text = CITED.sub(fix_named, text)
    def fix_bare(mo):
        cands = {m[int(mo.group(1))] for m in by_base.values() if int(mo.group(1)) in m}
        if len(cands) == 1:
            changed[0] += 1
            return f'`:{cands.pop()}`'
        return mo.group(0)
    text = BARE.sub(fix_bare, text)
    q.write_text(text)
    print(doc, ':', changed[0], 'citations rewritten')
