# PR-33a round 3 — scoped: the round-1 and round-2 correction passages, clause by clause

Reviewer: a fresh, no-context subagent, new for this round, told only that two
full-diff rounds had returned zero Major and that their corrections needed a
clause-by-clause read (the measured Phase 7 pattern: a correction pass introduces
new defects at about half the rate of the pass it corrects). Scope: the four
correction sites — the concepts paragraph after the PDS4 example, the rewrapped
graph paragraph, the shell-scripts "permits" sentence and its neighbors, the
reworked test with its pinned product set — plus the records, plus any new Major
anywhere in the diff. It made no edits.

What it reproduced: the `pds4linkshelf` run on a scratch copy of the bundle set
(exit 1 **and** both shelf files written — the sentence's two central clauses);
the single error's exactness against the real `document/` tree (the PDF really
beside the label); the pds4linkshelf page's own account of that error and of the
exit status; the index-shelf path form against the pds4indexshelf page and the
real tree; the link-shelf coverage (exactly three `_linkshelf-*` directories in
the real PDS3 tree, the rule loop at `pdsdependency.py:656-665`,
`_linkshelf-bundles` written by its own run); the chain-independence claim
against the rule table; the script sequence's command-by-command identity with
the concepts example; the five `--initialize` refusals at their source lines; the
pinned set against the script and the real layout; **the negative control the
round-1 correction claims to enable** — with a deletion and its rebuild dropped
symmetrically from a scratch copy, the set test now fails where the old two-way
comparison would have passed; the negative-control table (2 failed / 1 passed
pre-fix, 3 passed at head); the ns suite (1208/34); both Sphinx builds (0 problem
lines, 78/78); and the line discipline of every touched prose line.

Verdict: **goal met** — zero Major, one Minor, no new Deferred.

## The Minor finding, and its resolution

**m1. round-2.md misstated its own input: "11 files at `bdb227e`" — the diff is
10 files.** Introduced by the round-2 correction commit, the measured pattern
landing in the record rather than the code; it misstates the round's input, not
its findings. **Fixed:** the count now reads 10, re-measured with
`git diff feat/api-stubs..bdb227e --name-only | wc -l`.
