##########################################################################################
# tests/holdings_maintenance/__init__.py
#
# Tests for the holdings-maintenance CLI tools (issue #82).
#
# Every tool is driven as a subprocess against a disposable copy of an explicitly
# declared subset of real holdings (see subsets.py and conftest.py). Subprocesses
# are not a convenience: PdsFile.CACHE is a class-level cache keyed by *logical*
# path and the test session preloads the real holdings tree, so an in-process
# call would resolve a temporary-tree path back to the real tree.
#
# test_re_validate.py is the exception. Everything it covers is pure over text,
# paths and an argparse namespace and constructs no PdsFile, so it runs in-process
# and needs no holdings at all; its own header says so.
#
# Deliberately NOT covered here:
#
#   * re_validate.validate_one_volume() and its batch driver loop -- they call the
#     five sibling tools against a real volume, which those tools' own modules
#     already cover, and send_email(), which opens a socket. The message that one
#     builds is covered through format_email().
#   * holdings_maintenance/pds3/*.sh -- the sync/setup shell scripts are
#     document-only; they are covered by prose in the user guide, not by tests.
##########################################################################################
