# PR-13 — adversarial review round 6 (scoped confirmation)

- Focus diff: `git diff 3fab1ed..HEAD` — the fixes for round 5's findings.
- Head reviewed: `1417291`
- Reviewer: a **sixth** fresh no-context subagent, given round 5's six findings
  verbatim and a two-job mandate: confirm each is resolved, and raise only new
  **Major** findings.

## Verdict

**goal met** — **zero new Major findings**. Round 5's two Major findings are
resolved and were confirmed by running, not by reading.

## Job A — round 5's findings

| # | Finding | Reviewer's call |
|---|---|---|
| 5.1 (Major) | Duplicate registry entry number 12 | **Resolved.** The CI entry is 14, the lead-in says explicitly that 12-13 are process observations, and both citations follow. The reviewer extracted every list marker in the registry (no duplicates remain) and additionally confirmed that the two by-number citations in the deviation addendum still resolve to their intended entries. |
| 5.2 (Major) | `unordered=True` unpinned 18 lines to absorb instability in 6 | **Resolved**, and verified three ways by running: forcing the tool's enumeration ascending vs descending reproduces exactly the claimed 12/6 split; the module and the whole suite pass under a forced-descending enumeration (111 passed, harness confirmed active in 222 tool subprocesses); and with a harness that swaps two *stable* steps the test **fails**, while swapping two `.tab` steps still passes. "The load-bearing order is genuinely pinned and the genuinely unstable order genuinely tolerated." |
| 5.3 (Minor) | `validation.md` cited a `round-5.md` that did not exist, verdict pre-declared | **Partially resolved — the same defect re-committed one round forward.** `round-5.md` now exists with an honest verdict, but the row had been rewritten to say "round 6 confirmed. See `round-1.md` … `round-6.md`" before this review had run. Fixed properly this time: `round-6.md` is this file, written from the review's actual outcome, and the row now describes what happened rather than what was expected. |
| 5.4 (Minor) | Wrong mechanism ("different rules") | **Resolved.** No such wording survives outside round-5.md's own restatement of the finding. The reviewer checked the corrected mechanism against the tool: the checksums+infoshelf pair is one rule's two-message list and the archive triple another, both single-path globs, while the six moving steps come from the multi-match metadata and cumulative rules. |
| 5.5 (Minor) | `return pytest.fail(...)` | **Resolved.** |
| 5.6 (Minor) | `''.join(sorted(lines))` not injective on multisets | **Resolved** — `check_golden` compares line lists. The reviewer noted a side effect and judged it harmless: the ordered path now also goes through `splitlines()`, so a trailing-newline or line-ending difference no longer fails a golden. Every golden's text is reconstructed line-by-line by a normalizer with `\n` terminators, and `.gitattributes` normalizes committed text to LF, so nothing previously pinned is now unpinned. Recorded rather than changed. |

## Job B — new Major findings

**None.**

Gates the reviewer ran at this head: `ruff check` clean; API-freeze 1 passed;
clean-install passed; `--mode ns` 790 passed / 34 skipped (= baseline 679 + 111);
`--mode s` 555 passed / 3 skipped, identical to baseline; no-holdings run 23
passed / 801 skipped. The whole-PR diff touches no file under `src/` and none of
the four prohibited files; the ruff `per-file-ignores` block is untouched; no
golden changed in the follow-up; no `xfail` or test-level skip was added.

## Loop status

Six rounds total: 1-4 before the PR was opened (all `goal met`, zero Major),
round 5 after the CI failure (`goal not met`, 2 Major, both fixed), round 6
confirming (`goal met`, zero Major). Nothing was ever rebutted except CodeRabbit's
markdownlint finding, whose rebuttal is recorded in `ci-and-coderabbit.md`.
