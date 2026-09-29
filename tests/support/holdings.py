##########################################################################################
# tests/support/holdings.py
#
# Resolve which holdings tree the test session runs against, so that
# tests/conftest.py and the per-dataset helper modules agree on a single answer.
#
# Selection is driven by PDSFILE_TEST_HOLDINGS:
#   full  -> roots from PDS3_HOLDINGS_DIR / PDS4_HOLDINGS_DIR (error if unset).
#   mini  -> roots $PDSFILE_TEST_DATA_DIR/holdings and .../pds4-holdings (error
#            if PDSFILE_TEST_DATA_DIR is unset or those trees are missing).
#   unset -> mini when PDSFILE_TEST_DATA_DIR resolves to real trees, otherwise no
#            holdings are available and every data-dependent test is skipped.
#
# An explicit but broken selection (full/mini) raises loudly. The unset-and-
# nothing-available case never raises: importing the test modules and collecting
# the suite must succeed even with no holdings present.
##########################################################################################

import os

SKIP_REASON = 'no holdings available (set PDSFILE_TEST_HOLDINGS)'

# Placeholder roots used only when no holdings are available. Every data-dependent
# test is skipped in that case, so these paths are never dereferenced; they exist
# so that module-scope path expressions in the test modules (slicing on
# 'holdings'/'pdsdata', f-string joins) do not raise at import time.
_PLACEHOLDER_PDS3 = os.path.join(os.sep, 'pdsfile-no-holdings', 'pdsdata', 'holdings')
_PLACEHOLDER_PDS4 = os.path.join(os.sep, 'pdsfile-no-holdings', 'pdsdata', 'pds4-holdings')


class HoldingsConfig:
    """The resolved holdings selection for a test session.

    Attributes:
        flavor: 'full', 'mini', or None when no holdings are available.
        pds3_root: Absolute path to the PDS3 holdings tree.
        pds4_root: Absolute path to the PDS4 holdings tree.

    ``pds3_root`` / ``pds4_root`` are always non-None strings. When ``flavor`` is
    None they are unreachable placeholders (data-dependent tests are skipped).
    """

    def __init__(self, flavor, pds3_root, pds4_root):
        self.flavor = flavor
        self.pds3_root = pds3_root
        self.pds4_root = pds4_root

    @property
    def available(self):
        """True when a real holdings tree was resolved (flavor is 'full' or 'mini')."""
        return self.flavor is not None


def _skip_config():
    return HoldingsConfig(None, _PLACEHOLDER_PDS3, _PLACEHOLDER_PDS4)


def _resolve_full():
    pds3 = os.environ.get('PDS3_HOLDINGS_DIR')
    pds4 = os.environ.get('PDS4_HOLDINGS_DIR')
    missing = [name for name, value in
               (('PDS3_HOLDINGS_DIR', pds3), ('PDS4_HOLDINGS_DIR', pds4)) if not value]
    if missing:
        raise RuntimeError(
            "PDSFILE_TEST_HOLDINGS=full requires " + ' and '.join(missing) + " to be set")
    invalid = [path for path in (pds3, pds4) if not os.path.isdir(path)]
    if invalid:
        raise RuntimeError(
            "PDSFILE_TEST_HOLDINGS=full: missing holdings tree(s): " + ', '.join(invalid))
    return HoldingsConfig('full', pds3, pds4)


def _resolve_mini(explicit):
    """Resolve the mini fixtures. When ``explicit`` (PDSFILE_TEST_HOLDINGS=mini) a
    missing dir or tree raises; otherwise (the unset default) it falls back to the
    no-holdings skip config so collection still succeeds."""
    data_dir = os.environ.get('PDSFILE_TEST_DATA_DIR')
    if not data_dir:
        if explicit:
            raise RuntimeError(
                "PDSFILE_TEST_HOLDINGS=mini requires PDSFILE_TEST_DATA_DIR to be set")
        return _skip_config()

    pds3 = os.path.join(data_dir, 'holdings')
    pds4 = os.path.join(data_dir, 'pds4-holdings')
    missing = [path for path in (pds3, pds4) if not os.path.isdir(path)]
    if missing:
        if explicit:
            raise RuntimeError(
                "PDSFILE_TEST_HOLDINGS=mini: missing holdings tree(s): "
                + ', '.join(missing))
        return _skip_config()

    return HoldingsConfig('mini', pds3, pds4)


def resolve_holdings():
    """Return the HoldingsConfig for this session (see module docstring)."""
    requested = os.environ.get('PDSFILE_TEST_HOLDINGS')

    if requested == 'full':
        return _resolve_full()
    if requested == 'mini':
        return _resolve_mini(explicit=True)
    if requested:
        raise RuntimeError(
            "PDSFILE_TEST_HOLDINGS must be 'full' or 'mini' "
            f"(got {requested!r})")

    # Unset: prefer the mini fixtures when PDSFILE_TEST_DATA_DIR resolves to real
    # trees; otherwise no holdings are available and collection stays green with
    # every data-dependent test skipped.
    if os.environ.get('PDSFILE_TEST_DATA_DIR'):
        return _resolve_mini(explicit=False)
    return _skip_config()
