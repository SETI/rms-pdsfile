################################################################################
# pdsviewable.py
################################################################################

import os
from PIL import Image

import pdslogger

################################################################################
# Class definitions
################################################################################

class PdsViewable(object):
    """Contains the minimum information needed to show an image in HTML."""

    def __init__(self, abspath, url, width, height, bytecount, alt='',
                       name='', pdsf=None):

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
        return 'PdsViewable("' + self.abspath + '")'

    def assign_name(self, name):
        """Assign a name to this PdsViewable"""

        self.name = name

    def copy(self):
        """An exact copy of this PdsViewable"""

        return PdsViewable(self.abspath, self.url, self.width, self.height,
                           self.bytes, self.alt, self.name, self.pdsf)

    def to_dict(self, exclude=[]):
        """Return the attributes of a PdsViewable object as a dictionary
        suitable for JSON.

        The abspath, url, and alt, and attributes can optionally be excluded.
        If the name attribute is blank, it is excluded."""

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
        """Construct a PdsViewable object from the dictionary returned by
        to_dict.

        If the alt attribute is missing, the basename of the abspath or url
        is used in its place.
        """

        abspath = d.get('abspath', '')
        url     = d.get('url',  '')
        alt     = d.get('alt',  os.path.basename(abspath or url))
        name    = d.get('name', '')

        return PdsViewable(abspath, url, d['width'], d['height'], d['bytes'],
                           alt, name)

    @staticmethod
    def from_pdsfile(pdsf, name=''):
        """Construct a PdsViewable object from a PdsFile representing a file
        that happens to be viewable, such as a JPEG or PNG."""

        if not pdsf.width:
            raise ValueError('PdsFile is not viewable: ' + pdsf.abspath)

        return PdsViewable(pdsf.abspath, pdsf.url, pdsf.width, pdsf.height,
                           pdsf.size_bytes, os.path.basename(pdsf.logical_path),
                           name, pdsf)

################################################################################
################################################################################
################################################################################

class PdsViewSet(object):
    """Viewables selectable by size or name."""

    def __init__(self, viewables=[], priority=0, include_named_in_sizes=False):

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
        return len(self.viewables) > 0

    def __repr__(self):
        if not self.viewables:
            return 'PdsViewSet()'

        if self.widths:
            selected = self.by_width[self.widths[-1]]
        else:
            selected = list(self.viewables)[0]

        count = len(self.viewables)
        if count == 1:
            return f'PdsViewSet("{selected.abspath}")'
        else:
            return f'PdsViewSet("{selected.abspath}"...[{count}])'

    def append(self, viewable, include_named_in_sizes=False):
        """Append the given PdsViewable to this PdsViewSet.

        If include_named_in_sizes is True, then a named viewable is added to the
        dictionaries keyed by size. Otherwise, not. This allows a PdsViewable
        object called "full" to be accessible by name but never to be used by
        for_width, for_height, or for_frame. Often, our "full" products do not
        look the same as the smaller versions because, for example, the smaller
        versions are color-coded but the "full" version is not. In this case,
        we want to ensure that the color-coded are always used in web pages
        unless "full" is requested explicitly.
        """

        if viewable in self.viewables:
            return

        # Allow a recursive call
        if isinstance(viewable, PdsViewSet):
            for viewable in viewable.viewables:
                self.append(viewable)
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
        """Alternative constructor from a JSON-friendly dictionary generated by
        from_dict()."""

        obj = PdsViewSet(priority=d.get('priority', 0))
        for v in d['viewables']:
            obj.append(PdsViewable.from_dict(v))

        return obj

    def to_dict(self, exclude=['abspath', 'alt']):
        """Return a the info in this PdsViewSet encoded into JSON-friendly
        dictionaries."""

        d = {'viewables': [v.to_dict(exclude) for v in self.viewables]}
        if self.priority != 0:
            d['priority'] = self.priority       # defaults to zero

        return d

    def by_match(self, match):
        """Return a PdsViewable that contains the given match string"""

        for v in self.viewables:
            if match in (v.abspath + v.url):
                return v

        return None

    @property
    def thumbnail(self):
        viewable = self.by_match('_thumb')
        if not viewable:
            viewable = self.by_height[self.heights[0]]

        return viewable

    @property
    def small(self):
        viewable = self.by_match('_small')
        if not viewable:
            viewable = viewable.for_frame(200,200)

        return viewable

    @property
    def medium(self):
        viewable = self.by_match('_med')
        if not viewable:
            viewable = viewable.for_frame(400,400)

        return viewable

    @property
    def full_size(self):
        """The viewable designated as "full" or else the largest."""

        if 'full' in self.by_name:
            return self.by_name['full']

        return self.by_height[self.heights[-1]]

    def __len__(self):
        """Number of PdsViewables organized by size in this PdsViewSet."""

        return len(self.widths)

    def for_width(self, size):
        """The PdsViewable for the specified width."""

        if not self.viewables:
            raise IOError('No viewables have been defined')

        if self.widths:
            pdsview = self.by_width[self.widths[-1]]
            for key in self.widths[:-1]:
                if key >= size:
                    pdsview = self.by_width[key]
                    break
        elif 'full' in self.by_name:
            pdsview = self.by_name['full']
        else:
            pdsview = list(self.viewables)[0]

        result = pdsview.copy()
        result.height = max(1, int(pdsview.height_over_width * size + 0.5))
        result.width = size
        return result

    def for_height(self, size):
        """The PdsViewable for the specified height."""

        if not self.viewables:
            raise IOError('No viewables have been defined')

        if self.heights:
            pdsview = self.by_height[self.heights[-1]]
            for key in self.heights[:-1]:
                if key >= size:
                    pdsview = self.by_height[key]
                    break
        elif 'full' in self.by_name:
            pdsview = self.by_name['full']
        else:
            pdsview = list(self.viewables)[0]

        result = pdsview.copy()
        result.width = max(1, int(pdsview.width_over_height * size + 0.5))
        result.height = size
        return result

    def for_frame(self, width, height=None):
        """The PdsViewable to fit inside the specified rectangle."""

        if height is None:
            height = width

        pdsview = self.for_width(width)
        if pdsview.height > height:
            pdsview = self.for_height(height)
            pdsview.width = min(pdsview.width, width)

        return pdsview

    @staticmethod
    def from_pdsfiles(pdsfiles, validate=False, full_is_special=True):
        """A PdsViewSet constructed from a list of viewable PdsFile objects."""

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
                if validate: raise
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

REQUIRED_SIZES = set([50, 100, 200])

# Create a dictionary of PdsViewSets keyed by:
#   [icon_type]
#   [icon_type, open_state]
#   [icon_type, open_state, color]

ICON_SET_BY_TYPE = {}

def load_icons(path, url, color='blue', logger=None):
    """Loads icons for use by PdsViewable.iconset_for().

    This can be called multiple times on different directories. The icons
    loaded last take precedence. Icons loaded earlier are not removed, although
    they may be replaced.

    Icons found in the directory tree that do not correspond to one of the
    "required" names are saved under the name embedded within the file,
    following "document_" or "folder_", and with an optional, trailing, "_open".

    If a color is specified, the subdirectory of that name is searched and the
    icons are also keyed under their color in the ICON_SET_BY_TYPE dictionary.
    In this way, it would be possible to work with icons with different colors
    at the same time within OPUS or Viewmaster, although this capability is
    unused.
    """

    icon_path_ = path.rstrip('/') + '/'
    icon_url_  = url.rstrip('/') + '/'

    if color:
        icon_path_ += color + '/'
        icon_url_  += color + '/'

    # Read all image files in this directory tree; organize by basename and size
    viewables = {}
    for root, dirs, basenames in os.walk(icon_path_):

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

def iconset_for(pdsfiles, is_open=False):
    """Select the icon set for a list of PdsFiles. Use the icon_type highest in
    priority."""

    if type(pdsfiles) != list:
        pdsfiles = [pdsfiles]

    icon_type = 'UNKNOWN'
    (priority, template) = ICON_FILENAME_VS_TYPE[icon_type]

    for pdsf in pdsfiles:
        test_type = pdsf.icon_type
        (new_priority, _) = ICON_FILENAME_VS_TYPE[test_type]
        if new_priority > priority:
            priority = new_priority
            icon_type = test_type

    return ICON_SET_BY_TYPE[icon_type, is_open]

################################################################################
