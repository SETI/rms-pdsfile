Developer Guide
===============

This guide is for people who modify, extend, test or release ``rms-pdsfile`` itself:
how the code is organized, how the pieces cooperate, and how to work on it safely. It
assumes a competent Python developer who is new to this codebase. A user of the
command-line programs wants the :doc:`/user_guide/user_guide` instead, and a caller of
the library API wants the :doc:`/api/index`, which these chapters cross-reference
throughout.

.. toctree::
   :maxdepth: 2

   dev_guide_repository_layout
   dev_guide_architecture
   dev_guide_subsystems
   dev_guide_extending_rules
   dev_guide_extending_tools
   dev_guide_testing
   dev_guide_goldens
   dev_guide_ci
