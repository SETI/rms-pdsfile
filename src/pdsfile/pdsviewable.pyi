"""Type stubs for ``pdsfile.pdsviewable`` (see the module docstring there).

The implementation is unannotated (modernization ground rule 5); these stubs
declare the public surface frozen in ``tests/api/api_manifest.json``. Types are
derived from the implementation and its docstrings; where the truth is broader
than a single concrete type, the broader type is declared.
"""

# The manifest freezes `os`, `pdslogger` and `Image` as public attributes of
# this module, so the stubs re-export them. rms-pdslogger ships no py.typed
# marker, hence the suppression on its import.
import os as os
from collections.abc import Container, Iterable
from typing import Any

import pdslogger as pdslogger  # type: ignore[import-untyped]
from PIL import Image as Image

from pdsfile.pdsfile import PdsFile

# rms-pdslogger ships no py.typed marker, so a PdsLogger cannot be named here.
_PdsLogger = Any

REQUIRED_ICONS: dict[str, tuple[str, int]]
REQUIRED_SIZES: set[int]
# Keys: icon_type, (icon_type, is_open) or (icon_type, is_open, color).
ICON_SET_BY_TYPE: dict[str | tuple[str, bool] | tuple[str, bool, str], PdsViewSet]

class PdsViewable:
    abspath: str
    url: str
    width: int
    height: int
    bytes: int
    alt: str
    name: str
    pdsf: PdsFile | None
    width_over_height: float
    height_over_width: float
    def __init__(
        self,
        abspath: str,
        url: str,
        width: int,
        height: int,
        bytecount: int,
        alt: str = '',
        name: str = '',
        pdsf: PdsFile | None = None,
    ) -> None: ...
    def __repr__(self) -> str: ...
    def assign_name(self, name: str) -> None: ...
    def copy(self) -> PdsViewable: ...
    def to_dict(self, exclude: Container[str] = ...) -> dict[str, str | int]: ...
    @staticmethod
    def from_dict(d: dict[str, Any]) -> PdsViewable: ...
    @staticmethod
    def from_pdsfile(pdsf: PdsFile, name: str = '') -> PdsViewable: ...

class PdsViewSet:
    priority: int
    viewables: set[PdsViewable]
    by_width: dict[int, PdsViewable]
    by_height: dict[int, PdsViewable]
    by_name: dict[str, PdsViewable]
    widths: list[int]
    heights: list[int]
    def __init__(
        self,
        viewables: Iterable[PdsViewable] = ...,
        priority: int = 0,
        include_named_in_sizes: bool = False,
    ) -> None: ...
    def __bool__(self) -> bool: ...
    def __repr__(self) -> str: ...
    def append(
        self, viewable: PdsViewable | PdsViewSet, include_named_in_sizes: bool = False
    ) -> None: ...
    @staticmethod
    def from_dict(d: dict[str, Any]) -> PdsViewSet: ...
    def to_dict(self, exclude: Container[str] = ...) -> dict[str, Any]: ...
    def by_match(self, match: str) -> PdsViewable | None: ...
    @property
    def thumbnail(self) -> PdsViewable: ...
    @property
    def small(self) -> PdsViewable: ...
    @property
    def medium(self) -> PdsViewable: ...
    @property
    def full_size(self) -> PdsViewable: ...
    def __len__(self) -> int: ...
    def for_width(self, size: int) -> PdsViewable: ...
    def for_height(self, size: int) -> PdsViewable: ...
    def for_frame(self, width: int, height: int | None = None) -> PdsViewable: ...
    @staticmethod
    def from_pdsfiles(
        pdsfiles: PdsFile | list[PdsFile] | tuple[PdsFile, ...],
        validate: bool = False,
        full_is_special: bool = True,
    ) -> PdsViewSet | None: ...

def load_icons(
    path: str, url: str, color: str | None = 'blue', logger: _PdsLogger | None = None
) -> None: ...
def iconset_for(pdsfiles: PdsFile | list[PdsFile], is_open: bool = False) -> PdsViewSet: ...
