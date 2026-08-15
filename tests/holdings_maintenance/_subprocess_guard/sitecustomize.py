##########################################################################################
# tests/holdings_maintenance/_subprocess_guard/sitecustomize.py
#
# Python imports `sitecustomize` automatically at interpreter startup if it is on the
# path, which is how a tool subprocess gets the same read-only-holdings guard the pytest
# process installs. `support.ToolTree.env` puts this directory on PYTHONPATH and names
# the roots to protect in PDSFILE_READONLY_ROOTS.
#
# The directory holds nothing else, so putting it on PYTHONPATH shadows nothing.
##########################################################################################

try:
    from tests.holdings_maintenance import readonly_roots
except ImportError:                                             # pragma: no cover
    pass
else:
    readonly_roots.install()
