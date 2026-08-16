# PR-33a round 2 — full diff

Reviewer: a fresh, no-context subagent, new for this round, given the owner's four
instructions, the §2 ground rules, §6.1/§6.2, the §6.6 progressive-compliance
schedule, the exact diff `git diff feat/api-stubs..fix/archive-infoshelf-rebuild`
(11 files at `bdb227e`), and read access to the repository and the read-only
holdings roots. It made no edits and knew nothing of round 1's findings.

The reviewer independently reproduced the full evidence chain: the scratch
end-to-end script run with a stale seed (exit 0, seven products, seed replaced);
the deletion-shape necessity against the real category layout (files, no
directories) and the five `--initialize` refusals at their source lines; the
negative control (2 failed / 1 passed pre-fix from
`git show feat/api-stubs:...`, 3 passed at head) plus its own independent check
of the old six commands against the rule table (only the fifth rule was violated,
via the missing product — confirming the old prose's ordering complaint was
false); the diagram's 8 nodes and 7 edges one-to-one against
`pdsdependency.py:610-697`, an `mmdc` render, and the source-vs-built-HTML match;
all four PDS4 example commands against a scratch copy of the bundle set,
including the single linkshelf error with the PDF really beside the label; the
`BUNDLESET_PLUS_REGEX` rejection reproduced from both tools; the absence of a
`pds4dependency` console script; the full ns suite at head (1208/34); ruff, LF,
frozen files, no absolute holdings path; the §9/round-file correspondence; the
register arithmetic; and round 1's m5 rebuttal, which it judged sound and did not
re-raise.

Verdict: **goal met** — zero Major, two Minor, two Deferred (both already
observations 4062/4063).

## Minor findings, and their resolutions

**m1. A new unwrapped splice inside round 1's own fix** — the sentence added to
resolve round 1's m2 left a 116-character line at `user_guide_concepts.rst:241`,
the same defect class round 1's m1 named. The measured Phase 7 pattern (a
correction pass carries new defects at about half the rate of the pass it
corrects) holds on this PR too. **Fixed:** the paragraph is rewrapped; no prose
line in the section now exceeds the file's column discipline.

**m2. "In the order the dependency graph requires" overstates** —
`user_guide_shell_scripts.rst:106` claimed the graph *requires* the script's
sequence, against the concepts chapter's own thesis (and the truth) that the
constraint is a partial order with many valid linearizations. **Fixed:** the
sentence now reads "in an order the dependency graph in
:doc:`user_guide_concepts` permits", and the next sentence already identifies it
as the same sequence the chapter's PDS3 example shows.
