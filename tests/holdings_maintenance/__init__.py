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
# Deliberately NOT covered here (ground rule 7 of the modernization plan --
# "leave re_validate alone for now", "sync shell scripts are document-only"):
#
#   * holdings_maintenance/pds3/re_validate.py -- neither imported nor executed.
#     It is frozen: its email/batch internals are out of scope for this effort,
#     and importing it at collection time would drag those internals into every
#     test run for no benefit.
#   * holdings_maintenance/pds3/*.sh -- the sync/setup shell scripts are
#     document-only; they are covered by prose in the user guide (PR-32), not by
#     tests.
##########################################################################################
