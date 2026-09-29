# PR-02 adversarial review — round 1

Fresh, no-context Opus reviewer given the PR-02 deliverables, ground rules, §6.1,
the diff (`git diff rewrite..HEAD`), and read access to the repo + holdings.
Mandate: assume the goal was not met and try to prove it.

## Verdict: goal met (0 Major, 2 Minor, 3 Deferred)

The reviewer ran the dumper/checker directly and confirmed: byte-reproducibility
(incl. across `PYTHONHASHSEED`, CWD), process-state independence (0 diffs after
importing the tests helpers + running `preload()`; the exclusion filter is
load-bearing), the module set matches the spec exactly (43 modules = 7 + 26 + 10),
rule subclasses + inherited surface captured (COISS_xxxx = 259 members, class
de-dup correct), the un-hand-filtered Phase-0 snapshot matches the plan's
heads-up, and the checker detects removed/kind-changed/signature-changed members
with non-overbroad forgiveness. `consumer_used_private_names.json` is genuinely
consumed for module-level names.

## Minor findings and disposition (both FIXED — documentation only)

1. **Private-name override is module-scoped, not class-member scoped**
   (`scripts/dump_public_api.py`, class-member loop). Correct observation: the
   override forgives module-level underscore names (which a consumer *imports*),
   not class internals. No current consumer needs a private class member; the
   file is seeded empty. **Fix:** added a code comment at the class-member loop
   explaining the override is intentionally module-scoped, so a future
   maintainer isn't surprised. (No behavior change; manifest byte-identical.)

2. **Allowlist `"module"` field doubles as the class key for class-member
   diffs** (`tests/api/manifest_allowlist.json` `_comment`). Functional but
   under-documented. **Fix:** expanded the allowlist `_comment` to state that
   `"module"` holds the diff location — the module name for module attributes or
   the class key (e.g. `pdsfile.pds3file.Pds3File`) for class members — and that
   category patterns match `"<location>::<name>"`. (Comment key ignored by the
   checker; no behavior change.)

## Deferred (out of scope for PR-02; logged, not blocking)

- The freeze is defeatable by editing the manifest/dumper/test — inherent to
  this contract style; explicitly prohibited in both docstrings, the allowlist
  `_comment`, and plan §6.4. A process control, not a technical gap.
- `test_api_freeze.py` collection currently needs holdings env vars because the
  root `conftest.py` imports the tests helpers and preloads — resolved by PR-09
  (already documented in the test docstring).
- `_is_forgiven` does not guard against `KeyError`/`re.error` on a malformed
  future allowlist entry; harmless while seeded empty and fail-safe (raises
  rather than mis-forgives).

Appended to `critiques/deferred-observations.md`.

## Convergence

The sole findings were two non-blocking documentation Minors on an already
"goal met" verdict; both resolved by comment-only edits that leave the manifest
byte-identical and the test green. A scoped confirmation round follows
(round-2).
