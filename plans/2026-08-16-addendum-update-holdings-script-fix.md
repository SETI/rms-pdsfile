# Addendum — the owner directed a fix to `update_holdings_for_new_metadata.sh`

**Status: OWNER-DIRECTED, 2026-08-16.** The owner instructed, in this effort's
Phase 7 documentation work: fix `update_holdings_for_new_metadata.sh` rather than
describe its defect in the user guide; give the guide's "The order in which they
must be built" section explicit PDS3 and PDS4 command examples and a mermaid
diagram of the dependency DAG; and, as a standing principle, "we should never be
documenting bugs — we should be fixing bugs." Because the instruction came from
the owner, it is its own acknowledgment; this file records it so the freeze
question below has a written answer.

## Why an addendum at all

Ground rule 7 and `.cursor/rules/pdsfile_overrides.mdc` (6) freeze **the sync
shell scripts** as document-only. `update_holdings_for_new_metadata.sh` is not a
sync script — the user guide's own grouping places it in the rebuild group, not
the `pdsdata-sync-*` group — but `tests/holdings_maintenance/__init__.py` read
the freeze as covering every `.sh` file ("the sync/setup shell scripts are
document-only"), so the boundary was ambiguous. The owner's instruction settles
it for this script: the defect is fixed, with a regression test, and the guide
describes the fixed behavior. The six `pdsdata-sync-*` scripts and the four
copy/setup scripts remain document-only.

## The defects that were fixed

The script deleted seven products of one volume set's metadata and rebuilt six.
`_infoshelf-archives-metadata/` was the seventh: its deletion targeted
`<category>/$VOLSET`, a directory that never exists (the category holds
`<volset>_info.pickle`/`.py` files at its top level), so the old shelf survived,
and no `pdsinfoshelf` run over `archives-metadata/` followed, so a correct shelf
was never written either — the failure `pdsdependency.py`'s fifth general rule
reports. The fix corrects the deletion to the files that exist, adds the missing
rebuild, and reorders the commands into the topological order the user guide's
dependency graph documents. `tests/holdings_maintenance/test_update_holdings_script.py`
pins the delete/rebuild correspondence, the ordering, and the flat-category
deletion shape.

A second defect fell under the same ruling: the `checksums-archives-metadata/`
deletion's `${VOLSET}_*` glob also matched versioned siblings —
`<volset>_v1.0_metadata_md5.txt` and kin — that the rebuild, which reads only the
unversioned `archives-metadata/<volset>`, never rewrites, so a rerun destroyed
checksum files it could not restore. That deletion is narrowed to the one file
the rebuild writes, `${VOLSET}_metadata_md5.txt`, the volume-set argument is
validated as a single path component before anything is removed, and the test
module pins the property directly: each flat-category deletion, expanded as a
glob, must match exactly the files its rebuild writes.
