# Observations

Open observations from the modernization review rounds, renumbered and split by priority. Resolved and withdrawn observations are not carried over. Each observation appears in exactly one file.

| File | Contents | Observations | Numbers |
|---|---|---:|---|
| [observations-scheduled.md](observations-scheduled.md) | Owned by a remaining PR | 10 | 1000–1503 |
| [observations-p1.md](observations-p1.md) | Blocks the merge | 0 | — |
| [observations-p2.md](observations-p2.md) | Before the merge | 15 | 3000–3401 |
| [observations-p3.md](observations-p3.md) | After the merge | 133 | 3999–4406 |
| [observations-p4.md](observations-p4.md) | No action | 52 | 6000–6616 |

**210 open observations.** The source record held 375: 364 numbered entries plus 11 unnumbered bullets. 28 were resolved or withdrawn and are not carried over; the remaining 347 were combined into 228 by 51 merge groups that gather duplicates and same-subject clusters, one `MemcachedCache` observation replacing sixteen and one `re_validate` observation replacing five; and 27 have since been closed by the work and the owner rulings that followed, entry 1100 by the developer guide enabling `sphinxcontrib.mermaid`, entries 1200 and 1201 by the README rewrite, entry 4063 by narrowing the checksum deletion in the same script fix whose measurements found it, entries 3004 and 4033 by the owner-directed removal of `shelf_consistency_check`, whose capability gap issue #156 now tracks, and entries 3402, 4062 and 4064 by the owner's 2026-08-16 four-item ruling (`plans/2026-08-16-addendum-owner-four-items.md`): the Python-floor corrections, the widened `BUNDLESET_PLUS_REGEX` that lets the PDS4 archive checksum and info shelf be built, and the copy/setup scripts' `exit 1` guards. 375 - 28 resolved - 119 absorbed by merging - 27 since closed + 9 found during the later work (one while fixing entries, two by PR-33's reviews, three by PR-34's measurements and reviews, three by the `update_holdings_for_new_metadata.sh` fix's measurements and reviews) = 210. PR-35's two scheduled entries (1300, 1301) were not closed but re-homed: the stubs declare the names as they are, and the removal question moved to the post-merge file as entries 4127 and 4128, so the total is unchanged.

Number blocks: 1000s scheduled work, grouped by owning PR; 2000s blocking; 3000s before the merge; 4000s after the merge; 6000s no action. Within each priority, observations are grouped by category on hundred boundaries, leaving room for later additions.
