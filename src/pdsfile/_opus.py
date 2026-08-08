##########################################################################################
# pdsfile/_opus.py
##########################################################################################

"""OPUS support: resolving an OPUS ID, and the product dictionary OPUS consumes.

OPUS is the search tool that publishes this holdings tree. It names a data product by an
**OPUS ID**, a short identifier such as ``co-iss-n1460961026``, and by an **OPUS type**,
a short name for a product's role such as ``coiss_raw`` or ``browse_medium``. Neither is
a path; both are mapped onto paths by translator tables the rule modules define.

``_OpusMixin`` holds three methods. ``from_filespec()`` and ``from_opus_id()`` are
constructors: each turns an identifier OPUS holds into the PdsFile it names.
``opus_products()`` goes the other way, and is the one OPUS calls per search result: it
takes one data product and returns every file OPUS should offer alongside it, keyed by
what each group of files is for.
"""

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
    not in scope::

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

    opus_prioritizer is a hook, not a member: a rule subclass may define it and
    most do not, so both call sites test for it with hasattr first. The two call
    sites disagree about its result. from_opus_id rebinds its dictionary from the
    return value; opus_products discards the return value and keeps its own
    dictionary, so a prioritizer there can only take effect by mutating in place.
    The two implementations in the tree do both, which is why the disagreement is
    invisible today.

    None of these methods works on a bare PdsFile. FILESPEC_TO_BUNDLESET,
    OPUS_ID_TO_SUBCLASS and OPUS_PRODUCTS are all None there, so the first
    translator call raises AttributeError, and CROSS_PDS3_PDS4_PRODUCTS is not
    defined on PdsFile at all. All four carry a real table on Pds3File and
    Pds4File, which is where OPUS uses them.
    """

    @classmethod
    def from_filespec(cls, filespec, fix_case=False):
        """Return the PdsFile named by a file specification, without its category.

        A file specification is the part of a logical path that starts at the bundle
        name, so it carries no category and no bundle set. The bundle set is recovered
        from the specification itself, through the class's ``FILESPEC_TO_BUNDLESET``
        translator, and the category is always the class's ``BUNDLE_DIR_NAME``, so the
        file this returns is always in the bundles tree and never in a parallel one.

        The result is constructed, not verified: nothing here reads the filesystem, so
        a well-formed specification for a file that does not exist still returns an
        object.

        Parameters:
            filespec (str): the file specification, starting at the bundle name.
            fix_case (bool): whether to correct the capitalization of each component
                against the filesystem. False leaves the capitalization as given, which
                may still happen to be corrected.

        Returns:
            PdsFile: the object for that specification.

        Raises:
            ValueError: if the translator recognizes no bundle set for the
                specification.
        """

        bundleset = cls.FILESPEC_TO_BUNDLESET.first(filespec)
        if not bundleset:
            raise ValueError('Unrecognized file specification: ' + filespec)

        return cls.from_logical_path(cls.BUNDLE_DIR_NAME + '/' + bundleset + '/'
                                         + filespec, fix_case)

    @classmethod
    def from_opus_id(cls, opus_id):
        """Return the PdsFile of the primary data file an OPUS ID names.

        The OPUS ID first selects the rule subclass that owns it, through the class's
        ``OPUS_ID_TO_SUBCLASS`` translator; everything after that is done on that
        subclass rather than on the class this was called on.

        That subclass supplies ``OPUS_ID_TO_PRIMARY_LOGICAL_PATH``, which is either a
        plain function or a translator table. A function is called and its result is
        returned as it stands, so what that branch returns is whatever the rule module
        chose to return. A translator yields one or more logical paths, each of which is
        made absolute and then resolved against the filesystem: a path holding a
        wildcard through a case-sensitive glob, one without through a case-sensitive
        existence test.

        Exactly one surviving match is the ordinary case. Several means the OPUS ID is
        ambiguous, and then a rule subclass that defines the ``opus_prioritizer`` hook
        decides, through a single-key dictionary built for the purpose; one that does
        not defines nothing, so the first match wins and every match is logged as a
        warning, with the chosen one marked.

        Parameters:
            opus_id (str): the OPUS ID.

        Returns:
            PdsFile: the primary data file.

        Raises:
            ValueError: if no rule subclass claims the OPUS ID, or if no file on this
                machine matches any path the subclass derives from it.
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
        """Return every file OPUS should offer alongside this data product or label.

        The answer is a dictionary. Each key is a five-element tuple, and OPUS displays
        the results in the sorted order of those keys, which is what the group name and
        the priority number are for::

            (group, priority, opus_type, description, default_checked)

            ('Cassini ISS',    0, 'coiss_raw',       'Raw Image',                  True)
            ('Cassini VIMS', 130, 'covims_full',     'Extra Preview (full-size)',  True)
            ('Cassini CIRS', 618, 'cirs_browse_pan', 'Extra Browse Diagram (Pan)', True)
            ('metadata',      40, 'ring_geometry',   'Ring Geometry Index',        True)
            ('browse',        30, 'browse_medium',   'Browse Image (medium)',      True)

        Each value is a list of sublists, and a sublist is what OPUS adds to its results
        together. A sublist holds a data product, the label that describes it if the
        label was among the files found, and every ``.fmt`` file that label embeds, in
        that order for a product that is alone at its version. **Products that share a
        version rank are concatenated into one sublist**, so a sublist can hold several
        data products and several labels, and the whole sublist is then sorted by
        absolute path, which is what fixes its final order rather than the roles above.

        The sublists under one key run from the highest version rank to the lowest. That
        order is read off the first file of each sublist after the path sort, which is
        not necessarily the data product the sublist was grouped by.

        The files themselves come from the class's ``OPUS_PRODUCTS`` table, which turns
        this file's logical path into wildcard patterns below this file's own holdings
        root. A pattern can carry an OPUS type of its own, and then every file it
        matches is filed under that type; a file matched by a pattern that carries none
        is filed under its own ``opus_type``. A product whose type comes out empty is
        logged as an error and is still filed, under the empty key.

        A second table, ``CROSS_PDS3_PDS4_PRODUCTS``, finds the same observation in the
        other PDS version's holdings. The other version is the first direct subclass of
        PdsFile that is not this one's, and its root is its first preloaded holdings
        directory if it has one, or this root with the holdings directory name
        substituted if it does not. If there is no such subclass, no cross-version file
        is added. Neither is any of them if **every** one of them is an index file,
        which is how an index whose data files are absent is kept out of the results.

        A label among the matched files is looked up in the link shelf to find the
        ``.fmt`` files it embeds. A missing or unreadable link shelf is logged as a
        warning and costs that label its ``.fmt`` files, not its place in the results,
        so the same call can return more files later once the shelf exists. A label is
        attached to at most one data product per key; a second product naming the same
        label gets a sublist holding only itself.

        A rule subclass that defines the ``opus_prioritizer`` hook is given the
        dictionary before any of the grouping and sorting above. Its return value is
        discarded here, so it takes effect only by mutating what it was passed, and any
        ordering it establishes among sublists of one version rank is replaced by the
        path sort.

        Returns:
            dict: the five-element key mapped to its list of sublists of PdsFile
            objects.
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
                label_pdsfiles[abspath] = [pdsf] + fmt_pdsfiles
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
