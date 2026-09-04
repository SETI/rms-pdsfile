##########################################################################################
# tests/docs/test_markup.py
#
# Two reStructuredText mistakes that delete published prose without any diagnostic.
# Sphinx reports neither, under -W or under -n: the text simply does not appear on the
# rendered page, and the build is green.
#
#   N1  A directive written with one colon. `.. note:` is parsed as a comment, so the
#       directive and every indented line under it vanish from the page.
#
#   N2  Inline markup nested inside a strong span. reStructuredText does not nest
#       inline markup, so `**a ``b`` c**` renders the asterisks and backticks as
#       literal characters instead of emphasising anything.
#
# Both are checked against the sources -- the .rst files under docs/ and the docstrings
# under src/ -- rather than against a built tree. A check that reads docs/_build needs a
# build to have happened, and a Sphinx event that fires per document only fires for the
# documents a build actually re-read, so an incremental build skips unchanged files and
# the check goes quiet. Reading the files cannot fail that way.
##########################################################################################

import ast
import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_DOCS = _ROOT / 'docs'
_SRC = _ROOT / 'src'

# Directive names spelled with one colon are the whole of N1. The list is explicit
# rather than a pattern because `.. _target:` (a hyperlink target), `.. [1]` (a
# citation) and `.. text` (a comment) are all correct with one colon or none, and a
# pattern over any word would report them.
_DIRECTIVES = frozenset([
    'attention', 'autoclass', 'autofunction', 'automodule', 'caution', 'code',
    'code-block', 'danger', 'deprecated', 'error', 'figure', 'hint', 'image',
    'important', 'include', 'index', 'literalinclude', 'math', 'note', 'rubric',
    'seealso', 'tip', 'toctree', 'versionadded', 'versionchanged', 'warning',
])

_ONE_COLON = re.compile(r'^\s*\.\.\s+([a-z][a-z0-9-]*):(?!:)')

# Directives whose body is published verbatim. A `::` at the end of a line opens a
# literal block, but these carry an argument after the colons -- `.. code-block:: text`
# -- so the line does not end in `::` and the body would otherwise be scanned as prose.
_LITERAL_DIRECTIVES = re.compile(
    r'^(\s*)\.\.\s+(?:code-block|code|literalinclude|parsed-literal|math)::')

# A strong span, by the reStructuredText inline-markup rules: the opening ** is not
# followed by whitespace, the closing ** is not preceded by whitespace, and the span
# holds no ** of its own. Nested markup is a backtick or a lone asterisk inside it.
_STRONG = re.compile(r'\*\*(?![\s*])((?:(?!\*\*).)+?)(?<![\s*])\*\*')
_NESTED = re.compile(r'`|(?<![\w*])\*(?![\s*])')


def _uncode(lines):
    """Blank out literal blocks, so their contents are not read as markup.

    A literal block is the indented run that follows a line ending in `::` or a literal
    directive such as `.. code-block:: text`, and its text is published verbatim --
    asterisks and all -- so neither rule applies to it.

    Parameters:
        lines (list): the source lines.

    Returns:
        list: the same lines with every literal-block line replaced by an empty one.
    """
    out = list(lines)
    k = 0
    while k < len(out):
        directive = _LITERAL_DIRECTIVES.match(out[k])
        if directive or out[k].rstrip().endswith('::'):
            indent = len(directive.group(1)) if directive else (
                len(out[k]) - len(out[k].lstrip()))
            j = k + 1
            while j < len(out):
                stripped = out[j].strip()
                if stripped and (len(out[j]) - len(out[j].lstrip())) <= indent:
                    break
                out[j] = ''
                j += 1
            k = j
        else:
            k += 1
    return out


def _paragraphs(lines, first_line):
    """Group lines into paragraphs, keeping each paragraph's first line number.

    Inline markup may span lines within a paragraph, so N2 is checked per paragraph
    rather than per line.

    Parameters:
        lines (list): the source lines.
        first_line (int): the 1-based line number of lines[0].

    Returns:
        list: (line_number, text) pairs, one per paragraph.
    """
    out = []
    buf = []
    start = first_line
    for offset, line in enumerate(lines):
        if line.strip():
            if not buf:
                start = first_line + offset
            buf.append(line.strip())
        elif buf:
            out.append((start, ' '.join(buf)))
            buf = []
    if buf:
        out.append((start, ' '.join(buf)))
    return out


def check_text(text, path, first_line=1):
    """Report the two markup mistakes in one block of reStructuredText.

    Parameters:
        text (str): the source text.
        path (str): the path to name in a finding.
        first_line (int): the 1-based line number that text starts on.

    Returns:
        list: findings, each a `path:line: CODE: message` string.
    """
    findings = []
    lines = _uncode(text.split('\n'))

    for offset, line in enumerate(lines):
        match = _ONE_COLON.match(line)
        if match and match.group(1) in _DIRECTIVES:
            findings.append(f'{path}:{first_line + offset}: N1: '
                            f'directive ".. {match.group(1)}:" has one colon, so it '
                            f'and everything indented under it is dropped')

    for line_number, para in _paragraphs(lines, first_line):
        for strong in _STRONG.finditer(para):
            if _NESTED.search(strong.group(1)):
                findings.append(f'{path}:{line_number}: N2: '
                                f'inline markup nested inside a strong span renders '
                                f'literally: **{strong.group(1)[:48]}**')
    return findings


def _docstring_findings(path):
    """Report markup mistakes in every docstring of one Python module.

    Parameters:
        path (Path): the module to read.

    Returns:
        list: findings.
    """
    tree = ast.parse(path.read_text(encoding='utf-8'))
    findings = []
    nodes = [tree] + [n for n in ast.walk(tree)
                      if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))]
    for node in nodes:
        doc = ast.get_docstring(node, clean=False)
        if not doc:
            continue
        # The docstring node is the first statement; its end_lineno is the closing
        # quote, so the text starts (number of lines) earlier.
        expr = node.body[0]
        first = expr.end_lineno - doc.count('\n')
        findings += check_text(doc, str(path.relative_to(_ROOT)), first)
    return findings


def test_no_markup_that_silently_drops_text():
    """Every .rst page and every docstring is free of the two silent-loss mistakes."""
    findings = []
    for path in sorted(_DOCS.rglob('*.rst')):
        if '_build' in path.parts:
            continue
        findings += check_text(path.read_text(encoding='utf-8'),
                               str(path.relative_to(_ROOT)))
    for path in sorted(_SRC.rglob('*.py')):
        # _version.py is generated by setuptools_scm at build time and is not tracked;
        # it carries no docstring and is not ours to check.
        if path.name == '_version.py':
            continue
        findings += _docstring_findings(path)

    assert not findings, (
        f'{len(findings)} markup findings that Sphinx does not report:\n'
        + '\n'.join(findings))


def test_the_check_reports_the_mistakes_it_exists_for():
    """The two rules fire on text that carries the defects, and not on correct text."""
    dropped = check_text('.. note:\n\n   This paragraph never reaches the page.\n', 'x')
    assert len(dropped) == 1
    assert 'N1' in dropped[0]

    nested = check_text('A **strong ``literal`` span** renders its asterisks.\n', 'x')
    assert len(nested) == 1
    assert 'N2' in nested[0]

    clean = check_text(
        '.. note::\n\n   This one is published.\n\n'
        'A **strong span** and a ``literal`` beside it are correct.\n\n'
        '.. _a-hyperlink-target:\n\n'
        'Literal blocks are exempt::\n\n'
        '   **a ``b`` c**\n',
        'x')
    assert not clean, clean

    # A directive body is published verbatim too, and it does not end in `::`, so it
    # needs its own exemption rather than the trailing-colon one.
    in_a_code_block = check_text(
        'Shown, not rendered:\n\n'
        '.. code-block:: text\n\n'
        '   **a ``b`` c**\n'
        '   .. note:\n\n'
        'Back to prose.\n',
        'x')
    assert not in_a_code_block, in_a_code_block
