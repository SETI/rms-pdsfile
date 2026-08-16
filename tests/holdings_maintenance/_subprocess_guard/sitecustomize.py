##########################################################################################
# tests/holdings_maintenance/_subprocess_guard/sitecustomize.py
#
# Python imports `sitecustomize` automatically at interpreter startup if it is on the
# path, which is how a tool subprocess gets the same read-only-holdings guard the pytest
# process installs. `support.ToolTree.env` puts this directory on PYTHONPATH and names
# the roots to protect in PDSFILE_READONLY_ROOTS.
#
# **This fails closed.** Python catches whatever a sitecustomize hook raises, prints it,
# and carries on starting up, so a guard that could not install would leave the tool
# running unprotected while its test still passed -- a gate that cannot fail, which is
# the defect this guard exists to prevent rather than to imitate. The interpreter is
# therefore killed outright if the guard is wanted and did not install.
#
# The directory holds nothing else, so putting it on PYTHONPATH shadows nothing.
##########################################################################################

import os
import sys

_WANTED = bool(os.environ.get('PDSFILE_READONLY_ROOTS', ''))


def _die(reason):
    """Stop the interpreter rather than run a tool without the guard.

    Parameters:
        reason (str): what went wrong, written to stderr before exiting.
    """

    sys.stderr.write(
        f'sitecustomize: refusing to start without the read-only holdings guard: '
        f'{reason}\n')
    sys.stderr.flush()
    os._exit(70)                    # EX_SOFTWARE; _exit so nothing can catch it


if _WANTED:
    try:
        from tests.holdings_maintenance import readonly_roots
    except Exception as error:
        _die(f'the guard could not be imported ({error!r})')

    try:
        readonly_roots.install()
    except Exception as error:
        _die(f'the guard raised while installing ({error!r})')

    if not readonly_roots.installed():
        _die('the guard reported that it did not install')
