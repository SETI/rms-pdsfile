"""Re-derive the file-and-line citations a docstring change has moved.

A docstring-only PR changes no statement and still invalidates every citation below the
docstrings it grows, in `critiques/pr-29/check_citations.py`'s table and in the records
that table checks. PR-29a repaired seven of them by hand; this PR moved 92 in two passes,
which is more than hand-checking can be trusted with.

The repair has to be a re-derivation and not a renumbering. Two files at two commits are
aligned line by line with `difflib`, which is exact here because the code did not move;
each citation is then carried to the line its own line became, and **the citation's token
must still be present there** or nothing is written at all. That is what makes this safe
to run unattended: a citation whose anchor really did change fails the run rather than
being silently pointed at the wrong line.

The checker's table and the documents are rewritten in the same pass, so the two cannot
end up disagreeing.

Usage, from the repository root:

    python critiques/pr-29b/remap_citations.py COMMIT

`COMMIT` is a commit at which the citations were correct. Exit status is 1 if any citation
could not be resolved, in which case nothing is written.
"""

import difflib
import importlib.util
import pathlib
import re
import subprocess
import sys

CHECKER = pathlib.Path('critiques/pr-29/check_citations.py')

# The documents whose citations the checker covers. Kept in step with its own RECORD and
# DEFERRED, and read from it rather than restated would be better; they are listed here
# because the checker names them as module constants that a rewrite has to reach anyway.
DOCS = ('critiques/pr-29-validation.md', 'critiques/deferred-observations.md')

# The files a docstring PR moves. A citation into any other file is left alone.
FILES = ('src/pdsfile/pdsfile.py', 'src/pdsfile/pdsviewable.py',
         'src/pdsfile/_properties.py')

ENTRY_RE = re.compile(r"^(\s*\('(?P<path>[^']+)', )(?P<num>\d+)(, .*)$")
CITED_RE = re.compile(r'`([A-Za-z0-9_./-]+\.py):(\d+)(?:-(\d+))?`')
BARE_RE = re.compile(r'`:(\d+)`')


def citations():
    """Return the checker's citation table.

    Returns:
        list: triples of file path, line number and the token that must appear there.
    """

    spec = importlib.util.spec_from_file_location('check_citations', CHECKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    return module.CITATIONS


def line_map(commit, path):
    """Return the mapping from a file's line numbers at one commit to its numbers now.

    Only lines the alignment calls equal are mapped, so a line whose text changed has no
    entry and its citation is reported rather than guessed at.

    Parameters:
        commit (str): the commit to align against.
        path (str): the file to align.

    Returns:
        dict: line number at the commit, mapped to line number in the working tree.
    """

    old = subprocess.run(['git', 'show', f'{commit}:{path}'], capture_output=True,
                         text=True, check=True).stdout.split('\n')
    new = pathlib.Path(path).read_text().split('\n')

    mapping = {}
    matcher = difflib.SequenceMatcher(None, old, new, autojunk=False)
    for tag, i1, i2, j1, _j2 in matcher.get_opcodes():
        if tag == 'equal':
            for offset in range(i2 - i1):
                mapping[i1 + offset + 1] = j1 + offset + 1

    return mapping


def resolve(commit):
    """Work out where every citation into the moved files has gone.

    Parameters:
        commit (str): the commit at which the citations were correct.

    Returns:
        tuple: the moves, as file path mapped to old line mapped to new line; and the
        list of citations that could not be resolved, as quadruples of path, line, token
        and reason.
    """

    maps = {path: line_map(commit, path) for path in FILES}
    moves = {}
    unresolved = []

    for path, number, token in citations():
        if path not in maps:
            continue

        new = maps[path].get(number)
        if new is None:
            unresolved.append((path, number, token, 'no line matched'))
            continue

        if token not in pathlib.Path(path).read_text().split('\n')[new - 1]:
            unresolved.append((path, number, token, f'token absent at line {new}'))
            continue

        if new != number:
            moves.setdefault(path, {})[number] = new

    return moves, unresolved


def rewrite_checker(moves):
    """Rewrite the line number of every moved entry in the checker's table.

    The table is rewritten line by line rather than by text substitution, because two
    citations may share a line number with different tokens.

    Parameters:
        moves (dict): file path mapped to old line mapped to new line.

    Returns:
        int: how many entries were rewritten.
    """

    lines = CHECKER.read_text().split('\n')
    count = 0

    for index, line in enumerate(lines):
        match = ENTRY_RE.match(line)
        if not match or match.group('path') not in moves:
            continue
        new = moves[match.group('path')].get(int(match.group('num')))
        if new is not None:
            lines[index] = f'{match.group(1)}{new}{match.group(4)}'
            count += 1

    CHECKER.write_text('\n'.join(lines))

    return count


def rewrite_document(path, by_basename):
    """Rewrite every citation in one document that names a moved line.

    Both citation spellings the checker recognizes are handled: a full ``file.py:NNN``,
    which may carry a range, and a bare ``:NNN`` continuing an earlier file name. A bare
    citation is rewritten only where exactly one file's mapping moves that line, so an
    ambiguous one is left as it is and the checker reports it.

    Parameters:
        path (str): the document to rewrite.
        by_basename (dict): file basename mapped to old line mapped to new line.

    Returns:
        int: how many citations were rewritten.
    """

    document = pathlib.Path(path)
    text = document.read_text()
    count = 0

    def named(match):
        """Rewrite one ``file.py:NNN`` citation.

        Parameters:
            match (re.Match): the citation.

        Returns:
            str: the citation, with any moved line number replaced.
        """

        nonlocal count
        mapping = by_basename.get(match.group(1).rpartition('/')[2])
        if not mapping:
            return match.group(0)

        first = mapping.get(int(match.group(2)), int(match.group(2)))
        count += first != int(match.group(2))
        out = f'`{match.group(1)}:{first}'

        if match.group(3) is not None:
            last = mapping.get(int(match.group(3)), int(match.group(3)))
            count += last != int(match.group(3))
            out += f'-{last}'

        return out + '`'

    def bare(match):
        """Rewrite one bare ``:NNN`` citation, where it is unambiguous.

        Parameters:
            match (re.Match): the citation.

        Returns:
            str: the citation, with the line number replaced where one file claims it.
        """

        nonlocal count
        number = int(match.group(1))
        candidates = {m[number] for m in by_basename.values() if number in m}
        if len(candidates) != 1:
            return match.group(0)

        count += 1

        return f'`:{candidates.pop()}`'

    text = CITED_RE.sub(named, text)
    text = BARE_RE.sub(bare, text)
    document.write_text(text)

    return count


def main(argv):
    """Re-derive every moved citation and rewrite the checker and the documents.

    Parameters:
        argv (list): the commit at which the citations were correct.

    Returns:
        int: 1 if any citation could not be resolved, 0 otherwise.
    """

    moves, unresolved = resolve(argv[0])

    if unresolved:
        for path, number, token, reason in unresolved:
            print(f'UNRESOLVED {path}:{number} ({token!r}): {reason}')
        print(f'{len(unresolved)} citations unresolved; nothing written')
        return 1

    print(f'checker table: {rewrite_checker(moves)} entries moved')

    by_basename = {path.rpartition('/')[2]: mapping for path, mapping in moves.items()}
    for path in DOCS:
        print(f'{path}: {rewrite_document(path, by_basename)} citations rewritten')

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
