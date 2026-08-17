# Addendum — the owner directed fixes to the four items parked for a ruling

**Status: OWNER-DIRECTED, 2026-08-16.** Four items had each been recorded and
left for an owner ruling rather than fixed. The owner instructed that all four
be fixed in one PR, with each verified against the current tree before acting.
Because the instruction came from the owner, it is its own acknowledgment; this
file records it so the freeze questions below have a written answer.

## The four items

1. **Observation 3402 — the Python floor.** `pdsfile_overrides.mdc` still gave
   the floor as 3.10 after #146 moved `requires-python` to `>=3.11`;
   `pyproject.toml` is the authority. The owner directed correcting the
   overrides file and every other surviving 3.10 claim in the tree. The
   observation register held this one for the owner because the overrides file
   records owner decisions.

2. **The ruff `.pyi` exclusion.** `pyproject.toml` carried
   `extend-exclude = ["src/pdsfile/**/*.pyi"]` with an unmeasured justification.
   The owner directed resolving it by measurement: lint the stubs with the
   project configuration, and either bring them under the gate with the same
   permanent per-file-ignores their `.py` counterparts carry, or keep the
   exclusion if the measurement shows linting them would require new ratchet
   entries — the ratchet may only shrink and inline `noqa` is prohibited.
   Either way, the comment must state what was measured.

3. **Observation 4064 — `exit -1` in the copy/setup scripts.** Ground rule 7
   and deviation (6) of `pdsfile_overrides.mdc` hold the shell scripts
   document-only, which is why the twelve `exit -1` sites in
   `setup_new_holdings.sh`, `copy_documents.sh`, `copy_shelves.sh`,
   `copy_all_except_metadata.sh` and `create_fake_volumes_for_metadata.sh`
   were recorded rather than fixed. **The owner lifted the freeze for exactly
   this change**, extending the 2026-08-07 exit-code ruling (deferred
   observation 135, applied to `update_holdings_for_new_metadata.sh` under the
   2026-08-16 instruction in
   `plans/2026-08-16-addendum-update-holdings-script-fix.md`) to these five,
   conditional on every site being reachable only by an invalid invocation —
   which was verified before the change was made. The scripts otherwise remain
   document-only.

4. **Observation 4062 — the PDS4 archive products.** `Pds4File.child` rejected
   `checksums-archives-bundles/<set>_md5.txt` because `BUNDLESET_PLUS_REGEX`
   admitted no ending after a bundle-set name, so no PDS4 archive checksum and
   no PDS4 archive info shelf could be built. The owner directed fixing it as a
   deliberate behavior change to the frozen class, derived from the PDS3
   pattern rather than invented, with the failure reproduced first, the
   API-freeze gate confirming the manifest does not move, and tests pinning
   both directions plus an end-to-end build of both archive-side products
   against a temporary tree.

## Why an addendum at all

Items 3 and 4 change frozen behavior — the document-only scripts and the public
`Pds4File` class — and §6.4 requires a plan-level record when a ground rule is
lifted or a frozen surface deliberately moves. Items 1 and 2 are recorded here
because their resolutions (which 3.10 mentions are claims rather than
historical records, and which way the stub-linting question went) are owner
calls, not judgment calls left to a PR.

The register discharges observations 3402, 4062 and 4064 against this
instruction; `critiques/observations.md` carries the arithmetic.
