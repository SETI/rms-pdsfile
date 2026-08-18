##########################################################################################
# tests/holdings_maintenance/_subprocess_guard/sitecustomize.py
#
# Python imports `sitecustomize` automatically at interpreter startup if it is on the
# path, which is how a tool subprocess gets two things the pytest process gives itself:
# the read-only-holdings guard, and -- when a coverage run asked for it -- coverage
# measurement of the tool. `support.ToolTree.env` puts this directory on PYTHONPATH,
# names the roots to protect in PDSFILE_READONLY_ROOTS, and passes COVERAGE_PROCESS_START
# through when one is set.
#
# Startup is the only place either hook can go. The guard has to be in place before the
# tool's first write, and coverage has to start before `pdsfile` is imported, or the
# module-level lines of every module the tool imports are already gone.
#
# **Both fail closed.** Python catches whatever a sitecustomize hook raises, prints it,
# and carries on starting up, so a hook that could not install would leave the tool
# running unprotected -- or unmeasured while a report claims otherwise -- and its test
# would still pass: a gate that cannot fail, which is the defect these hooks exist to
# prevent rather than to imitate. The interpreter is therefore killed outright if a hook
# is wanted and did not install. That matters most for coverage, because a subprocess's
# stderr is captured by the test that ran it and read by nobody, so a warning there would
# be invisible.
#
# The directory holds nothing else, so putting it on PYTHONPATH shadows nothing.
##########################################################################################

import os
import sys

_GUARD_WANTED = bool(os.environ.get('PDSFILE_READONLY_ROOTS', ''))
_COVERAGE_WANTED = bool(os.environ.get('COVERAGE_PROCESS_START', ''))


def _die(hook, reason):
    """Stop the interpreter rather than run a tool without a hook it was promised.

    Parameters:
        hook (str): which hook did not install, named as the message needs it.
        reason (str): what went wrong, written to stderr before exiting.
    """

    sys.stderr.write(f'sitecustomize: refusing to start without {hook}: {reason}\n')
    sys.stderr.flush()
    os._exit(70)                    # EX_SOFTWARE; _exit so nothing can catch it


# Coverage first: it must be running before anything else this file imports, so that
# a module imported by a later hook is measured rather than recorded as never executed.
if _COVERAGE_WANTED:
    try:
        import coverage
    except Exception as error:
        _die('coverage measurement', f'coverage could not be imported ({error!r})')

    try:
        # Reads COVERAGE_PROCESS_START as its config file; `parallel` there is what
        # gives this process its own data file instead of overwriting the parent's.
        _started = coverage.process_startup()
    except Exception as error:
        _die('coverage measurement', f'coverage.process_startup() raised ({error!r})')

    # process_startup() returns None both when it starts nothing and when this process
    # had already started coverage, so the live Coverage object is what settles it.
    if _started is None and coverage.Coverage.current() is None:
        _die('coverage measurement', 'coverage.process_startup() started no measurement')

if _GUARD_WANTED:
    try:
        from tests.holdings_maintenance import readonly_roots
    except Exception as error:
        _die('the read-only holdings guard',
             f'the guard could not be imported ({error!r})')

    try:
        readonly_roots.install()
    except Exception as error:
        _die('the read-only holdings guard',
             f'the guard raised while installing ({error!r})')

    if not readonly_roots.installed():
        _die('the read-only holdings guard',
             'the guard reported that it did not install')
