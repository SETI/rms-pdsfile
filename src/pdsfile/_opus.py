##########################################################################################
# pdsfile/_opus.py
# OPUS support: the constructors that resolve an OPUS ID or a file specification, and the
# product dictionary OPUS consumes
##########################################################################################

from collections import defaultdict

from ._path_utils import _needs_glob, abspath_for_logical_path


##########################################################################################
# OPUS mixin
##########################################################################################
class _OpusMixin:
    """The methods that serve OPUS.

    A mixin of PdsFile; it holds methods only and defines no state of its own.

    Every attribute these methods read or write on a PdsFile object or on a
    PdsFile class, and nothing else -- str, list, dict and translator methods are
    not in scope:

      class attributes and        BUNDLE_DIR_NAME, CROSS_PDS3_PDS4_PRODUCTS,
      translators read            FILESPEC_TO_BUNDLESET, LOCAL_PRELOADED, LOGGER,
                                  OPUS_ID_TO_PRIMARY_LOGICAL_PATH,
                                  OPUS_ID_TO_SUBCLASS, OPUS_PRODUCTS,
                                  PDS_HOLDINGS, and the two the interpreter
                                  supplies, __base__ and __subclasses__
      lazy properties read        islabel, label_abspath, linked_abspaths,
                                  opus_type
      instance attributes read    abspath, logical_path, root_, version_rank
      instance attributes written none
      other methods called        from_abspath, from_logical_path,
                                  pdsfiles_for_abspaths, and the optional
                                  opus_prioritizer hook the rule modules supply

    All of them are defined on PdsFile or on its subclasses. Three more come from
    sibling mixins: glob_glob and os_path_exists from _LocalFsMixin, shelf_lookup
    from _ShelfMixin. Every one of these is an attribute lookup on self or on a
    class at run time, not an import, which is what lets the halves live in
    different modules.

    opus_products is the one method in the package that needs the PdsFile class
    object itself, to enumerate its direct subclasses. Its import is deferred into
    the method body: pdsfile.py imports this module to build the class, so a
    module-level import would be a cycle.
    """

    @classmethod
    def from_filespec(cls, filespec, fix_case=False):
        """Return the PdsFile object based on a bundle name plus file specification
        path, without the category or prefix specified.

        Keyword arguments:
            filespec -- the file specification
            fix_case -- True to fix the case of the child. (If False, it is permissible
                        but not necessary to fix the case anyway) (default False)
        """

        bundleset = cls.FILESPEC_TO_BUNDLESET.first(filespec)
        if not bundleset:
            raise ValueError('Unrecognized file specification: ' + filespec)

        return cls.from_logical_path(cls.BUNDLE_DIR_NAME + '/' + bundleset + '/'
                                         + filespec, fix_case)

    @classmethod
    def from_opus_id(cls, opus_id):
        """Return the PdsFile of the primary data file associated with this OPUS ID.

        Keyword arguments:
            opus_id -- the given opus id
        """

        pdsfile_class = cls.OPUS_ID_TO_SUBCLASS.first(opus_id)
        if not pdsfile_class:
            raise ValueError('Unrecognized OPUS ID: ' + opus_id)

        # If implemented as a function rather than as a translator...
        if callable(pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH):
            return pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH(opus_id)

        paths = pdsfile_class.OPUS_ID_TO_PRIMARY_LOGICAL_PATH.all(opus_id)
        patterns = [abspath_for_logical_path(p, cls) for p in paths]
        matches = []
        for pattern in patterns:
            if _needs_glob(pattern):
                abspaths = cls.glob_glob(pattern, force_case_sensitive=True)
            elif cls.os_path_exists(pattern, force_case_sensitive=True):
                abspaths = [pattern]
            else:
                abspaths = []

            matches += abspaths

        # One match is easy to handle
        if len(matches) == 1:
            return cls.from_abspath(matches[0])

        if len(matches) == 0:
            raise ValueError('Unrecognized OPUS ID: ' + opus_id)

        # Call a special product prioritizer if available
        pdsfiles = cls.pdsfiles_for_abspaths(matches)
        if hasattr(pdsfiles[0], 'opus_prioritizer'):
            fake_opus_key = ('', 0, '', '', True)
            fake_opus_sublists = [[pdsf] for pdsf in pdsfiles]
            fake_product_dict = {fake_opus_key: fake_opus_sublists}
            fake_product_dict = pdsfiles[0].opus_prioritizer(fake_product_dict)
            return fake_product_dict[fake_opus_key][0][0]

        for k, pdsf in enumerate(pdsfiles):
            cls.LOGGER.warn('Ambiguous primary product for OPUS ID ' + opus_id,
                        pdsf.abspath + (' (selected)' if k == 0 else ''))

        return pdsfiles[0]

    def opus_products(self):
        """For this primary data product or label, return a dictionary keyed
        by a tuple containing this information:
          (group, priority, opus_type, description, default_checked)
        Examples:
          ('Cassini ISS',    0, 'coiss_raw',       'Raw Image',                  True)
          ('Cassini VIMS', 130, 'covims_full',     'Extra Preview (full-size)',  True)
          ('Cassini CIRS', 618, 'cirs_browse_pan', 'Extra Browse Diagram (Pan)', True)
          ('metadata',      40, 'ring_geometry',   'Ring Geometry Index',        True)
          ('browse',        30, 'browse_medium',   'Browse Image (medium)',      True)
        These keys are designed such that OPUS results will be returned in the
        sorted order of these keys.

        For any key, this dictionary returns a list of sublists. Each sublist
        has the form:
            [PdsFile for a data product,
             PdsFile for its label (if any),
             PdsFile for the first embedded .FMT file (if any),
             PdsFile for the second embedded .FMT file (if any), etc.]
        This sublist contains every file that should be added to the OPUS
        results if that data product is requested. The sublists appear in order
        of decreasing version.

        If a class function opus_prioritizer exists, this is called before the
        dictionary is returned. In cases where multiple products with the same
        OPUS ID and version exists, an opus_prioritizer can be used to alter the
        dictionary returned in order to highlight the "best" among the
        alternative products.
        """

        cls = type(self)

        # Get the associated absolute paths
        patterns = self.OPUS_PRODUCTS.all(self.logical_path)

        abs_patterns_and_opus_types = []
        for pattern in patterns:
            if isinstance(pattern, str):    # match string only
                abs_patterns_and_opus_types.append((self.root_ + pattern, None))
            else:                           # (match string, opus_type)
                (p, opus_type) = pattern
                abs_patterns_and_opus_types.append((self.root_ + p, opus_type))

        # Construct a complete list of matching abspaths.
        # Create a dictionary of opus_types based on abspaths where opus_types
        # have already been specified.
        abspaths = []
        opus_type_for_abspath = {}
        for (pattern, opus_type) in abs_patterns_and_opus_types:
            these_abspaths = cls.glob_glob(pattern,
                                           force_case_sensitive=True)
            if opus_type:
                for abspath in these_abspaths:
                    opus_type_for_abspath[abspath] = opus_type

            for path in these_abspaths:
                abspaths.append((path, cls))

        # Handle cross pds products
        cross_pds_products_patterns = self.CROSS_PDS3_PDS4_PRODUCTS.all(self.logical_path)
        new_root = ''
        other_pds_cls = None

        # Deferred: pdsfile.py imports this module to build PdsFile, so importing
        # the class at module level here would be a cycle.
        from pdsfile.pdsfile import PdsFile

        direct_pds_subclasses = PdsFile.__subclasses__()
        family_cls = cls if cls in direct_pds_subclasses else cls.__base__
        sibling_cls_list = [sub_cls for sub_cls in direct_pds_subclasses
                            if sub_cls is not family_cls]

        # Get the proper root directory name for corss pds products
        for sub_cls in sibling_cls_list:
            if sub_cls.LOCAL_PRELOADED:
                new_root = f'{sub_cls.LOCAL_PRELOADED[0]}/'
            else:
                new_root = self.root_.replace(cls.PDS_HOLDINGS, sub_cls.PDS_HOLDINGS)
            other_pds_cls = sub_cls
            break

        if other_pds_cls is None:
            cross_pds_products_patterns = []

        # Append the cross pds products
        tmp_abspaths = []
        for pattern in cross_pds_products_patterns:
            pattern = new_root + pattern
            these_abspaths = other_pds_cls.glob_glob(pattern,
                                                     force_case_sensitive=True)

            for path in these_abspaths:
                tmp_abspaths.append((path, other_pds_cls))

        is_all_idx = True
        for path in tmp_abspaths:
            if '_index' not in path[0]:
                is_all_idx = False
                break
        # Don't include reproj index if there is no reproj files
        if not is_all_idx:
            abspaths += tmp_abspaths

        # Get PdsFiles for abspaths, organized by labels vs. datafiles
        # label_files[label_abspath] = [label_pdsfile, fmt1_pdsfile, ...]
        # data_files is a list
        label_pdsfiles = {}
        data_pdsfiles = []
        for (abspath, pds_class) in abspaths:
            pdsf = pds_class.from_abspath(abspath)
            if pdsf.islabel:
                # Check if the corresponding link info exists. If not, we issue
                # a warning and skip looking for the .fmt files.
                # Note this means that opus_products might return a different
                # list of products once the link file is available.
                try:
                    pdsf.shelf_lookup('link')
                except (OSError, KeyError, ValueError):
                    cls.LOGGER.warn('Missing links info',
                                pdsf.logical_path)
                    fmt_pdsfiles = []
                else:
                    links = set(pdsf.linked_abspaths)
                    fmts = [f for f in links if f.lower().endswith('.fmt')]
                    fmts.sort()
                    fmt_pdsfiles = pds_class.pdsfiles_for_abspaths(fmts,
                                                             must_exist=True)
                label_pdsfiles[abspath] = [pdsf, *fmt_pdsfiles]
            else:
                data_pdsfiles.append(pdsf)

        # Construct the dictionary to return
        pdsfile_dict = {}
        label_visited = defaultdict(list)
        for pdsf in data_pdsfiles:
            key = opus_type_for_abspath.get(pdsf.abspath, pdsf.opus_type)
            if key == '':
                cls.LOGGER.error('Unknown opus_type for', pdsf.abspath)
            if key not in pdsfile_dict:
                pdsfile_dict[key] = []

            # The try and except here is to bypass the error raised by missing link shelf
            # in internal_link_info when SHELVES_REQUIRED is set to True. In current opus
            # import for pds4, we don't have link shelf files, so the opus_prodcuts call
            # there will raise an error if we don't bypass it.
            try:
                # avoid duplicated label files in one opus type category
                if pdsf.label_abspath and pdsf.label_abspath not in label_visited[key]:
                    label_visited[key].append(pdsf.label_abspath)
                    sublist = [pdsf] + label_pdsfiles[pdsf.label_abspath]
                else:
                    sublist = [pdsf]
            except (OSError, KeyError, ValueError):
                sublist = [pdsf]

            pdsfile_dict[key].append(sublist)

        # Call a special product prioritizer if available
        if hasattr(self, 'opus_prioritizer'):
            self.opus_prioritizer(pdsfile_dict)

        # Sort the return
        for (header, sublists) in pdsfile_dict.items():
            # For the same opus type (header), combine different lists of the same
            # version to one sublist
            new_sublist_dict = {}
            for li in sublists:
                version = li[0].version_rank
                if li[0].version_rank not in new_sublist_dict:
                    new_sublist_dict[version] = li
                else:
                    new_sublist_dict[version] += li

            new_sublists = list(new_sublist_dict.values())

            # Sort the sublist by filepath (alphabetical order)
            for li in new_sublists:
                li.sort(key=lambda x: x.abspath)

            # Sort the list of sublists by version (in the order of decreasing version)
            new_sublists.sort(key=lambda x: x[0].version_rank, reverse=True)

            # update pdsfile_dict with sorted sublists
            pdsfile_dict[header] = new_sublists

        return pdsfile_dict
