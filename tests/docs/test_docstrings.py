##########################################################################################
# tests/docs/test_docstrings.py
#
# Runs check_docstrings.py over the package. That checker is the only thing in the
# repository that catches a docstring drifting from the signature or body it describes:
# the Sphinx gate does not, because a `Parameters:` entry naming a parameter that no
# longer exists, or missing one that does, builds perfectly cleanly.
#
# The rules it enforces are documented in check_docstrings.py's own module docstring.
##########################################################################################

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
_CHECKER = Path(__file__).resolve().parent / 'check_docstrings.py'
_SRC = _ROOT / 'src'


def _sources():
    """Every authored module of the package, in a stable order.

    Returns:
        list: paths to check.
    """
    # _version.py is written by setuptools_scm at build time, is not tracked, and
    # carries no docstring. It is a build artifact rather than a source file, and a
    # local full run materializes it, so excluding it by name keeps the check the
    # same whether or not the package has been built in place.
    return sorted(p for p in _SRC.rglob('*.py') if p.name != '_version.py')


def test_docstrings_match_the_code_they_describe():
    """Every docstring under src/ satisfies the mechanical rules of the style guide."""
    sources = _sources()
    assert sources, f'no sources found under {_SRC}'

    result = subprocess.run(
        [sys.executable, str(_CHECKER)] + [str(p) for p in sources],
        capture_output=True, text=True, cwd=str(_ROOT), check=False)

    # The checker prints its totals as the last line. Reporting the whole of stdout
    # rather than a tail: a totals line read through `tail` is how a checker on this
    # project once reported 24 findings that nobody saw.
    assert result.returncode == 0, (
        f'check_docstrings.py reported findings over {len(sources)} modules:\n'
        f'{result.stdout}{result.stderr}')


def test_the_checker_reports_a_docstring_that_does_not_match(tmp_path):
    """The check fails on a docstring whose Parameters block names no real parameter."""
    broken = tmp_path / 'broken.py'
    broken.write_text(
        '"""A module that carries one wrong docstring."""\n'
        '\n'
        '\n'
        'def f(a):\n'
        '    """Do nothing in particular.\n'
        '\n'
        '    Parameters:\n'
        '        b (int): a parameter this function does not have.\n'
        '    """\n',
        encoding='utf-8')

    result = subprocess.run(
        [sys.executable, str(_CHECKER), str(broken)],
        capture_output=True, text=True, cwd=str(_ROOT), check=False)

    assert result.returncode == 1, f'the checker passed a broken docstring:\n{result.stdout}'
    assert 'P1' in result.stdout or 'P2' in result.stdout, result.stdout
