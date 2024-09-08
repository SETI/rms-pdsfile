#!/usr/bin/env python3
################################################################################
# # shelf-consistency-check.py
#
# Syntax:
#   shelf-consistency-check.py [--verbose] shelf_root [shelf_root ...]
# 
# Confirm that every info shelf file has a corresponding directory in holdings/.
################################################################################

import os, sys

paths = sys.argv[1:]

# Look for --verbose option
if '--verbose' in paths:
    paths.remove('--verbose')
    verbose = True
else:
    verbose = False

# Traverse each directory tree...
errors = 0
tests = 0
for path in paths:
  for root, dirs, files in os.walk(path):

    # Ignore anything not inside a shelves directory
    if 'shelves' not in root: continue
    if root.endswith('shelves'): continue

    # Confirm it is one of the expected subdirectories
    tail = root.partition('shelves/')[-1]
    tail = tail.partition('/')[0]
    if tail not in ('info', 'links', 'index'):
        print('*** Not a valid shelves directory: ' + root)
        errors += 1
        tests += 1
        continue

    # Check each file...
    for name in files:
        shelf_path = os.path.join(root, name)
        tests += 1

        if name == '.DS_Store':
            continue

        # Check the file extension
        if not (name.endswith('.py') or name.endswith('.pickle')):
            print('*** Extraneous file found: ' + shelf_path)
            errors += 1
            continue

        # Convert to the associated holdings path
        holdings_path = shelf_path.replace('shelves/' + tail, 'holdings')
        holdings_path = holdings_path.rpartition('.')[0]

        # For index shelves, make sure the holdings label file exists
        if tail == 'index':
            if not os.path.exists(holdings_path + '.lbl'):
                print('*** Extraneous shelf: ' + shelf_path)
                error += 1
                continue

            if verbose:
                print(holdings_path)

        # For info and link shelves, make sure the holdings directory exists
        else:
            holdings_path = holdings_path.rpartition('_')[0]
            if not os.path.exists(holdings_path):
                print('*** Extraneous shelf: ' + shelf_path)
                errors += 1
                continue

            if verbose:
                print(holdings_path)

# Summarize
print('Tests performed: %d' % tests)
print('Errors found: %d' % errors)

if errors:
    sys.exit(1)

################################################################################
