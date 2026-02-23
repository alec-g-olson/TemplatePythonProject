106: Enforce Source Resource Folder Mapping
===========================================

Overview
--------
Add process and cache enforcement so source files that load committed resources have a
fixed, predictable resource directory location. This lets the build system reliably
rerun impacted tests when source resource files are updated, added, or deleted.

Requirements
------------
- Source resource directories must follow a strict naming convention derived from the
  corresponding source file name.
- Process enforcement must fail when a non-package source directory does not map to a
  matching source file resource directory.
- Unit test selection must rerun a source file's unit test when its source resource
  directory changes.
- Feature test selection must rerun feature tests when any source resource directory in
  the subproject changes.

Acceptance Criteria / Feature Tests
-----------------------------------
- Non-package source directories that are not named ``{src_file_stem}_resources`` fail
  process enforcement.
- A source resource update causes the corresponding unit test to be selected for rerun.
- A source resource update causes feature tests in the affected subproject to be
  selected for rerun.
- Source resource additions and deletions are detected by cache invalidation logic.
