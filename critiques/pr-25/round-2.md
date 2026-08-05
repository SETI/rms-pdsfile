# PR-25 adversarial review — round 2

**Reviewed:** `git diff ab1fa3b..6256e2a` (2,876 lines), branch
`pr-25-common-core`.
**Reviewer:** a fresh opus-class subagent with no development context and no
knowledge of round 1, given the same plan sections, the exact diff, and read
access to the head tree, the base tree, the holdings and the consumer repos.
**Verdict returned:** `goal met` — **0 Major**, 8 Minor, 3 Deferred.

## What the reviewer verified independently

It re-derived the AST statement counts and every per-function figure in §6; wrote
its own differential probes that import the base and head modules in separate
interpreters and capture the **entire logger call sequence** (name, args, kwargs,
level) plus return values for `load_directory_info`, `make_archive_filter` and
`validate_tuples` against **both** original copies, over inputs covering
`.DS_Store`, `._*` files and directories, backup and ` copy` names, invisible
files, and every branch of the tuple comparison — all identical, including the
two messages the `UP031` rewrite touched; AST-diffed the retained functions
(`initialize`, `reinitialize` and `update` are byte-identical); made its own
`--help` and `add_argument` dumps; re-ran the id-set comparison, the
`measured_files()` check and the tool-run comparison; re-derived the ratchet delta
and confirmed no new key; reverted the three `global LOGDIRS` lines in its own
`/tmp` copy and got 3 failed / 1 passed; and confirmed `re_validate.py:102` still
resolves and that neither consumer repo touches `holdings_maintenance` at all.

It also confirmed the four documented deviations against `ab1fa3b` — including
all six `write_archive`/task-function divergences the addendum lists — and that
the `pdsfile_overrides.mdc` deviation-(1) self-extension is gone from the diff.

## Major findings

**None.**

## Minor findings — all eight accepted, all in the evidence prose

| # | Finding | Resolution |
|---|---|---|
| m1 | §9 claimed "§5's runs exercise both error messages against a real volume". They did not: `grep mismatch` over the captures returned zero hits, because the harness never corrupted anything. The two rewritten `UP031` messages were the highest-risk part of the diff and the gate cited as covering them did not | **Accepted, and closed by widening the gate rather than by re-citing.** `tool_run_diff.sh` now truncates a real table to 100 bytes and `--validate`s, then moves a real label's modification time and `--validate`s, then `--reinitialize`s. Both messages now render inside the diffed evidence — `Byte count mismatch: 100 (filesystem) vs. 746315 (tarfile)` and `Modification time mismatch: 1500000000.0 (filesystem) vs. 1588638541.0 (tarfile)` — identically from both trees. Both corruptions use pinned times so the numbers are reproducible |
| m2 | §2 said `pytest tests/api/` is 15 ids; it collects **26** (1 freeze + 15 mixin-collision + 10 mixin-import-isolation) | **Accepted.** Corrected to 26 |
| m3 | §1 said ruff 0.15.7; the venv reports **0.15.22**, and every other record in the repo says 0.15.22 | **Accepted.** Corrected |
| m4 | §10 said "no comment text is new", measured against the head **trio**; against the trio, 17 texts are new (`_common.py`'s header, banners and notes). The claim is exactly true against the head **pair** | **Accepted.** §10 now says which comparison each half is about: four base texts absent from the trio, and against the pair alone, 18 absent and zero new |
| m5 | Two stale `_common.py` citations, both drifted by the two lines a round-1 docstring fix added: deferred 92's `:278-281` for the `*_LIMITS` (now `:280-283`) and §10's `:209` for the reworded comment (now `:211`) | **Accepted.** Both re-cited |
| m6 | §11's cross-check table under-reports its own script: the four infoshelf/linkshelf rows also produce `HSTN0_7176_md5_v001.txt`, because the probe's `pdschecksums --repair` setup step now versions too | **Accepted.** The table now says it lists each probed tool's own files, and names the extra entry |
| m7 | §5's invocation enumeration listed 14 + "the same thirteen" + 1 = 28 against a stated total of 27 | **Accepted.** The harness has since grown; §5 now enumerates 13 shared, 6 pds3-only and 2 pds4-only = **34**, which is what the script reports |
| m8 | The harness never set `PDS_LOG_ROOT` or passed `--log`, so `run_main`'s top-level `if args.log:` block — the only place the spec's handler-factory tuple is applied at the log root, and so the only place pds4's `warning_handler`-before-`error_handler` ordering runs — and the two-element `logfiles` set were both outside the gate | **Accepted.** Two invocations per tool added, one `--log <root>` and one with `PDS_LOG_ROOT` set. Both trees now write the same 39 log files with identical names and contents |

Re-measured after the harness change: **34 invocations and 39 log files per
tree, 3,999 normalized lines**, of which 32 stdout captures and 35 log files are
identical, and the four differing artifacts differ only in the traceback frames
§5 already recorded.

## Deferred

- **D1 → new entry 99.** Nine of the eleven tools build `logfiles` as a `set` and
  iterate it, so with a log root configured the two `Log file:` lines and the two
  file handlers come out in a **hash-dependent order** — observed flipping between
  runs of the *baseline* tree, so pre-existing. "Log text is frozen" is true only
  up to that permutation. PR-25's gate pins `PYTHONHASHSEED` and a fixed disk path
  so its comparison measures the code rather than the hash; the fix is one
  `sorted()`, but it is a log-text change and six other tools still have their own
  copy of the construct.
- **D2** — already recorded as entry 98 (`_common.py`'s per-family layout).
- **D3** — the shared `run_main` traceback frame. The reviewer confirms it is the
  **only** observable output change in the archives migration and that the
  addendum escalates it correctly.

## Rebuttals

None. Every Minor was accepted.

## Re-verification after the fixes

None of the round-2 fixes touched `src/pdsfile/`: they are the harness under
`/tmp`, the records, and the new deferred entry. Per §6.6 step 5 the full-data
record carries forward — it was generated at 20:41/20:43 against the last
`src/pdsfile/` change at 20:38:52, and its numbers are unchanged (ns 892 → 896,
`s` empty). The tool-run gate **was** re-run, because its harness changed, and
§5's table is from that run.
