################################################################################
# pdsviewable.py
################################################################################

"""Images that can be displayed on a web page, and the icons that stand in for files.

Three things live here:

  * ``PdsViewable`` -- one image. It records where the image is on disk, the URL that
    serves it, its width and height in pixels, its size in bytes, its alt text, and an
    optional name.
  * ``PdsViewSet`` -- a group of ``PdsViewable`` objects showing the same subject at
    different sizes. A caller asks for the member that suits a width, a height or a
    bounding box, or for one by name.
  * ``ICON_SET_BY_TYPE`` -- a dictionary of icon sets, filled by ``load_icons()`` and
    read by ``iconset_for()``. A file that cannot be displayed directly is represented
    on a page by the icon set matching its icon type.

Sizes are in pixels throughout and byte counts are in bytes. A ``PdsViewable`` returned
by a size lookup is a scaled copy rather than a member of the set: the dimension asked
for is exactly what was asked for, and the other is derived from it, so neither describes
any file on disk. Its ``abspath`` and ``url`` still name the file that was chosen, which
is the one whose stored size is the smallest that is at least as large as the request, or
the largest stored size when every one of them is smaller.

``REQUIRED_ICONS`` maps an icon file's basename to the icon type it supplies and that
type's priority. When one icon has to stand for several grouped files, the highest
priority wins, which is what keeps a generic label icon from displacing a specific one.
``REQUIRED_SIZES`` is the set of icon widths a complete icon directory provides.
"""

import os

# `pdslogger` is not referenced below; it is re-exported for callers that reach
# it as pdsfile.pdsviewable.pdslogger. The redundant `as` alias is the explicit
# re-export form.
import pdslogger as pdslogger
from PIL import Image

################################################################################
# Class definitions
################################################################################

class PdsViewable:
    """One displayable image, described by everything an HTML page needs to show it.

    An instance is a description, not an open image: nothing here reads or holds pixel
    data. The attributes are ``abspath``, ``url``, ``width``, ``height``, ``bytes``,
    ``alt``, ``name`` and ``pdsf``, plus the two aspect ratios ``width_over_height`` and
    ``height_over_width``.

    The two ratios are computed once, at construction. A scaled copy from a
    ``PdsViewSet`` size lookup has new width and height but keeps the ratios of the
    image it was copied from, so on a copy they describe the source image rather than
    the copy's own dimensions.
    """

    def __init__(self, abspath, url, width, height, bytecount, alt='',
                       name='', pdsf=None):
        """Construct a viewable from the location and dimensions of one image.

        A width or height of zero raises ZeroDivisionError, because the aspect ratios
        are computed here.

        Parameters:
            abspath (str): absolute path to the image file.
            url (str): URL at which the image is served.
            width (int): width of the image in pixels.
            height (int): height of the image in pixels.
            bytecount (int): size of the image file in bytes. It is stored under the
                attribute name ``bytes``.
            alt (str): alt text for the HTML tag.
            name (str): optional name. A named viewable can be looked up by name in a
                ``PdsViewSet``, and by default is excluded from that set's lookups by
                size.
            pdsf: optional ``PdsFile`` for the image file, carried for the caller's
                convenience and not used here.
        """

        # Core properties of a viewable
        self.abspath = abspath
        self.url = url
        self.width = width
        self.height = height
        self.bytes = bytecount
        self.alt = alt

        # Optional
        self.name = name    # Named viewables cannot be looked up by size
        self.pdsf = pdsf    # Optional

        self.width_over_height = float(self.width) / float(self.height)
        self.height_over_width = float(self.height) / float(self.width)

    def __repr__(self):
        """Return the object's printable form, which quotes its absolute path.

        Returns:
            str: the text ``PdsViewable("<abspath>")``.
        """

        return 'PdsViewable("' + self.abspath + '")'

    def assign_name(self, name):
        """Give this viewable a name, replacing any name it already had.

        The name is used as a lookup key by ``PdsViewSet``. Renaming a viewable that a
        set already holds does not re-index it, so the set continues to answer to the
        name the viewable had when it was appended.

        Parameters:
            name (str): the new name.
        """

        self.name = name

    def copy(self):
        """Return a separate viewable carrying all the same values.

        The eight stored attributes are passed on, including the name and the
        ``PdsFile``, which is shared rather than duplicated. The two aspect ratios are
        not: they are recomputed from the copied width and height. On an ordinary
        viewable that makes no difference, but copying a scaled copy replaces the source
        image's ratios with the scaled copy's own.

        Returns:
            PdsViewable: the copy.
        """

        return PdsViewable(self.abspath, self.url, self.width, self.height,
                           self.bytes, self.alt, self.name, self.pdsf)

    def to_dict(self, exclude=[]):
        """Return this viewable as a dictionary of JSON-compatible values.

        The width, height and byte count are always present. The absolute path, the URL
        and the alt text are present unless their attribute names appear in ``exclude``.
        The name is present only when it is not empty, whatever ``exclude`` says. The
        ``PdsFile`` is never included, so a viewable rebuilt from this dictionary has
        none.

        Parameters:
            exclude: names of the optional attributes to leave out, as a container that
                supports the ``in`` test. The names it can carry are ``'abspath'``,
                ``'url'`` and ``'alt'``.

        Returns:
            dict: the attribute values, keyed by attribute name. The byte count is
            therefore keyed ``'bytes'``, not by the constructor's name for it.
        """

        d = {'width':  self.width,
             'height': self.height,
             'bytes':  self.bytes}

        # Include optional parts optionally
        if 'abspath' not in exclude:
            d['abspath'] = self.abspath

        if 'url' not in exclude:
            d['url'] = self.url

        if 'alt' not in exclude:
            d['alt'] = self.alt

        if self.name:
            d['name'] = self.name

        return d

    @staticmethod
    def from_dict(d):
        """Construct a viewable from a dictionary in the form ``to_dict()`` produces.

        The width, height and byte count are required; a dictionary missing any of them
        raises KeyError. The absolute path, URL and name default to the empty string.
        The alt text defaults to the basename of the absolute path, or of the URL when
        there is no absolute path. The reconstructed viewable has no ``PdsFile``.

        Parameters:
            d (dict): the values, keyed as ``to_dict()`` keys them.

        Returns:
            PdsViewable: the reconstructed viewable.
        """

        abspath = d.get('abspath', '')
        url     = d.get('url',  '')
        alt     = d.get('alt',  os.path.basename(abspath or url))
        name    = d.get('name', '')

        return PdsViewable(abspath, url, d['width'], d['height'], d['bytes'],
                           alt, name)

    @staticmethod
    def from_pdsfile(pdsf, name=''):
        """Construct a viewable from a ``PdsFile`` that names a displayable image.

        The dimensions, byte count and URL are taken from the ``PdsFile``, and the alt
        text is the basename of its logical path. The ``PdsFile`` is retained on the
        result.

        Parameters:
            pdsf: the ``PdsFile`` for an image file, such as a JPEG or a PNG.
            name (str): optional name for the viewable.

        Returns:
            PdsViewable: the new viewable.

        Raises:
            ValueError: if the ``PdsFile`` has no width, which is how a file that is not
                a displayable image presents itself.
        """

        if not pdsf.width:
            raise ValueError('PdsFile is not viewable: ' + pdsf.abspath)

        return PdsViewable(pdsf.abspath, pdsf.url, pdsf.width, pdsf.height,
                           pdsf.size_bytes, os.path.basename(pdsf.logical_path),
                           name, pdsf)

################################################################################
################################################################################
################################################################################

class PdsViewSet:
    """A group of viewables of one subject, selectable by size or by name.

    The members are held in the set ``viewables`` and indexed three ways: ``by_width``
    and ``by_height``, each keyed by that dimension in pixels, and ``by_name``, keyed by
    the name a viewable carries. ``widths`` and ``heights`` are the keys of the first two
    indexes in ascending order. ``priority`` ranks one set against another and matters
    only for icon sets.

    A named viewable is indexed by name and, by default, not by size. That is how a
    "full" product that does not resemble its own smaller versions -- because the small
    ones are color-coded and it is not -- stays out of the sizes a page picks from. It
    stays out only while there is something else to pick: a size lookup on a set with
    nothing indexed by size falls back to the member named "full", and failing that to an
    arbitrary member, so a set holding named viewables alone serves them from every
    lookup.

    Because ``by_width`` and ``by_height`` hold one viewable per distinct dimension, two
    members of the same width leave only one of them reachable by width; an unnamed
    viewable displaces a named one at the same size.
    """

    def __init__(self, viewables=[], priority=0, include_named_in_sizes=False):
        """Construct a set and append the given viewables to it.

        Parameters:
            viewables: the ``PdsViewable`` objects to append, as any iterable. The
                default is an empty list, which gives a set with no members.
            priority (int): rank of this set against other sets. Used when several icon
                sets could represent the same group of files.
            include_named_in_sizes (bool): if True, a named viewable is indexed by size
                as well as by name.
        """

        self.priority = priority    # Used to prioritize among icon sets
        self.viewables = set()      # All the PdsViewable objects

        self.by_width = {}          # Keyed by width in pixels
        self.by_height = {}         # Keyed by height in pixels
        self.by_name = {}           # Keyed by name; these PdsViewables might
                                    # not appear in other dictionaries

        self.widths = []            # sorted smallest to largest
        self.heights = []           # ditto

        for viewable in viewables:
            self.append(viewable, include_named_in_sizes=include_named_in_sizes)

    def __bool__(self):
        """Report whether this set holds any viewable at all.

        A set holding only named viewables is true and has a length of zero, since the
        length counts what is indexed by size.

        Returns:
            bool: True if the set has at least one member.
        """

        return len(self.viewables) > 0

    def __repr__(self):
        """Return the object's printable form.

        It quotes the absolute path of the widest member, or of an arbitrary member when
        none is indexed by width, and appends the member count when there is more than
        one.

        Returns:
            str: the text ``PdsViewSet()``, ``PdsViewSet("<abspath>")`` or
            ``PdsViewSet("<abspath>"...[<count>])``.
        """

        if not self.viewables:
            return 'PdsViewSet()'

        if self.widths:
            selected = self.by_width[self.widths[-1]]
        else:
            selected = next(iter(self.viewables))

        count = len(self.viewables)
        if count == 1:
            return f'PdsViewSet("{selected.abspath}")'
        else:
            return f'PdsViewSet("{selected.abspath}"...[{count}])'

    def append(self, viewable, include_named_in_sizes=False):
        """Add one viewable to this set and update the indexes.

        A viewable already in the set is ignored. A named viewable is indexed by name;
        it is also indexed by size only when ``include_named_in_sizes`` is True, which
        is what keeps a viewable called "full" reachable by name while ``for_width()``,
        ``for_height()`` and ``for_frame()`` continue to choose among the others.

        Where two viewables share a width or a height, an unnamed one takes the index
        slot from a named one; between two unnamed ones, the later call wins.

        Passing a ``PdsViewSet`` rather than a ``PdsViewable`` adds exactly one of that
        set's members, chosen arbitrarily, and ignores the rest. Passing an *empty*
        ``PdsViewSet`` is worse: it falls through to the code that indexes a viewable,
        which puts the set object itself among this set's members and then raises
        AttributeError. Every later size lookup on the damaged set fails too.

        Parameters:
            viewable: the ``PdsViewable`` to add.
            include_named_in_sizes (bool): if True, index a named viewable by size as
                well as by name.
        """

        if viewable in self.viewables:
            return

        # Allow a recursive call
        if isinstance(viewable, PdsViewSet):
            for sub_viewable in viewable.viewables:
                self.append(sub_viewable)
                return

        self.viewables.add(viewable)

        # Update the dictionary by name if it has a name
        if viewable.name:
            self.by_name[viewable.name] = viewable
            if not include_named_in_sizes:
                return

        # Update the dictionary by width
        # Unnamed viewables take precedence; named ones are overridden
        if (viewable.width not in self.by_width) or (not viewable.name):
            self.by_width[viewable.width] = viewable

        # Update the dictionary by height
        if (viewable.height not in self.by_height) or (not viewable.name):
            self.by_height[viewable.height] = viewable

        # Sort lists of widths and heights
        self.widths = list(self.by_width.keys())
        self.widths.sort()

        self.heights = list(self.by_height.keys())
        self.heights.sort()

    @staticmethod
    def from_dict(d):
        """Construct a set from a dictionary in the form ``to_dict()`` produces.

        The key ``'viewables'`` is required; a dictionary without it raises KeyError. The
        priority defaults to zero, which is what ``to_dict()`` omits. The members are
        appended with the default indexing, so a named member is reachable by name only,
        whatever the set it came from did.

        Parameters:
            d (dict): the values, keyed as ``to_dict()`` keys them.

        Returns:
            PdsViewSet: the reconstructed set.
        """

        obj = PdsViewSet(priority=d.get('priority', 0))
        for v in d['viewables']:
            obj.append(PdsViewable.from_dict(v))

        return obj

    def to_dict(self, exclude=['abspath', 'alt']):
        """Return this set as a dictionary of JSON-compatible values.

        The key ``'viewables'`` holds one dictionary per member, each in the form
        ``PdsViewable.to_dict()`` produces. The key ``'priority'`` is present only when
        the priority is not zero.

        The members are listed in the iteration order of a Python set, which is not the
        order they were appended in and is not stable across processes.

        Parameters:
            exclude: names of the optional member attributes to leave out, passed
                through to each member's ``to_dict()``. The default drops the absolute
                path and the alt text, which leaves the images described by URL, size and
                byte count, plus the name of any member that has one.

        Returns:
            dict: the encoded set.
        """

        d = {'viewables': [v.to_dict(exclude) for v in self.viewables]}
        if self.priority != 0:
            d['priority'] = self.priority       # defaults to zero

        return d

    def by_match(self, match):
        """Return a member whose absolute path or URL contains the given text.

        The test is against the absolute path and the URL joined together, so a match
        may straddle the join. Where several members match, the one returned depends on
        the iteration order of a Python set and is not predictable.

        Parameters:
            match (str): the text to search for.

        Returns:
            PdsViewable: a matching member, or None if none matches.
        """

        for v in self.viewables:
            if match in (v.abspath + v.url):
                return v

        return None

    @property
    def thumbnail(self):
        """The member whose path or URL contains ``_thumb``, else the shortest member.

        Raises IndexError when nothing matches and no member is indexed by height.

        Returns:
            PdsViewable: the thumbnail-sized member.
        """

        viewable = self.by_match('_thumb')
        if not viewable:
            viewable = self.by_height[self.heights[0]]

        return viewable

    @property
    def small(self):
        """The member whose path or URL contains ``_small``.

        When no member matches, reading this property raises AttributeError rather than
        falling back to a scaled copy.

        Returns:
            PdsViewable: the matching member.
        """

        viewable = self.by_match('_small')
        if not viewable:
            viewable = viewable.for_frame(200,200)

        return viewable

    @property
    def medium(self):
        """The member whose path or URL contains ``_med``.

        When no member matches, reading this property raises AttributeError rather than
        falling back to a scaled copy.

        Returns:
            PdsViewable: the matching member.
        """

        viewable = self.by_match('_med')
        if not viewable:
            viewable = viewable.for_frame(400,400)

        return viewable

    @property
    def full_size(self):
        """The member named "full", else the tallest member.

        Raises IndexError when there is no member named "full" and no member is indexed
        by height.

        Returns:
            PdsViewable: the full-size member.
        """

        if 'full' in self.by_name:
            return self.by_name['full']

        return self.by_height[self.heights[-1]]

    def __len__(self):
        """Report how many distinct widths this set can be looked up by.

        Members reachable by name alone are not counted, so a set that is true can still
        have a length of zero.

        Returns:
            int: the number of distinct widths indexed.
        """

        return len(self.widths)

    def for_width(self, size):
        """Return a copy of the best member for a target width, scaled to that width.

        The member chosen is the one with the smallest indexed width that is at least
        ``size``; if every indexed width is smaller, the widest is chosen. When no
        member is indexed by width, the member named "full" is used, and failing that an
        arbitrary member.

        The result is a copy whose width is exactly ``size`` and whose height is
        ``size`` times the source image's height-to-width ratio, rounded half up and
        forced to at least 1. Its byte count and aspect ratios are the source image's and
        do not describe the scaled dimensions.

        Parameters:
            size (int): the target width in pixels.

        Returns:
            PdsViewable: the scaled copy.

        Raises:
            OSError: if the set has no members.
        """

        if not self.viewables:
            raise OSError('No viewables have been defined')

        if self.widths:
            pdsview = self.by_width[self.widths[-1]]
            for key in self.widths[:-1]:
                if key >= size:
                    pdsview = self.by_width[key]
                    break
        elif 'full' in self.by_name:
            pdsview = self.by_name['full']
        else:
            pdsview = next(iter(self.viewables))

        result = pdsview.copy()
        result.height = max(1, int(pdsview.height_over_width * size + 0.5))
        result.width = size
        return result

    def for_height(self, size):
        """Return a copy of the best member for a target height, scaled to that height.

        The member chosen is the one with the smallest indexed height that is at least
        ``size``; if every indexed height is smaller, the tallest is chosen. When no
        member is indexed by height, the member named "full" is used, and failing that
        an arbitrary member.

        The result is a copy whose height is exactly ``size`` and whose width is
        ``size`` times the source image's width-to-height ratio, rounded half up and
        forced to at least 1. Its byte count and aspect ratios are the source image's and
        do not describe the scaled dimensions.

        Parameters:
            size (int): the target height in pixels.

        Returns:
            PdsViewable: the scaled copy.

        Raises:
            OSError: if the set has no members.
        """

        if not self.viewables:
            raise OSError('No viewables have been defined')

        if self.heights:
            pdsview = self.by_height[self.heights[-1]]
            for key in self.heights[:-1]:
                if key >= size:
                    pdsview = self.by_height[key]
                    break
        elif 'full' in self.by_name:
            pdsview = self.by_name['full']
        else:
            pdsview = next(iter(self.viewables))

        result = pdsview.copy()
        result.width = max(1, int(pdsview.width_over_height * size + 0.5))
        result.height = size
        return result

    def for_frame(self, width, height=None):
        """Return a copy of the best member scaled to fit inside a rectangle.

        The copy is scaled to the given width; if that makes it taller than the frame,
        it is scaled to the given height instead and its width is clamped to the frame's
        width. The result therefore fits within the frame in both directions, and
        touches at least one of its edges.

        Parameters:
            width (int): width of the frame in pixels.
            height (int): height of the frame in pixels. Defaults to the width, giving a
                square frame.

        Returns:
            PdsViewable: the scaled copy.

        Raises:
            OSError: if the set has no members. It is raised by the size lookups this
                calls, ``for_width()`` and ``for_height()``.
        """

        if height is None:
            height = width

        pdsview = self.for_width(width)
        if pdsview.height > height:
            pdsview = self.for_height(height)
            pdsview.width = min(pdsview.width, width)

        return pdsview

    @staticmethod
    def from_pdsfiles(pdsfiles, validate=False, full_is_special=True):
        """Construct a set from the ``PdsFile`` objects that name displayable images.

        A ``PdsFile`` that is not a displayable image is skipped, unless ``validate`` is
        True, in which case the first such file stops the call.

        When ``full_is_special`` is True, a file whose logical path contains ``_full.``
        is named "full" and appended after the others, which leaves it reachable by name
        and out of the lookups by size. Only one such file survives: each one replaces
        the one before it, and the replaced ones are not added to the set at all, so a
        group with two of them keeps the last and loses the first entirely.

        Parameters:
            pdsfiles: the ``PdsFile`` objects, as a list or a tuple. A single object may
                be passed instead of a one-item list.
            validate (bool): if True, do not skip a file that is not displayable.
            full_is_special (bool): if True, treat a path containing ``_full.`` as the
                full-size product and name it "full".

        Returns:
            PdsViewSet: the new set, or None if no file was displayable.

        Raises:
            ValueError: if ``validate`` is True and a file is not a displayable image.
                It is raised by ``PdsViewable.from_pdsfile()``.
        """

        if type(pdsfiles) not in (list,tuple):
            pdsfiles = [pdsfiles]

        viewables = []
        full_viewable = None
        for pdsf in pdsfiles:
            if full_is_special and '_full.' in pdsf.logical_path:
                name = 'full'
            else:
                name = ''

            try:
                viewable = PdsViewable.from_pdsfile(pdsf, name=name)
            except ValueError:
                if validate:
                    raise
            else:
                if name == 'full':
                    full_viewable = viewable
                else:
                    viewables.append(viewable)

        if viewables or full_viewable:
            viewset = PdsViewSet(viewables)
            if full_viewable:
                viewset.append(full_viewable)
            return viewset

        return None

################################################################################
# ICON definitions
################################################################################

# This is a dictionary keyed by icon file basename, which returns the icon_type
# and priority. # Priority is just a rough number to ensure that, when several
# files are grouped and represented by a single icon, the icon with the "best"
# icon (the one with highest priority number) is used. Primarily, this ensures
# that we do not use the label icon when a more specific icon is available.
#
# For proper layout, full-size folder icons are 500x365 (w x h); other icons
# are square.
#
# The boundary area of all icons is transparent.
#
# Standard sizes are 50, 100, and 200 pixels wide. Size 30 is also useful but
# not required. This refers to the widths of folder icons.

REQUIRED_ICONS = {      # basename: (icon name, priority)

    # Lowest-priority, least descriptive icons
    'document_generic'   : ('UNKNOWN'  ,  0),   # < LABEL
    'document_label'     : ('LABEL'    ,  1),
    'folder_generic'     : ('FOLDER'   ,  2),   # < any specific folder

    # Folders are never grouped, so they can all have the same priority
    'folder_previews'    : ('BROWDIR'  , 15),
    'folder_checksums'   : ('CHECKDIR' , 15),
    'folder_software'    : ('CODEDIR'  , 15),
    'folder_cubes'       : ('CUBEDIR'  , 15),
    'folder_binary'      : ('DATADIR'  , 15),
    'folder_diagrams'    : ('DIAGDIR'  , 15),
    'folder_extras'      : ('EXTRADIR' , 15),
    'folder_geometry'    : ('GEOMDIR'  , 15),
    'folder_images'      : ('IMAGEDIR' , 15),
    'folder_index'       : ('INDEXDIR' , 15),
    'folder_info'        : ('INFODIR'  , 15),
    'folder_labels'      : ('LABELDIR' , 15),
    'folder_series'      : ('SERIESDIR', 15),
    'folder_archives'    : ('TARDIR'   , 15),
    'folder_volumes'     : ('VOLDIR'   , 15),

    # These last two "folders" don't look like folders, but they serve the same
    # function. They are not square; they have folder proportions. They look the
    # same "open" or "closed".
    'folder_volume'      : ('VOLUME'   , 15),
    'folder_viewmaster'  : ('ROOT'     , 15),

    # Documents always take priority over their labels. In cases where multiple
    # documents are grouped, the more descriptive icon has the higher priority,
    # so it is the one that will be used.
    'document_binary'    : ('DATA'     , 20),   # < IMAGE, etc.
    'document_zipbook'   : ('ZIPFILE'  , 21),   # < LINK
    'document_checksums' : ('CHECKSUM' , 22),
    'document_archive'   : ('TARBALL'  , 23),
    'document_diagram'   : ('DIAGRAM'  , 24),
    'document_preview'   : ('BROWSE'   , 25),
    'document_info'      : ('INFO'     , 26),   # < TXTDOC

    'document_link'      : ('LINK'     , 31),
    'document_table'     : ('TABLE'    , 32),   # < INDEX, SERIES
    'document_image'     : ('IMAGE'    , 33),   # < CUBE
    'document_geometry'  : ('GEOM'     , 34),
    'document_txt'       : ('TXTDOC'   , 35),   # < PDFDOC, CODE

    'document_index'     : ('INDEX'    , 41),
    'document_series'    : ('SERIES'   , 42),
    'document_cube'      : ('CUBE'     , 43),
    'document_software'  : ('CODE'     , 44),
    'document_pdf'       : ('PDFDOC'   , 45),
    'document_pdsinfo'   : ('PDSINFO'  , 46),
}

REQUIRED_SIZES = {50, 100, 200}

# Create a dictionary of PdsViewSets keyed by:
#   [icon_type]
#   [icon_type, open_state]
#   [icon_type, open_state, color]

ICON_SET_BY_TYPE = {}

def load_icons(path, url, color='blue', logger=None):
    """Read a tree of icon files into ``ICON_SET_BY_TYPE``, for ``iconset_for()`` to use.

    The tree is walked and every file whose extension lowercases to ``.png`` is read;
    files whose names begin with a dot are skipped, and so, as the extension test stands,
    are JPEG files. Each image becomes a ``PdsViewable``, and the images sharing a
    basename become one ``PdsViewSet``.

    An image's nominal size is what distinguishes two images sharing a basename, and is
    what ``REQUIRED_SIZES`` is checked against; it is not the size the image is indexed
    under within its set, which is always the image's own width and height. It is read
    from the deepest path component of the form ``png-<n>`` above the image, or, only if
    there is no such component at all, from the deepest ``jpg-<n>``. Where there is
    neither, the larger of the image's own two dimensions is used.

    A set is stored under the icon type and priority that ``REQUIRED_ICONS`` gives for
    its basename. A basename that is not listed there supplies its own type, which is the
    basename uppercased with ``document_`` and ``folder_`` removed -- every occurrence,
    not just a leading one, so ``page_folder_icon`` supplies ``PAGE_ICON`` -- and takes
    priority 99999, above every listed type.

    A basename ending in ``_open`` supplies the open form of its type. Each set is
    stored under the key ``(icon_type, is_open)``; a closed set is also stored under
    ``icon_type`` alone, and under ``(icon_type, True)`` if no open form has been stored
    yet. When ``color`` is given, the set is stored under ``(icon_type, is_open, color)``
    as well, so icons of several colors can be held at once.

    The call may be repeated over different directories. Nothing is removed, and a set
    read later replaces one read earlier under the same key -- except under
    ``(icon_type, True)``, whose test for an existing entry does not distinguish one
    left by an earlier call from one left by this call. A directory read second therefore
    supplies the closed icons and leaves the first directory's open icons in place, which
    is the key ``iconset_for(..., is_open=True)`` reads.

    With a logger, an image file that is not a recognizable image is reported and
    skipped, and a set missing any of ``REQUIRED_SIZES`` is reported. Without one, such a
    file is neither reported nor skipped: it is stored, carrying the dimensions of
    whichever image was read before it, and if it is the first image the walk reaches
    there is no such previous image and the call raises UnboundLocalError.

    Only an unrecognizable image is handled at all. Any other failure to open a file --
    a broken symlink, a permission error -- propagates out of the call, logger or no
    logger.

    Parameters:
        path (str): path to the directory tree holding the icon files.
        url (str): URL prefix that serves that tree. A file's URL is this prefix
            followed by its path below the tree.
        color (str): name of the color subdirectory to read, appended to both the path
            and the URL. Pass a false value to read the tree's top level instead and to
            store no color-keyed entries.
        logger: optional PdsLogger for problem reports.
    """

    icon_path_ = path.rstrip('/') + '/'
    icon_url_  = url.rstrip('/') + '/'

    if color:
        icon_path_ += color + '/'
        icon_url_  += color + '/'

    # Read all image files in this directory tree; organize by basename and size
    viewables = {}
    for root, _dirs, basenames in os.walk(icon_path_):

        # Guess the nominal size from the directory path, if possible
        parts = root.rpartition('/png-')
        if not parts[2]:
            parts = root.rpartition('/jpg-')
        if parts[2]:
            parts = parts[2].partition('/')
            try:
                nominal_size = int(parts[0])
            except ValueError:
                nominal_size = 0
        else:
            nominal_size = 0

        # For each image file...
        for basename in basenames:
            if basename[0] == '.':
                continue

            (key,ext) = os.path.splitext(basename)
            if ext.lower() not in ('.png', 'jpg'):
                continue

            # Create the PdsViewable
            abspath = os.path.join(root, basename).replace('\\', '/')
            url = icon_url_ + abspath[len(icon_path_):]
            try:
                im = Image.open(abspath)
            except Image.UnidentifiedImageError:
                if logger:
                    logger.error('Invalid icon file', abspath)
                    continue

            (width, height) = im.size
            size = nominal_size or max(im.size)
            im.close()
            bytecount = os.stat(abspath).st_size
            pdsview = PdsViewable(abspath, url, width, height, bytecount)

            # Save the PdsViewable by basename and size
            if key in viewables:
                viewables[key][size] = pdsview
            else:
                viewables[key] = {size: pdsview}

    # Save PdsViewsets into the master dictionary
    for key, size_dict in viewables.items():

        # Define icon name, open status, and priority
        is_open = key.endswith('_open')
        key_base = key[:-5] if is_open else key

        if key_base in REQUIRED_ICONS:
            (icon_name, priority) = REQUIRED_ICONS[key_base]
        else:
            icon_name = key_base.replace('document_', '')
            icon_name = icon_name.replace('folder_', '')
            icon_name = icon_name.upper()
            priority = 99999

        # Warn if any sizes are missing
        sizes = set(size_dict)
        missing = REQUIRED_SIZES - sizes
        if missing and logger:
            missing = list(missing)
            missing.sort()
            logger.warn(f'Missing sizes for icon {icon_name} ({key})',
                        str(missing)[1:-1])

        # Create the PdsViewSet
        viewset = PdsViewSet(size_dict.values(), priority)

        # Save into dictionary under multiple keys
        ICON_SET_BY_TYPE[icon_name, is_open] = viewset
        if not is_open:
            ICON_SET_BY_TYPE[icon_name] = viewset

            # Also save under open=True if there is no file ending in "_open"
            if (icon_name, True) not in ICON_SET_BY_TYPE:
                ICON_SET_BY_TYPE[icon_name, True] = viewset

        if color:
            ICON_SET_BY_TYPE[icon_name, is_open, color] = viewset

################################################################################
# Method to select among multiple icons
################################################################################

def _priority_of_icon_type(icon_type, is_open):
    """Return the priority of the icon set for this icon type and open state.

    load_icons() puts a priority into every PdsViewSet it creates -- the one
    REQUIRED_ICONS gives for a listed basename, and 99999 for any other -- so the
    loaded icon sets are the authority on priority. The lookup is keyed on the open
    state that is actually being requested, so an icon type can only win a
    comparison if the set that would then be returned exists. A type with no icon
    set for this open state has no priority and gets zero, the same value as the
    least descriptive icon.

    Parameters:
        icon_type (str): the icon type, as it appears in ``REQUIRED_ICONS``.
        is_open (bool): the open state being requested.

    Returns:
        int: the priority of the matching icon set, or zero if there is none.
    """

    viewset = ICON_SET_BY_TYPE.get((icon_type, is_open))
    if viewset is None:
        return 0

    return viewset.priority

def iconset_for(pdsfiles, is_open=False):
    """Return the one icon set that best represents a group of files.

    Each file offers its own icon type, and the type with the highest priority wins. The
    comparison starts from ``UNKNOWN``, which is what an empty group leaves standing, and
    what a group whose every type is unloaded for this open state leaves standing too.

    ``UNKNOWN`` is not checked for existence before it is looked up, so the lookup can
    fail on the fallback rather than on the group. The requirement is that
    ``load_icons()`` has loaded a ``document_generic`` icon for the open state being
    asked for, and not merely that it has run: without one, this raises KeyError for
    every group whose types are all unloaded, the empty group included.

    Parameters:
        pdsfiles: the ``PdsFile`` objects, as a list. A single object may be passed
            instead of a one-item list; a tuple may not.
        is_open (bool): True to return the open form of the icon set, for a directory
            being shown expanded.

    Returns:
        PdsViewSet: the icon set for the winning icon type and open state.
    """

    if type(pdsfiles) is not list:
        pdsfiles = [pdsfiles]

    icon_type = 'UNKNOWN'
    priority = _priority_of_icon_type(icon_type, is_open)

    for pdsf in pdsfiles:
        test_type = pdsf.icon_type
        new_priority = _priority_of_icon_type(test_type, is_open)
        if new_priority > priority:
            priority = new_priority
            icon_type = test_type

    return ICON_SET_BY_TYPE[icon_type, is_open]

################################################################################
