# PR-29b review round 1 — the ten `_properties.py` docstrings of the line-count sample

Fresh reviewer subagent, no context from this session or any other round. Brief: the ten
members `exists`, `is_documents`, `extension`, `html_path`, `_info`, `mime_type`,
`version_ranks`, `label_basename`, `label_abspath` and `version_info`, with the five angles
named in order and the instruction to run a claim rather than reason about it wherever
holdings data can settle it. Real holdings were mounted and the reviewer used them.

**Twenty-one findings over ten docstrings, and eight discoveries about the code.** Every
finding was re-verified by the executor before it was acted on. None was rejected.

## The findings, in file order

| # | member | severity | what was wrong |
|---|---|---|---|
| 1 | `exists` | incomplete | the SHELVES_ONLY claim omitted that the documents tree is excluded, because no shelves are written for it |
| 2 | `exists` | wrong | "memoizes its answer for the life of the process" -- it is an LRU of `PATH_EXISTS_CACHE_SIZE` (200) entries, and an evicted answer is recomputed and can change |
| 3 | `extension` | wrong | attributed the bundle-set behavior to "the bundle-set rules"; a bundle-set name is matched by the regular expression **before** the split rules are consulted, and the rules never see it |
| 4 | `extension` | incomplete | on a class with no split rules the subscript indexes a string, so a basename shorter than three characters raises IndexError; there was no `Raises:` |
| 5 | `extension` | wrong | `Returns: str: the extension, with its leading period` contradicted the same docstring's own three counter-examples |
| 6 | `html_path` | wrong | "starting with the HTML root" -- a `.link` file's value is the file's contents, which is a complete external URL, scheme and host included |
| 7 | `html_path` | incomplete | "which is a merged directory" is an apposition the code does not support: a child of a merged category directory reaches the same branch with `is_merged` False, and fails with TypeError rather than IndexError |
| 8 | `_info` | wrong | named `checksum` among the properties that read it; `checksum` reads the volume-info table's MD5 first, which is what the documents tree carries. And `width`/`height` **do** reach the filesystem, through `_repair_width_height()` |
| 9 | `_info` | wrong | "derived once ... and returned unchanged afterwards" -- `_repair_width_height()` rewrites the fifth element in place when `width` or `height` is read on a viewable the shelves did not measure |
| 10 | `_info` | wrong | "which is what makes the seven properties above safe to read on any object" -- on a checksums bundle-set directory all five reading properties raise ValueError, with SHELVES_REQUIRED at its default False |
| 11 | `_info` | incomplete | `Returns: tuple:` where the same docstring says four lines earlier that a merged directory and an index row hold a **list** |
| 12 | `_info` | wrong | attributed ValueError to the SHELVES_REQUIRED re-raise alone; the bundle-set loop's handler catches OSError only, so a ValueError from `shelf_lookup()` escapes unconditionally |
| 13 | `_info` | incomplete | `shelf_lookup()` can also raise SyntaxError and NameError from the readable sidecar, and neither handler here catches either |
| 14 | `mime_type` | incomplete | the side-effect list named `_split_filled` and omitted `_isdir_filled` |
| 15 | `mime_type` | incomplete | the `isdir` test raises KeyError under SHELVES_ONLY for a path the shelf covers and holds no entry for -- where `exists` would have answered False |
| 16 | `mime_type` | wrong | "the extension without its leading period" -- the slice drops the first character whatever it is, so a bundle-set name's `_previews` is looked up as `previews` |
| 17 | `mime_type` | unverifiable | the claim about what callers read an empty string as is about consumers outside this repository; nothing here can settle it |
| 18 | `version_ranks` | incomplete | "derived once ... returned unchanged afterwards" is exactly the property the None case does not have: the slot stays None, so the whole body reruns on every access |
| 19 | `label_basename` | incomplete | named its own slot and none of the four others its body fills, and had no `Raises:` for the link-shelf re-raise |
| 20 | `label_abspath` | incomplete | "the one case where it does not" -- there is a second route, a name the link shelf recorded in another directory of the bundle, which nothing tests before it is rebuilt beside this file |
| 21 | `version_info` | incomplete | "compared with any other of its own bundle set by rank alone" holds only while the minor and micro numbers stay below 100; `_v1.100` and `_v2` both rank 20000 |

Findings 2, 3, 5, 6, 8, 9, 10, 12 and 16 are the ones a reader would have acted on and been
wrong. Four of them (8, 9, 10, 12) are in one docstring, `_info`, which is the largest body
in the file.

Two of the twenty-one were fixed by moving a `Raises:` entry to prose rather than by
rewriting the claim: `mime_type`'s KeyError and `label_basename`'s three both arrive through
a **property** read, which the checker's E1 cannot attribute to any mechanism it can see in
the AST. That is PR-29's stated convention -- an exception E1 can verify gets an entry, and
one it cannot goes in the body of the docstring -- applied rather than reinvented.

## Discoveries about the code, not about the prose

1. The worked example in `version_info`'s own code comment is arithmetically wrong:
   `_v2.1 -> 201000` and `_v2.1.3 -> 201030` against a measured 20100 and 20103. Only the
   first line of the three is right.
2. `_info` raises ValueError on every checksums bundle-set directory, which is a real
   browsable path, with default settings.
3. The bundle-set size sum contributes the bundle-set directory's own inode size, once per
   bundle whose sidecar is missing, rather than the bundle's size.
4. `_repair_width_height` mutates a slot the rest of the module treats as write-once.
5. `os_path_isdir` raises KeyError where `os_path_exists` returns False, for the same path
   under SHELVES_ONLY, and every property that tests `isdir` inherits it.
6. Bundle-set checksum tables get no MIME type, because their `extension` is a volume type.
7. `version_info` accepts a negative version part: `_v-1` ranks -10000 with no exception.
8. `child()` on a merged category directory can return a non-merged object with a None
   absolute path, whose `childnames` raises TypeError.

Items 1, 2, 3, 4 and 7 are carried as deferred observations; 5, 6 and 8 are documented in
the docstrings that reach them.

## What the reviewer checked hard and found correct

Recorded so the next round does not repeat it. Every "born with the slot pre-set" claim in
the ten was checked by name against `new_merged_dir()` and `new_index_row_pdsfile()` and
confirmed at runtime -- no slot was claimed that is not pre-set, and no pre-set slot was
forgotten. Deferred entry 68's `version_ranks` returning None was reproduced.
`label_basename`'s empty-stem case, which is the `basename[:-0]` gotcha, was reproduced. The
whole of `version_info`'s suffix table was run, including the fourth part being dropped from
the rank and the id while staying in the message. `_info`'s shelf branch was traced in full:
the fixed offsets do land microseconds in the right argument, an empty time string does
become None, a dashed checksum does become empty, and the fall-through-unless-SHELVES_REQUIRED
control flow is exactly as written.
