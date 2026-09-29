# PR-29 adversarial review, round 4 — `pdscache.py`, second read

Reviewer: a fresh subagent with no context from the executor's session or from rounds 1
to 3. Same slice as round 1 — `src/pdsfile/pdscache.py`, 3 classes and 60 functions — and
the first slice in this PR to be read twice.

## Why this round exists, and the framing it corrects

The executor reported rounds 1 to 3 (15, 11, 18 findings) as a non-converging *trend*.
That reading is wrong and the coordinator corrected it. Those three were independent
first passes over three *different* files, so nothing about them increases or decreases;
they are not successive samples of one surface.

The true and more serious statement is simpler: **every file had had exactly one
adversarial read, and each of those reads found roughly fifteen real defects in prose
written for this PR.** Nothing in that established what a *second* read of any file
returns. This round is the experiment that answers it.

`pdscache.py` was chosen for three reasons: round 1 was the least informed review,
because it ran before rounds 2 and 3 discovered where these docstrings drift; the file
holds the most consequential code defects (entries 23, 24, 157, 170); and round 1's own
findings showed the reviewer correcting *new* prose, not just cataloguing old bugs.

The reviewer was pointed at the three angles round 1 lacked: exceptions from operators,
subscripts and attribute access rather than from `raise`; arithmetic, rounding and
boundary claims; and any sentence asserting a **relationship between two things** — that
one method calls another, that one is safe because another checked, that a lifetime or a
limit behaves the same way in both cache classes.

## The answer: a second read does not return zero

**Ten ranked findings and eleven smaller ones — about twenty items, comparable to round
1's fifteen.** Every one was re-verified by the executor before acting on it, and every
re-verification agreed.

Split by kind, which is the distinction that matters for judging the PR:

| | count | what it means |
|---|---:|---|
| **Defects in the new prose** | 13 | a docstring written for this PR says something untrue |
| **Discoveries about the code** | 7 | a real defect the docstring was simply silent about |

The angle that paid best was the third. Of the 13 prose defects, **6 were relationship
claims** — a statement about how two methods interact, or about one class stated as
though true of both. That is the same shape as the one thing CodeRabbit found that all
three earlier rounds missed (`_recache`'s lifetime claim). It is now clear that this is
the systematic weak point of the prose, not a one-off.

## Findings

| # | finding | kind | fix |
|---:|---|---|---|
| 1 | `delete_multi` — "raises AttributeError **before touching the server**. Nothing on the server … is changed." Its first statement is `wait_for_unblock`, which reads the blocking key and, past `MAX_BLOCK_SECONDS`, writes it. Verified: with another process holding the block, the call recorded `get, get, set($OK_PID, 0)`, **broke that block**, and only then raised. | prose | rewritten; entry 194 |
| 2 | `replicate_clear_if_necessary` — "a clear can go unnoticed through any number of `set()` … calls." `set()` calls `flush()`, which calls this. Verified: with a value buffered and the shared counter bumped, `set('new', …)` returns **True** while the replication empties the buffer, so the value reaches neither the buffer nor the server. | prose | rewritten in three places; entry 192 |
| 3 | `MemcachedCache.get()` can raise `KeyError`: it returns `permanent_values[key]` after a restore that deletes from `permanent_values` when the server refuses the value as too large. Verified. | code | `Raises:` added; entry 193 |
| 4 | `_restore_permanent_to_cache` — documented as moving the value and *then* failing to log. The warn comes **first**, so with no logger neither the move nor the drop happens. The opposite ordering to `_wait_for_ok`, which the file gets right 950 lines earlier. | prose | rewritten; entry 195 |
| 5 | module docstring — lists `delete_multi()` as shared interface and calls `set_multi()` "the sharpest" difference. `delete_multi` **cannot execute at all** on one of the two classes, which is a far wider gap. | prose | rewritten as a ranked list of five divergences |
| 6 | `_trim` — "until exactly the limit remains" is false whenever the expiring entries are already at or below the limit, and unconditionally false at `limit=0`, where the slice is empty for any input. Verified: 500 entries, every trim discards nothing. | prose | rewritten; entry 197 |
| 7 | `int(x + 0.999)` is not "rounded up to a whole second": `1.0005 → 1`, and `0.0005 → 0`, which this file everywhere means *never expires*. | prose | rewritten in three places; entry 196 |
| 8 | the stale-key `KeyError` was documented without saying **who sees it**. Verified: `set()`, `set_multi()`, `__setitem__` and `resume()` raise; `get()`, `delete()` and `len()` do not. `resume()`'s "harmless" was exactly wrong. | prose | `Raises:` on three methods, `resume()` rewritten |
| 9 | a bound or class method is a lifetime *function* to `MemcachedCache` and a *constant* to `DictionaryCache` — and `_preload.py:369`/`:401` build a `DictionaryCache` with `lifetime=cls.cache_lifetime`, a classmethod. Verified: the first default-lifetime `set()` raises `TypeError`. | code | documented; entry 191 |
| 10 | eleven smaller items: `flush()` leaves already-written batches in the buffer; its log count subtracts keys from groups; `get()`/`get_now()` raise `TypeError` unpacking a non-pair, reachable for every bookkeeping key; a toobig key *is* still asked of the server by `get_now()` and `__len__`; `permanent_values` is filled at flush, not at store; `was_cleared()` propagates nothing; `len_mc`'s multi-server caveat describes a client the constructor cannot build; `__delitem__` raises for a key held only in `permanent_values`; `_trim` logs even when it discards nothing. | mixed | all rewritten; entries 196, 198 |

## A change to the checker this round forced

Findings 3 and 10 are exceptions raised by **subscripts and tuple unpacking**, not by
`raise` statements. (Finding 7 is about rounding, not about an exception, and is not part
of this.) Section 4.1 of the record had a convention that such exceptions go in
prose rather than in a `Raises:` section, because check E1 could not verify an attribution
to anything but a call — and round 4 shows that convention was wrong, since these are
exactly the failures a caller needs told about, and prose buries them.

So E1 was widened rather than the prose weakened. `called_names()` now also records tuple
unpacking, and an entry may attribute an exception to a mechanism the body demonstrably
contains: a call, item syntax, or unpacking. The attribution is still checked against the
AST, so naming a mechanism the body does not use still fails — verified by deleting the
attribution from `get_now`'s `TypeError` entry, which E1 then reports.

## Gates after the fixes

AST hash unchanged at `eccdfbc6d19a526d`; all five hashes unchanged. Docstring checker 0
findings over 11 files. Comments: 3 removed, 0 added, 0 moved. `ruff check .` clean,
`E111,E112,E113` clean, ratchet 2,249. Sphinx clean under `-W -n`. Citation checker 0
stale.

## What this says about PR-29a

One adversarial read per file is not enough for a docstring PR of this size. Round 4
found about as much on a second read as round 1 found on the first, and the largest
single category — claims about a *relationship* between two methods or two classes — is
one that a reader only becomes good at finding after seeing several. PR-29a covers 156
functions across ten modules and should not assume three passes will exhaust them.
