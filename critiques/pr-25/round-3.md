# PR-25 adversarial review — round 3

**Reviewed:** `git diff ab1fa3b..c49a913` (3,032 lines), branch
`pr-25-common-core`.
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of rounds 1 or 2.
**Verdict returned:** `goal met` — **0 Major**, 6 Minor, 2 Deferred.

## What the reviewer verified independently

It re-derived the statement counts and every per-function figure; wrote its own
differential probe recording every logger call and return value for
`load_directory_info`, `validate_tuples`, `write_archive` and the archive filter
against both originals, over a tree covering `.DS_Store`, `._*`, backup and
` copy` names, invisible paths and every branch of the tuple comparison, ×2
`archive_invisibles` — base ≡ head byte-for-byte for both flavors, and pds3 vs
pds4 differ in exactly the `info`/`normal` level, which is what shows the probe
is sensitive; made its own `--help`, `format_usage()` and `add_argument` dumps;
re-derived the ratchet delta; re-ran the id-set, `measured_files()` and tool-run
comparisons; reverted the three `global LOGDIRS` lines in its own `/tmp` copy and
got 3 failed / 1 passed; and spot-checked about thirty `file:line` citations
across the new deferred entries, all correct.

It also judged the `PYTHONHASHSEED` pinning "legitimate, not laundering" — a
judgement that m-numbers below partly overturn, in the author's favour of being
*more* careful rather than less.

## Minor findings — all six accepted

| # | Finding | Resolution |
|---|---|---|
| m1 | The owner-facing addendum still carried the pre-round-2 figures (27/23/25/19) where the record had been updated. It is the document §6.4 requires the owner to acknowledge | **Accepted.** Now 36/39/34/35, re-measured at this head |
| m2 | §13 said "New entries: 92 – 98"; the PR adds 92–**99** | **Accepted.** Corrected, with a clause describing 99 |
| m3 | §10 said "four texts have no exact match at head"; a tokenize-based set diff gives **five** — the table folds the pds3 and pds4 spellings of one comment into one row | **Accepted.** Re-derived with `tokenize` (5 absent from the trio, 17 new in the trio, 18 absent from the head *pair*, 0 new in the pair) and reworded to "five texts, in four dispositions" |
| m4 | The addendum's "four deviations" omitted two more: the plan's `ToolSpec` lists `holdings_sentinel` and `index_ext`, which are not fields, and a `log_extra_handlers` **flag**, which is an ordered `handler_factories` tuple. The tuple is material because the order is observable | **Accepted.** A fifth deviation section added, explaining that neither archives tool reads a sentinel or an index extension, and that a boolean would not carry the handler *order* — which is exactly what the two `--log`/`PDS_LOG_ROOT` invocations now put under the gate |
| m5 | `_common.py:156-158` — the `No archives for checksum files` branch of the shared driver is pinned by no test and reached by no capture. The only branch of the migrated driver no gate observed | **Accepted.** A checksums-path invocation added for each tool. Both trees now print `No archives for checksum files: <disk>/holdings/checksums-volumes/HSTNx_xxxx` (and the pds4 equivalent) and exit 1, inside the diffed evidence |
| m6 | Two small record inaccuracies: `compare_toolruns.py`'s `DISKNAME` regex could not match the harness's fixed `/tmp/tool-run-disk`, so that substitution was dead; and §14 named only `round-1.md` | **Accepted.** Regex fixed to match both spellings; §14 now names every round |

## What m5 turned up, which the round did not

Adding the two invocations shifted the run sequence, and the re-run exposed **two
defects in the comparator itself** — both of which had been making the previous
rounds' numbers look better than the method deserved:

1. **`PYTHONHASHSEED=0` does not align the two runs.** The strings in each tool's
   `logfiles` set contain the run's own one-second time tag, so they hash
   differently from one run to the next even under a pinned seed; the two
   `Log file:` lines duly came out in opposite orders in five captures. Round 3
   had judged the pin sufficient. It is not. The comparator now **sorts each run
   of consecutive `Log file:` lines**, which is the honest normalization: that
   order is not a function of the code (deferred observation 99 records why), and
   it flips between two runs of the baseline tree as readily as between base and
   head.
2. **Log blocks were paired by sorting on content.** Several log files share a
   normalized name — five `_archives_<TIMETAG>_validate.log` blocks, for instance
   — and sorting by content paired whichever happened to sort first, which
   manufactured sixteen spurious differences. Blocks are now keyed by
   `(normalized name, occurrence index in run order)`, so the k-th same-named log
   of one run is compared with the k-th of the other. The two runs execute the
   same sequence, so that is the pairing that means something.

Re-measured with both fixes and the two new invocations: **36 invocations and 39
log files per tree, 4,005 normalized lines**, of which **34 stdout captures and
35 log files are identical**, and the six that differ differ only in the
traceback frames already recorded.

## Deferred

- **The Phase-6 harness lives in uncommitted scratch.** Its *results* are in
  `critiques/` as §6.2 requires, but PR-26 and PR-27 have to rebuild it from the
  prose. Worth committing under `scripts/` once its shape settles at five pairs.
  **Owner: PR-26.**
- **Nothing in the repo pins the rendered `--help` text.** `test_task_flags.py`
  pins flag *semantics*; the byte-identity of the help output rests on
  out-of-repo probes. With `build_arg_parser` about to serve five pairs, a
  committed `--help` golden per tool is cheap insurance against a template edit
  silently rewording ten tools' help. **Owner: PR-26/27.**

Both are recorded here rather than in `deferred-observations.md`: neither is a
property of the code, and both are instructions to the next PR in this phase,
which is what this file is read for.

## Rebuttals

None. Every Minor was accepted.

## Re-verification after the fixes

None of the round-3 fixes touched `src/pdsfile/` — they are the harness and the
comparator under `/tmp`, the records, and the addendum. Per §6.6 step 5 the
full-data record carries forward unchanged (ns 892 → 896, `s` empty). The
tool-run gate was re-run because its harness changed, and §5's table is from that
run.
