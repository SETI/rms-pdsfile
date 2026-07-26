# PR-13 — adversarial review round 4 (scoped)

- Base: `origin/rewrite` @ `8d5cf16b8e16b60bfbcf2615d8a9ae54faec703d`
- Head reviewed: `6b63a16bde8829f5eed6653c21002eb755423997`
- Reviewer: a **fourth** fresh no-context subagent.

Per §6.6's anti-thrash rule, the fourth round is a **scoped** re-review: confirm
the prior round's findings are resolved, and raise only **new Major** findings.
The reviewer was given round 3's five findings verbatim and that narrowed mandate,
and was told explicitly not to report Minor findings.

## Verdict

**goal met** — **zero new Major findings**. This closes the loop: four rounds, four
independent reviewers, `goal met` and zero Major every time.

## Job A — are round 3's findings resolved?

| Round-3 finding | Reviewer's call | Action |
|---|---|---|
| 3.1 stale "Five pre-existing defects" lead-in | **resolved** | — |
| 3.2 stale no-holdings count in three files | **resolved** (only surviving "794" is in `round-2.md`, correct as history) | — |
| 3.3 `sidecar_text` portability rationale | **partially resolved** — the false claim is gone and the load-bearing statement is now correct, but the replacement's parenthetical still mis-describes the *link* shelves, which emit list-valued entries before str-valued ones (each group sorted), not "sorted keys" or "table-row order". Goldens were never at risk; only the enumeration was wrong. | **Fixed**: the docstring now names all three orders explicitly. |
| 3.4 deviation register incomplete | **partially resolved** — the addendum is now complete and correct (four deviations, each with an "if rejected" note) and the sub-plan matches, but `critiques/pr-13/validation.md` still said "Two", contradicting the addendum it points at. | **Fixed**: the validation record now lists all four. |
| 3.5 archive test bypassing `check_golden` | **resolved** | — |

## Job B — new Major findings

**None.** The reviewer's independent verification at this head:

- 105 passed / 0 skipped against the goldens' reference root, **both in file order
  and in randomised order** — an independent confirmation of order-agnosticism.
- No-holdings run: 23 passed / 795 skipped, collection clean.
- API-freeze green; `ruff check` clean; no new `per-file-ignores` entry for any of
  the 15 new test files.
- **No file under `src/` in the diff at all**, so no tool behaviour, CLI surface,
  output, log format or exit code can have moved. None of the four prohibited
  files is touched. Every golden in the diff is new; no pre-existing golden or
  baseline record is edited.
- Traced the safety argument in the code rather than taking it on trust:
  `ToolTree.env` repoints both holdings variables into the temporary tree and
  strips `PDS_LOG_ROOT`, and a fresh subprocess has no preload and no
  `LOCAL_HOLDINGS_DIRS`, so `PDS3_HOLDINGS_DIR` wins and no `--repair` can reach
  real holdings.
- Confidentiality: the full diff contains neither root's absolute prefix, and no
  golden contains an absolute path.
- Every spec deliverable present, including the three pds4 tools that cannot
  complete a task cycle today being **pinned rather than skipped**, with their
  defects recorded as entries 1–4 of the deferred observations.

## Loop termination

Round 4 raised zero Major findings under its scoped mandate, and no rebutted
finding was ever re-raised (nothing was rebutted — all 27 Minor findings across
rounds 1–3 were accepted and fixed). The §6.6 loop is complete and the PR may be
opened.
