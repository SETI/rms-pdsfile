"""Check each maintenance tool module's docstrings against the vocabulary of its flavor.

Ten of the eleven modules this PR documents are five near-identical pairs: a `pds3`
module and a `pds4` module that do the same job over a different PDS version. Writing ten
docstring sets in one sitting is therefore the task where a sentence written for one half
of a pair is pasted onto the other, and the paste is invisible to every gate the earlier
docstring PRs shipped, because the two files are near-identical to begin with.

The two halves do not share a vocabulary, and that is what makes the paste mechanically
detectable. A `pds3` tool walks `volumes/` under `/holdings/`, builds `Pds3File` objects,
calls its unit a volume and its index tables `.tab`; a `pds4` tool walks `bundles/` under
`/pds4-holdings/`, builds `Pds4File` objects, calls its unit a bundle and its index tables
`.csv`. A `pds4` docstring that says "volume", or a `pds3` one that says "bundle", is
almost certainly pasted.

Checks:

    V0  The module has no docstring, so nothing else about the module can be evaluated.
    V1  A docstring in a `pds4` module uses a term of the PDS3 vocabulary.
    V2  A docstring in a `pds3` module uses a PDS4 term.
    V3  The module docstring does not name the module it documents.
    V4  A docstring names a module of the opposite flavor that is not its own twin.

V1 and V2 are the two directions the plan asks for, and they are checked over **every**
docstring in the file -- module, class, function and nested function -- rather than over
the module docstring alone, because the parameter descriptions are where most of this
PR's prose is and a per-parameter paste is the likeliest kind.

V3 catches a wholesale copy whose vocabulary happens to be neutral, which V1 and V2 are
both silent on. It reads the whole module docstring and not its summary line: these
modules announce themselves by their `progname`, which for all five `pds4` tools is the
`pds3` tool's name, so a summary line that had to carry the module's own stem would force
prose that contradicts what the tool calls itself.

V4 is what V3 cannot see: a docstring that names some other module of the other flavor.
Naming its **own twin** is not a finding and is what these docstrings are expected to do,
since what a tool's specification declares is best said by what differs from the other
half of the pair; naming a different tool of the other flavor is a paste.

**The version numbers themselves -- "PDS3", "PDS4", "pds3", "pds4" -- are deliberately not
in either vocabulary, and that is the one judgment in this script.** Every docstring here
has to contrast its tool with its twin, so the version number by itself is not evidence of
anything, while a `pds4` docstring saying "volume" or a `pds3` one saying "bundle" is. The
cost is real and is stated rather than hidden: a paste that carried only the version
number would pass V1 and V2. Nothing in this PR's prose is in that position, because a
docstring long enough to be worth pasting names its unit several times, which is the term
the vocabularies do carry.

ALLOWED holds the terms that survive a scan anyway. They are all of one kind: the PdsFile
base class names its unit a bundle, so the methods and attributes a PDS3 tool calls are
spelled `is_bundle_dir`, `log_path_for_bundle` and so on whatever the tool calls its unit
in prose. `Pds3File` aliases some of them to `volume` spellings and not others, so a `pds3`
docstring naming the method it actually calls has to write "bundle".

Each entry is stripped from the text once per occurrence before the scan, so an entry
licenses the exact string it names and nothing else: `log_path_for_bundle` is allowed and
the bare word "bundle" left behind by an edit to it is not. An entry is scoped either to a
flavor or to one module by name. The whole table is printed with the findings so that it
cannot grow silently.

Usage:
    python check_flavor_vocabulary.py FILE [FILE ...]

Exit status is 1 if any finding is reported, 0 otherwise.
"""

import ast
import pathlib
import re
import sys

# Terms belonging to one flavor only. Each is matched with word boundaries, so
# `bundlename` does not match `bundle` and `volumes` does not match `volumeset`.
PDS3_TERMS = ('volume', 'volumes', 'volset', 'volsets', 'volumeset', 'volumesets',
              'Pds3File', '.tab', '/holdings/', 'log_path_for_volume',
              'log_path_for_volset', 'volume_pdsfile', 'volset_pdsfile')

PDS4_TERMS = ('bundle', 'bundles', 'bundleset', 'bundlesets', 'Pds4File',
              '.csv', '/pds4-holdings/', 'log_path_for_bundle',
              'log_path_for_bundleset', 'bundle_pdsfile', 'bundleset_pdsfile')

# The stems of the modules in scope, by flavor. V4 reads these.
PDS3_MODULES = ('pdsarchives', 'pdschecksums', 'pdsindexshelf', 'pdsinfoshelf',
                'pdslinkshelf', 'linkshelf_repairs')

PDS4_MODULES = ('pds4archives', 'pds4checksums', 'pds4indexshelf', 'pds4infoshelf',
                'pds4linkshelf')

# Each module's twin: the module of the other flavor that does the same job. V4 reads
# this. `linkshelf_repairs` has no twin of its own, and the tool whose absence of a
# counterpart it exists to explain is `pds4linkshelf`.
TWIN = {'pdsarchives': 'pds4archives', 'pdschecksums': 'pds4checksums',
        'pdsindexshelf': 'pds4indexshelf', 'pdsinfoshelf': 'pds4infoshelf',
        'pdslinkshelf': 'pds4linkshelf', 'linkshelf_repairs': 'pds4linkshelf',
        'pds4archives': 'pdsarchives', 'pds4checksums': 'pdschecksums',
        'pds4indexshelf': 'pdsindexshelf', 'pds4infoshelf': 'pdsinfoshelf',
        'pds4linkshelf': 'pdslinkshelf'}

# Terms a docstring may carry although they belong to the other flavor. Each entry is
# (scope, term, reason), where the scope is a flavor name or one module's stem; the term
# is stripped once per occurrence before the scan, so it licenses itself and not the bare
# flavor word inside it.
ALLOWED = (
    # Shared PdsFile names. The base class calls its unit a bundle, so a PDS3 tool that
    # names the method it calls has to spell it that way.
    ('pds3', 'log_path_for_bundle',
     "_shelf_common.UNIT_LOG_PATH_METHOD is 'log_path_for_bundle', and pdslinkshelf's "
     'spec names it; Pds3File.log_path_for_volume is an alias of the same method'),
    ('pds3', 'log_path_for_bundleset',
     "_shelf_common.UNITSET_LOG_PATH_METHOD is 'log_path_for_bundleset', which "
     'run_selection_main picks for a pds3 target naming only a volume set'),
    ('pds3', 'is_bundle_dir',
     'PdsFile.is_bundle_dir has no volume-spelled alias; _shelf_common tests it for '
     'both flavors'),
    ('pds3', 'is_bundleset_dir',
     'PdsFile.is_bundleset_dir has no volume-spelled alias'),
    ('pds3', 'is_bundle_file',
     'PdsFile.is_bundle_file has no volume-spelled alias'),
    ('pds3', 'bundlename',
     'PdsFile.bundlename is what run_selection_main tests to pick a log path method'),
    ('pds3', 'bundletype_',
     'PdsFile.bundletype_ is what resolve_holdings_paths compares against spec.unit'),

)

IDENTIFIER_CHAR = r'[A-Za-z0-9_]'


def term_regex(term):
    """Return the pattern that matches one vocabulary term as a whole word.

    A term beginning or ending in a character that is not part of an identifier, such as
    `.tab` or `/holdings/`, gets a boundary only on the sides where one means anything.
    Without that, `.tab` would never match, since a dot is already a boundary.

    Parameters:
        term (str): the term to match.

    Returns:
        re.Pattern: the compiled pattern.
    """

    left = f'(?<!{IDENTIFIER_CHAR})' if re.match(IDENTIFIER_CHAR, term[0]) else ''
    right = f'(?!{IDENTIFIER_CHAR})' if re.match(IDENTIFIER_CHAR, term[-1]) else ''

    return re.compile(left + re.escape(term) + right)


PDS3_PATTERNS = [(term, term_regex(term)) for term in PDS3_TERMS]
PDS4_PATTERNS = [(term, term_regex(term)) for term in PDS4_TERMS]


def flavor_of(path):
    """Return which half of a pair one file belongs to.

    Parameters:
        path (pathlib.Path): the module file.

    Returns:
        str: 'pds3' or 'pds4', taken from the package directory the file sits in, and
        None for a file in neither.
    """

    parent = path.parent.name
    return parent if parent in ('pds3', 'pds4') else None


def docstrings_of(tree):
    """Return every docstring in one parsed module, with the name of what carries it.

    Parameters:
        tree (ast.Module): the parsed module.

    Returns:
        list: (label, text) pairs, the module's own docstring first where there is one.
        A nested function is labeled with the name of the function holding it.
    """

    found = []
    doc = ast.get_docstring(tree)
    if doc:
        found.append(('module', doc))

    def walk(node, prefix):
        """Collect the docstrings of one node's classes and functions, recursively.

        Parameters:
            node (ast.AST): the node whose body is read.
            prefix (str): what to write in front of each name found.
        """

        for child in node.body:
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                label = prefix + child.name
                text = ast.get_docstring(child)
                if text:
                    found.append((label, text))
                walk(child, label + '.')

    walk(tree, '')

    return found


def allowed_terms(flavor, stem):
    """Return the terms one module may carry although they belong to the other flavor.

    Parameters:
        flavor (str): 'pds3' or 'pds4'.
        stem (str): the module's file stem.

    Returns:
        set: the terms whose scope is this flavor or this module.
    """

    return {term for scope, term, _reason in ALLOWED if scope in (flavor, stem)}


def strip_allowed(text, terms):
    """Return one docstring with a given set of terms removed.

    Each term is replaced by a space rather than deleted, so that removing it cannot join
    two words into a third that then matches.

    Parameters:
        text (str): the docstring.
        terms (set): the terms to remove.

    Returns:
        tuple: the text with those terms removed, and the set of terms that were found
        in it.
    """

    used = set()
    for term in sorted(terms):
        pattern = term_regex(term)
        if pattern.search(text):
            used.add(term)
            text = pattern.sub(' ', text)

    return (text, used)


def main(argv):
    """Run every check over every file named on the command line.

    Parameters:
        argv (list): the file paths to check.

    Returns:
        int: 1 if any finding was reported, 0 otherwise.
    """

    paths = [pathlib.Path(name) for name in argv]

    findings = []
    counts = {}
    exceptions_used = {}

    def report(path, code, text):
        """Record one finding and count it under its code.

        Parameters:
            path (pathlib.Path): the file the finding is about.
            code (str): the check that produced it.
            text (str): the description printed after the code.
        """

        findings.append(f'{path.name}: {code}: {text}')
        counts[code] = counts.get(code, 0) + 1

    for path in paths:
        flavor = flavor_of(path)
        if flavor is None:
            report(path, 'V0', 'file is in neither the pds3 nor the pds4 package')
            continue

        tree = ast.parse(path.read_text())
        docs = docstrings_of(tree)

        if not ast.get_docstring(tree):
            report(path, 'V0', 'module has no docstring')

        wrong = PDS3_PATTERNS if flavor == 'pds4' else PDS4_PATTERNS
        other_flavor = 'pds3' if flavor == 'pds4' else 'pds4'
        code = 'V1' if flavor == 'pds4' else 'V2'
        licensed = allowed_terms(flavor, path.stem)
        others = PDS3_MODULES if flavor == 'pds4' else PDS4_MODULES

        for label, text in docs:
            (scanned, used) = strip_allowed(text, licensed)
            for term in used:
                exceptions_used.setdefault(term, []).append(f'{path.name}:{label}')

            for term, pattern in wrong:
                hits = len(pattern.findall(scanned))
                if hits:
                    report(path, code,
                           f'{label} docstring uses "{term}" {hits} time(s), which '
                           f'belongs to the {other_flavor} vocabulary')

            for other in others:
                if other in (path.stem, TWIN.get(path.stem)):
                    continue
                if term_regex(other).search(scanned):
                    report(path, 'V4', f'{label} docstring names "{other}", a '
                                       f'{other_flavor} module that is not its twin')

        module_doc = ast.get_docstring(tree) or ''
        if path.stem not in module_doc:
            report(path, 'V3', f'module docstring does not name "{path.stem}"')

    for line in findings:
        print(line)

    total = sum(counts.values())
    print()
    print(f'{total} findings over {len(paths)} files')
    for code in sorted(counts):
        print(f'  {code}: {counts[code]}')

    print()
    print(f'ALLOWED, {len(ALLOWED)} entries:')
    for scope, term, reason in ALLOWED:
        where = exceptions_used.get(term, [])
        print(f"  [{scope}] {term}: {reason}")
        print(f'      used in: {", ".join(where) if where else "(nowhere)"}')

    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
