##########################################################################################
# tests/core/support.py
#
# Helpers shared by the core-module tests. Nothing here touches a holdings tree.
##########################################################################################

from pdsfile import Pds3File, pdscache


class RecordingDictionaryCache(pdscache.DictionaryCache):
    """A real DictionaryCache that also records the keys written through set()."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_keys = []

    def set(self, key, value, lifetime=None):
        self.set_keys.append(key)
        return super().set(key, value, lifetime=lifetime)


def blank_pds3file(logical_path, html_root_='/holdings/'):
    """Return a blank Pds3File carrying only the fields the tests read.

    PdsFile's constructor is documented as returning a blank object, so the fields
    below are assigned the way the real parsing code would assign them. The logical
    paths the tests pass in name bundle sets that exist in no holdings tree, so such
    an object can never be mistaken for a real one.
    """

    pdsf = Pds3File()
    pdsf.logical_path = logical_path
    pdsf.abspath = '/nonexistent-holdings/' + logical_path
    pdsf.html_root_ = html_root_
    pdsf.basename = logical_path.rpartition('/')[2]
    return pdsf

##########################################################################################
