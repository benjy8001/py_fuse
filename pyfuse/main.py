#!/usr/bin/env python3
# coding: utf-8

"""py-fuse

Usage:
    py-fuse
    py-fuse <root> <mountpoint>
    py-fuse get-default-mountpoint
    py-fuse get-default-root
    py-fuse get-default-metadata

Options:
    -h --help            Show this screen
"""

from __future__ import print_function, absolute_import, division

import sys
import os
import logging
from docopt import docopt

from pyfuse.constants import (
    FUSE_METADATA_DIR,
    FUSE_MOUNTPOINT,
    FUSE_ROOT,
)
from pyfuse import run

logging.basicConfig(filename='logs.log', level=logging.DEBUG)
logger = logging.getLogger(__name__)

fuse_root = FUSE_ROOT
fuse_mountpoint = FUSE_MOUNTPOINT
fuse_metadata_dir = FUSE_METADATA_DIR


def main():
    arguments = docopt(__doc__, version='py-fuse 0.1')

    if arguments['get-default-mountpoint']:
        print(fuse_mountpoint)
        sys.exit(0)

    if arguments['get-default-root']:
        print(fuse_root)
        sys.exit(0)

    if arguments['get-default-metadata']:
        print(fuse_metadata_dir)
        sys.exit(0)

    root = os.path.abspath(arguments['<root>']) if arguments['<root>'] else fuse_root
    mountpoint = os.path.abspath(arguments['<mountpoint>']) if arguments['<mountpoint>'] else fuse_mountpoint
    os.makedirs(root, exist_ok=True)
    os.makedirs(mountpoint, exist_ok=True)

    run(root, mountpoint)


if __name__ == '__main__':
    main()
