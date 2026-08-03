# PR-21 — adversarial review round 3

**Date:** 2026-07-27
**Reviewer:** a fresh, no-context opus-class subagent (§6.6), given the same
inputs as rounds 1 and 2 and no knowledge of either, plus the owner's 2026-07-27
ruling that absolute holdings paths in `plans/` and `critiques/` are not
confidential (so it would not spend the round on §3.4).
**Diff reviewed:** HEAD `ca25103` ("docs: record round 2, withdraw entry 57, and
rescope three figures"), 10 files, +2,522 / −525.
**Verdict:** **goal met** — 0 Major, 3 Minor, 0 new Deferred.

## What the reviewer re-derived independently

Both moved blocks byte-for-byte; all five §5 byte totals and all nine stay-list
counts; the name-loss comparison across seven modules plus `dir()` of all three
classes; the API dump on both trees; the whole §8 ratchet table, parent and head,
**with per-file-ignores disabled** so it measured the minimal code set rather than
the configured one; the nine import orders; the docstring contract (31 receivers,
4 PdsFile-side, 27 others, 25 of 25 names, zero residue either direction); the
statement counts; the banner-width table and the `:496–498` citation round 2 had
just corrected; the stub-`pylibmc` manifest diff (2 extra at base, 1 at head);
`_index_rows.py:254`'s sniff; and the two consumer repo commits. It **ran** ruff,
`pytest tests/api/`, the clean-install gate and the no-holdings job (82 / 800).

Its own summary of the outcome is worth quoting: "All three findings are wording
in a record, a sub-plan heading and the new class docstring; none is in the
extracted code, which for the fourth PR in a row is where this stack's defects
live."

## Major

**None.** The reviewer states it could not construct the "goal not met" case, and
records that it set out to raise the `pylibmc` name loss as a Major and could not
sustain it.

## Minor — all three accepted, all three fixed

Each was re-measured by the executor before being fixed, and each measurement
reproduced the finding. **Two of the three are in `src/`**, which is the first
time in this loop and which triggers §6.6 step 5's regeneration rule.

### Minor 1 — a heading asserted the opposite of its own table's last row, in two files

`critiques/phase5-validation.md` §5.3 and `plans/2026-07-27-pr-21-subplan.md` §5.2
were both headed "Six names are stranded in `pdsfile.py`, **and every one of them
stays bound**". The table directly beneath has six rows with `left = 0`, and the
sixth is `pylibmc`, whose disposition cell says "see §5.4" — and §5.4 is headed
"`pylibmc` — the one name this PR does **not** carry back". The body text and the
sub-plan's own commit table both say **five**; the heading was the outlier, and it
is the sentence a reader scanning the record takes away.

Re-measured: with a stub `pylibmc` on `PYTHONPATH`, `'pylibmc' in
vars(pdsfile.pdsfile)` is `True` at `2df25ab` and `False` at HEAD, so five of the
six stay bound and the sixth does not.

**Fixed** in both files: "Six names are stranded in `pdsfile.py`; five stay bound
and the sixth is §5.4" (§5.3 in the sub-plan's numbering).

### Minor 2 — the mixin docstring's "and nothing else" list omitted four receiver families and named one that does not occur

`src/pdsfile/_preload.py` read "…and nothing else -- str, list, dict, **set**,
os.path, pdscache, pdsviewable and logger methods are not in scope".

Re-measured with an AST walk over the mixin's five bodies — 31 distinct receiver
expressions — the list was wrong in both directions:

| | |
|---|---|
| named but never a receiver | `set` — `set(parts[2])` is a constructor call, not an attribute access |
| a receiver but not named | `os` itself (`os.listdir`), file objects (`f.readlines`), `pylibmc` (`pylibmc.Error`), `time` (`time.sleep`) — at HEAD `_preload.py:255`, `:266`, `:382` and `:387`; the fix that closed this finding added four lines above them, so the pre-fix numbers were four lower |

The validation record's own §15 already listed the measured families correctly, so
the docstring and the record disagreed and the docstring was the one that was
wrong — the same claim-versus-measurement class as round 2's Minor 3, one level
down.

**Fixed:** the enumeration now reads `str, list, dict, file, os, os.path,
pdscache, pdsviewable, pylibmc, time and logger`. Nothing below the colon changed:
the contract still verifies **25 of 25 in both directions**, re-run after the edit.

### Minor 3 — the docstring's memcached condition excluded the path deployment actually takes

The docstring said the MemcachedCache is chosen "when a non-zero **port is
supplied** and pylibmc imported", and repeated it lower down. The code is

```python
if (port == 0 and cls.MEMCACHE_PORT == 0) or not HAS_PYLIBMC:
```

so the memcached half also runs when **no** port is supplied but
`cls.MEMCACHE_PORT` is already non-zero — which is the normal state after any
earlier `preload(..., port=N)`, because the branch's first statement is
`cls.MEMCACHE_PORT = cls.MEMCACHE_PORT or port`, written onto the class. The
docstring's own contract table lists `MEMCACHE_PORT` as read **and written** two
paragraphs above, so the prose contradicted the table it sits under; and
rms-viewmaster, which the same paragraph names, preloads twice.

**Fixed:** both sentences now read "when pylibmc is importable and either the port
argument or the class's MEMCACHE_PORT is non-zero", and the second adds why the
second disjunct matters.

## Deferred

**None new.** The reviewer raised two, both already recorded:

1. **Entry 58** (`pylibmc`'s reachability) — it reproduced every measurement in
   the entry and agreed with the disposition. Its one suggestion was to annotate
   the exception in the code, at `pdsfile.py`'s re-export block, whose comment
   says the private names there "are carried so that no name reachable as
   `pdsfile.pdsfile.<name>` is lost". **Declined, with the reasoning recorded in
   entry 58** rather than acted on: the clause is a *purpose* statement scoped to
   the four private names the sentence introduces, none of which is `pylibmc`, not
   a global invariant over the module; and it is inherited wording, written by
   PR-16 and extended by PR-17, PR-20 and PR-21 only by adding names to its lists,
   so rewording its claim is a change to another PR's prose. Entry 58 now says so,
   and says the one-line edit is available to whichever PR next touches that block
   if the owner wants the exception visible in the source.
2. **Entry 60** (banner widths) — it re-measured the three-tree table and the
   `:496–498` citation round 2 had just corrected, confirmed both, and agreed the
   entry belongs to PR-23.

## What this round changed, and the regeneration it forced

Minor 2 and Minor 3 are edits to `src/pdsfile/_preload.py` — two paragraphs of the
class docstring, no executable line. By §6.6 step 5 that stales the full-data
record, so **the full-data run was regenerated** at `dd75796` before this round's
record was written:

| Head pair | `--junitxml` written | Tree at | `--mode ns` | `--mode s` |
|---|---|---|---|---|
| 1 | 22:08:52 / 22:10:41 | `a8f4cb3` | 848 / 34 | 555 / 3 |
| **2** | **23:37:21 / 23:39:10** | **`dd75796`** | **848 / 34** | **555 / 3** |

The set diff against the baseline is **empty in both modes** on the new pair, and
the diff between the two head pairs is **empty in both modes** too — which is what
a docstring-only change should produce and is measured rather than assumed.
Provenance re-checked on the new pair: 71 measured files, 0 outside the main
tree's prefix, 14 directly under `src/pdsfile/`. §9's and §12's statement figures
were re-derived on it and are unchanged (226 / 43 / 5 for the file; `preload` 113
/ 83 / 30), because a docstring is not a statement.
