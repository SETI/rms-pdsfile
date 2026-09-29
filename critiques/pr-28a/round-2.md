# PR-28a adversarial review — round 2

Reviewed at `356e055`, including round 1's own changes to the test and the capture
harness. **Nothing Major.** The reviewer re-derived the extraction rather than
taking round 1's word for it — the extracted body differs from the base block by one
blank line and the `return` — and re-diffed the gate independently. Two Minors and
three Nits, all acted on.

## Findings and disposition

**1. Minor — the record overclaimed the attachment control. Corrected, and the
number measured.** §3.1 said each writable probe run logs an error "so that the
handlers have something to write", making an unattached handler visible. Built the
mutation and counted: the control fires on **7 of the 10 tools**, not ten.
`pds4archives`'s probe run succeeds and logs nothing at WARNING or above, so its
handler files are empty in both halves; the two index shelf tools recreate the same
files from `run_index_main`'s per-target loop, which writes into the tool's own log
directory. The record now names all three exceptions.

**2. Minor — one valid input class was executed by nothing: `--quiet` with `--log`.
Fixed in the harness.** No gate scenario passed `--log`; no probe scenario passed
`--quiet`. The reviewer proved the cell unpinned by mutating `if not args.quiet:` to
`if not args.quiet or args.log:`, which changes behaviour only when both flags are
given: byte-identical gate, byte-identical probe, 337 passed. The probe now runs
each tool a third time, `--quiet` with a writable log root. Base-versus-base is
still 0, base-versus-head is still the same 30 traceback lines, and the mutation
that used to be invisible now moves **191 probe lines**.

**3. Nit — `setup_run`'s `Raises:` named one of the three statuses it produces.
Fixed.** `parse_args` exits 0 for `--help` and 2 for a command line it cannot
classify; 30 of the 158 gate scenarios take one of those. The base had no such
section, so this PR introduced the omission. The docstring now names all three.

**4. Nit — `raw=`'s stated justification was not demonstrated. Corrected.** The
reviewer built the duplication `log_paths_for` guards against and found the **set**
moves for all ten tools too, because each driver logs one `Log file` line per path;
and that the other shape is unreachable, since pdslogger deduplicates handlers by
path. The total is kept as a second cheap check, and the record now says that
rather than claiming a safety net.

**5. Nit — the plan still carried the sentence round 1 fixed in the validation
record, and one assertion was described too strongly. Both fixed.** The plan now
says "driver-backed"; the record says the tool's log directory holds exactly the two
files **at its top level**, which is what `glob('*.log')` asserts.

## What round 2 checked and found clean

Round 1's test change fails under the no-attach mutation, and its exact-two-element
list is stable — both handler factories default to `rotation='none'`, so no rotated
third file, and every per-target log lands one directory down. `logroot()` is
deterministic across six independent captures. No stranded comments, no dead
`parser`, no newly unused imports. `run_selection_main`'s and `run_index_main`'s
`Raises:` sections remain true. `check_record_numbers.py` is not pytest-collectable
and each of its `expect()` calls is backed by a tree-derived assertion.
