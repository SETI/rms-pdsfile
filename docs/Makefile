# Minimal makefile for Sphinx documentation.
#
# `make html` builds docs/_build/html. Pass flags through SPHINXOPTS and choose a
# different output tree through BUILDDIR:
#
#     make html SPHINXOPTS="-W"
#     make html SPHINXOPTS="-n -W" BUILDDIR=_build/nitpicky
#
# Two builds that share a BUILDDIR share its doctree cache, and Sphinx re-reads only
# what has changed, so the second one reports nothing. `make clean` empties BUILDDIR;
# a separate BUILDDIR is what makes a second set of flags a second full build.

SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
