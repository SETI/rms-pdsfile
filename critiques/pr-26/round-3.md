# PR-26 adversarial review — round 3

One fresh no-context auditor, pointed at something rounds 1 and 2 explicitly did
**not** cover. Both round-2 reviewers said in as many words that they had not
checked the full-data id maps, the ratchet figures or the four-tool transcript —
so the numbers in `critiques/pr-26-validation.md` had been read by nobody but
their author. This round audited the numbers themselves: not "is the code right"
but "does each claimed measurement reproduce".

The auditor was told to assume the numbers might be wrong, to re-run everything
itself, and to show raw output. It was warned about the two measurement traps
(deferred 110 and 121) so that a mis-measured "base" could not silently pass.

## Verdicts

| Claim | Verdict |
|---|---|
| Ratchet: 69/185/2,280 base → 69/184/2,271 head; per-entry table; new modules carry no entry | **TRUE**, every part |
| Full-data base counts, and `--mode s` identical at both | **TRUE** |
| **Zero outcome changes among shared ids, both modes**; 2 ids removed | **TRUE** |
| `run-all-checks.sh -c -s`: 264/812 head, 250/804 base | **TRUE** |
| `tests/api` 26 passed; four frozen files byte-identical | **TRUE** |
| The nine tests that fail at base and pass at head | **TRUE**, exact set match, no others |
| `--mode ns` head counts and "22 ids added" | **stale** → 1,076 / 1,042 / 24 |
| Post-split line counts 339/241/529 | **stale** → 337/242/533 |
| "1,081 is reconstructible from git history" | **Not reconstructible** — never committed |
| The 9-line reconstruction gap is the round-2 fixes | **FALSE** |

Every load-bearing claim held. The four defects were all in the same category:
**sections not re-measured after a later commit moved the tree.** Two of them I
had already caught and corrected while the audit was running, to precisely the
values it measured independently — which is itself a useful signal, since two
parties arriving at 337/242/533 and 1,076/1,042/24 separately is better evidence
than either alone.

## The one the audit found that I had not

§5 explained the 9-line gap between the pre-split measurement (1,081) and the
reconstruction from head (1,072) as the round-2 fixes. Wrong in both magnitude and
direction: round 2 is a net **+3** lines across the three modules, so backing it
out moves the reconstruction to 1,069 and *widens* the gap to 12.

The real cause is the split itself. Base's `_common.py` carried two inner section
banners — `# Archive tools` and `# Checksum and shelf file tools`, three lines
each plus the blank after — and the split removed both, each new module's own
header taking over the role. The reconstruction subtracts those headers as part of
each module's preamble, so the eight lines never come back; the ninth is a blank
line normalized around the function that moved to `_archives_common.py`.

That is a small number in a paragraph nobody would have re-derived, and it was
wrong because I reached for the most recent change as the explanation instead of
measuring. Corrected, with the arithmetic shown.

## Also corrected

§6 said eight new holdings-dependent tests skip; there are **ten**, and +8 is the
net after the two removed ids. The section now gives the id-set diff (2 removed,
24 added, zero outcome changes) rather than a net figure presented as a gross one.

## What the round confirms about the method

The audit reproduced the base measurements by running pytest **from** a base tree
— `git archive 56b8823` into scratch with the head's test files copied in — and
verified that `support.REPO_ROOT` resolved to the probe tree, so tool subprocesses
got base source. It reports observing 1,054 collected ids at base against 1,076 at
head, and nine base-only failures, as its own evidence that the two trees were
genuinely distinct rather than silently sharing head code.

That is the form deferred 121 says is now the only reliable one, applied by
someone who was told about the trap rather than discovering it the hard way. It
worked.
