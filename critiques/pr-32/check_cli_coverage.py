#!/usr/bin/env python3
"""Compare the user guide's option tables against the programs' real argument parsers.

The user guide documents fifteen command-line programs. Nothing in the Sphinx build can
tell a flag that exists from a flag that does not, so a chapter can name an option the
program never had, omit one it does have, or -- the failure mode this package is most
exposed to, because five of the programs are near-copies of five others -- document its
twin's option instead of its own. This script reads both sides and reports every
disagreement.

**The parser side is the program's own.** Each parser is captured out of the module's
``main()`` by replacing ``parse_args`` and ``parse_intermixed_args`` with a function that
raises, so what is measured is the parser a run actually builds rather than a function
that happens to build one. Two of the programs build their parser inline in ``main()``
and have no builder to call, and this is how they are reached.

**The guide side is the chapter's text**, with three exclusions, each of which exists for
a reason:

  * lines inside a ``.. code-block:: console`` block are skipped. Those blocks are
    captured output, verified by being run rather than by being read, and one of them is
    a deliberately rejected flag;
  * a table row whose first cell names a program states that program's options rather
    than the shared ones, so such a row counts only for the program it names. That is
    what keeps the shared chapter's per-program summary table from attributing
    ``--archives`` to all ten programs;
  * a program's name followed by one or more flags is a command line for that program, so
    ``pdschecksums --infoshelf`` written in the info shelf chapter is removed before the
    flags of that line are read. A bare mention of another program is not removed, since
    a chapter is expected to name its neighbors.

For each program, what the guide documents is its own chapter's flags plus, for the ten
that share a command line, the shared chapter's. Three comparisons follow:

  1. a flag the guide attributes to a program whose parser does not have it;
  2. a flag on a parser that no chapter documents for that program;
  3. a default the parser carries that the guide does not state.

Comparison 3 is narrow by construction and the pass line says so: an option whose default
is false, empty or None has nothing to state, so only an option with a substantive
default is checked, and there is one such option across the fifteen programs.

Run it with no arguments to check the guide in the tree it sits in. It exits 1 if it
found anything, 2 if it could not run the comparison at all -- including when the
documentation directory holds no chapter, so that a clean pass over nothing is not
possible.
"""

import argparse
import importlib
import os
import re
import sys

# Every program the guide documents: its name, its module, and its chapter.
PROGRAMS = [
    ('pdsarchives', 'pdsfile.holdings_maintenance.pds3.pdsarchives', True),
    ('pdschecksums', 'pdsfile.holdings_maintenance.pds3.pdschecksums', True),
    ('pdsindexshelf', 'pdsfile.holdings_maintenance.pds3.pdsindexshelf', True),
    ('pdsinfoshelf', 'pdsfile.holdings_maintenance.pds3.pdsinfoshelf', True),
    ('pdslinkshelf', 'pdsfile.holdings_maintenance.pds3.pdslinkshelf', True),
    ('pds4archives', 'pdsfile.holdings_maintenance.pds4.pds4archives', True),
    ('pds4checksums', 'pdsfile.holdings_maintenance.pds4.pds4checksums', True),
    ('pds4indexshelf', 'pdsfile.holdings_maintenance.pds4.pds4indexshelf', True),
    ('pds4infoshelf', 'pdsfile.holdings_maintenance.pds4.pds4infoshelf', True),
    ('pds4linkshelf', 'pdsfile.holdings_maintenance.pds4.pds4linkshelf', True),
    ('pdsdependency', 'pdsfile.holdings_maintenance.pds3.pdsdependency', False),
    ('crlf', 'pdsfile.holdings_maintenance.pds3.crlf', False),
    ('re_validate', 'pdsfile.holdings_maintenance.pds3.re_validate', False),
    ('shelf_consistency_check',
     'pdsfile.holdings_maintenance.pds3.shelf_consistency_check', False),
    ('show_opus_products', 'pdsfile.tools.show_opus_products', False),
]

# The chapter holding the command line the ten specification-driven programs share.
SHARED_CHAPTER = 'user_guide_maintenance_tools.rst'

# ``-h``/``--help`` is argparse's own and no chapter is expected to document it.
IGNORED_FLAGS = {'-h', '--help'}

# A flag token as the guide writes one: inside double backticks, one or two leading
# hyphens, then letters, digits and hyphens.
FLAG_IN_RST = re.compile(r'``(--?[A-Za-z][A-Za-z0-9-]*)')

# The opening of a block whose lines are captured output rather than documentation.
CONSOLE_BLOCK = re.compile(r'^(\s*)\.\.\s+code-block::\s+console\s*$')

# The first cell of a list-table row.
ROW_START = re.compile(r'^\s*\*\s+-\s*(.*)$')


class _ParserCapturedError(Exception):
    """Carries the parser out of the ``parse_args`` call that was about to consume it."""

    def __init__(self, parser):
        """Carry one parser out of the call that was about to consume a command line.

        Parameters:
            parser (argparse.ArgumentParser): The parser to carry.
        """

        super().__init__('parser captured')
        self.parser = parser


def capture_parser(module_name, prog):
    """Return the ArgumentParser one program's ``main()`` builds.

    ``parse_args`` and ``parse_intermixed_args`` are replaced for the duration with a
    function that raises, so ``main()`` runs as far as its own parser and no further.
    Both are replaced because the programs do not agree on which they call. ``sys.argv``
    is set to the program name alone, which is what a parser is built from before
    anything is parsed.

    Parameters:
        module_name (str): The dotted name of the program's module.
        prog (str): The program's name, used as ``sys.argv[0]``.

    Returns:
        argparse.ArgumentParser: The parser that ``main()`` built.

    Raises:
        RuntimeError: if ``main()`` returned or exited without parsing a command line,
            which means this program's parser cannot be reached this way.
    """

    module = importlib.import_module(module_name)

    real_args = argparse.ArgumentParser.parse_args
    real_intermixed = argparse.ArgumentParser.parse_intermixed_args

    def intercept(self, *args, **kwargs):
        """Raise instead of parsing, carrying the parser this was called on.

        Parameters:
            self (argparse.ArgumentParser): The parser the program built and was about
                to parse with. It is what this carries out.
            *args: Whatever the program passed; ignored.
            **kwargs: Whatever the program passed; ignored.

        Raises:
            _ParserCapturedError: always.
        """

        raise _ParserCapturedError(self)

    argparse.ArgumentParser.parse_args = intercept
    argparse.ArgumentParser.parse_intermixed_args = intercept
    saved_argv = sys.argv
    sys.argv = [prog]
    try:
        module.main()
    except _ParserCapturedError as captured:
        return captured.parser
    finally:
        argparse.ArgumentParser.parse_args = real_args
        argparse.ArgumentParser.parse_intermixed_args = real_intermixed
        sys.argv = saved_argv

    raise RuntimeError(f'no parser reached in {module_name}.main()')


def parser_actions(parser):
    """Return the optional actions of a parser, keyed by their first option string.

    Parameters:
        parser (argparse.ArgumentParser): The parser to read.

    Returns:
        dict: {first option string: (all option strings, default)}, omitting the
        positional arguments and argparse's own help action.
    """

    actions = {}
    for action in parser._actions:
        if not action.option_strings:
            continue
        if action.option_strings[0] in IGNORED_FLAGS:
            continue
        actions[action.option_strings[0]] = (tuple(action.option_strings),
                                             action.default)

    return actions


def option_rows(text, strings):
    """Return the list-table rows that document one option, as whole strings.

    A row runs from its ``* - `` marker to the marker of the next row or the end of the
    table, so a row's own continuation lines and its second cell are inside it and the
    neighbouring rows are not. A row belongs to this option when its first cell carries
    one of the option's flag spellings in inline literal markup.

    Parameters:
        text (str): The chapter's reStructuredText.
        strings (list): One option's flag spellings, as argparse holds them.

    Returns:
        list: The matching rows, each a single string. Empty if the chapter documents
        this option outside a list-table, which is why the caller falls back to the
        shared chapter before reporting anything.
    """

    rows = []
    current = None
    for line in text.splitlines():
        if ROW_START.match(line):
            if current is not None:
                rows.append('\n'.join(current))
            current = [line]
        elif current is not None:
            if line.strip() and not line.startswith((' ', '\t')):
                rows.append('\n'.join(current))
                current = None
            else:
                current.append(line)
    if current is not None:
        rows.append('\n'.join(current))

    wanted = [f'``{flag}' for flag in strings]
    return [row for row in rows
            if any(token in row.split('\n')[0] for token in wanted)]


def documented_flags(text, prog, all_progs):
    """Return the flags a page documents for one program, and where each was found.

    Parameters:
        text (str): The page's reStructuredText.
        prog (str): The program whose options are being collected.
        all_progs (set): Every program's name, so a table row keyed by another one, and
            a command line written for another one, can be left out.

    Returns:
        dict: {flag: line number of its first occurrence}.
    """

    others = sorted(name for name in all_progs if name != prog)
    command_lines = [re.compile(re.escape(name) + r'(?:\s+`*-{1,2}[A-Za-z][\w-]*`*)+')
                     for name in others]

    found = {}
    console_indent = None
    row_prog = None
    for lineno, line in enumerate(text.splitlines(), start=1):

        # Skip the body of a console block: it is captured output, not documentation.
        if console_indent is not None:
            if line.strip() == '':
                continue
            indent = len(line) - len(line.lstrip())
            if indent > console_indent:
                continue
            console_indent = None

        match = CONSOLE_BLOCK.match(line)
        if match:
            console_indent = len(match.group(1))
            continue

        # A table row whose first cell names a program belongs to that program.
        row = ROW_START.match(line)
        if row:
            row_prog = None
            for name in all_progs:
                if name in row.group(1):
                    row_prog = name
                    break
        if row_prog is not None and row_prog != prog:
            continue

        # A command line written for another program carries that program's flags.
        for pattern in command_lines:
            line = pattern.sub('', line)

        for flag in FLAG_IN_RST.findall(line):
            if flag in IGNORED_FLAGS:
                continue
            found.setdefault(flag, lineno)

    return found


def check(docs_dir):
    """Compare every program's parser with its chapter and return the findings.

    Parameters:
        docs_dir (str): The directory holding the user-guide chapters.

    Returns:
        tuple: the list of finding strings, and a dict of what was measured.

    Raises:
        OSError: from the ``open()`` calls below, if the directory, the shared chapter or
            any program's chapter is absent -- so that a run over a tree with no guide in
            it cannot report a clean pass over nothing.
    """

    names = {prog for prog, _, _ in PROGRAMS}

    shared_path = os.path.join(docs_dir, SHARED_CHAPTER)
    with open(shared_path, encoding='utf-8') as handle:
        shared_text = handle.read()

    findings = []
    n_actions = 0
    n_option_strings = 0
    n_defaults = 0

    for prog, module_name, shares_command_line in PROGRAMS:
        chapter = os.path.join(docs_dir, f'user_guide_{prog}.rst')
        with open(chapter, encoding='utf-8') as handle:
            chapter_text = handle.read()

        own = documented_flags(chapter_text, prog, names)
        documented = dict(own)
        if shares_command_line:
            for flag, lineno in documented_flags(shared_text, prog, names).items():
                documented.setdefault(flag, lineno)

        actions = parser_actions(capture_parser(module_name, prog))
        real = {flag for strings, _ in actions.values() for flag in strings}

        n_actions += len(actions)
        n_option_strings += len(real)

        # 1. A flag the guide attributes to this program that the parser lacks.
        for flag in sorted(documented):
            if flag not in real:
                where = SHARED_CHAPTER if flag not in own else os.path.basename(chapter)
                findings.append(
                    f'{prog}: {where} documents {flag}, which {prog} has no such option')

        # 2. A flag on the parser that no chapter documents for this program.
        for flag in sorted(real):
            if flag not in documented:
                findings.append(
                    f'{prog}: the parser has {flag} and no chapter documents it '
                    f'for {prog}')

        # 3. A substantive default the guide does not state. The search is scoped to
        # the option's own table row rather than to the whole chapter, so a value that
        # happens to appear in prose, in an example or in another option's row does not
        # stand in for the statement this asks for.
        for _first, (strings, default) in sorted(actions.items()):
            if default in (None, False, True, '', 0) or default == []:
                continue
            n_defaults += 1
            rows = option_rows(chapter_text, strings) or option_rows(shared_text, strings)
            if not any(str(default) in row for row in rows):
                flags = '/'.join(strings)
                findings.append(
                    f'{prog}: {flags} defaults to {default!r} and the chapter does '
                    f'not state it')

    measured = {'programs': len(PROGRAMS), 'options': n_actions,
                'option strings': n_option_strings, 'defaults': n_defaults}

    return (findings, measured)


def main(argv=None):
    """Run the comparison and print what it measured.

    Parameters:
        argv (list): The command line. Defaults to sys.argv.

    Returns:
        int: 0 for no findings, 1 for findings, 2 if the comparison could not be run.
    """

    if argv is None:
        argv = sys.argv

    parser = argparse.ArgumentParser(
        description='Compare the user guide against the programs\' argument parsers.')
    parser.add_argument('--docs', type=str, default='',
                        help='The directory holding the user-guide chapters. Defaults '
                             'to docs/user_guide beside this repository\'s root.')
    args = parser.parse_args(argv[1:])

    docs_dir = args.docs
    if not docs_dir:
        here = os.path.dirname(os.path.abspath(__file__))
        docs_dir = os.path.join(here, '..', '..', 'docs', 'user_guide')
        docs_dir = os.path.normpath(docs_dir)

    try:
        (findings, measured) = check(docs_dir)
    except (OSError, RuntimeError) as error:
        print(f'check_cli_coverage: cannot run the comparison: {error}')
        return 2

    for finding in findings:
        print(finding)

    # Singular where the count is one, so the pass line reads as a measurement rather
    # than as a template: "1 default", not "1 defaults".
    summary = ', '.join(f'{measured[key]} {key if measured[key] != 1 else key[:-1]}'
                        for key in ('programs', 'options', 'option strings', 'defaults'))
    n = len(findings)
    print(f'check_cli_coverage: {n} finding{"" if n == 1 else "s"} over {summary}')

    return 1 if findings else 0


if __name__ == '__main__':
    sys.exit(main())
