from __future__ import print_function, absolute_import, division

from errno import ENOENT
from time import time
from stat import S_IFDIR
import os
from os.path import realpath
from fcntl import LOCK_SH
from glob import glob
from threading import Lock
import logging
from fuse import FuseOSError

from pyfuse.metadata import (
    Files,
    GarbageCollector,
    Directories,
    Deletes,
    IdLinks,
    locking, fuse_metadata_dir
)
from pyfuse.fs.meta import get_lock_filename

logger = logging.getLogger(__name__)


class BaseFS:
    log = logger

    freeze_operation = (
        'write', 'truncate', 'create',
        'mkdir', 'release', 'rename',
        'rmdir', 'unlink',
    )

    skip_operation_log = ('read', 'write', 'getxattr')

    """Fuse up2p schedule put when file is updated (pyfuse.release)"""
    lstat_attr = ('st_atime', 'st_ctime', 'st_gid', 'st_mode',
                  'st_mtime', 'st_nlink', 'st_size', 'st_uid')
    statfs_attr = ('f_bavail', 'f_bfree', 'f_blocks', 'f_bsize',
                   'f_favail', 'f_ffree', 'f_files', 'f_flag',
                   'f_frsize', 'f_namemax')

    def __init__(self, root):
        self.rwlock = Lock()
        self.locks = {}
        self._clean_locks()
        self.root = realpath(root)

        self.files = Files()
        self.directories = Directories()
        self.deletes = Deletes()
        self.uid_links = IdLinks()
        self.garbage_collector = GarbageCollector()

        now = time()
        if '/' not in self.files:
            self.files['/'] = dict(st_mode=(S_IFDIR | 0o755), st_ctime=now,
                                   st_mtime=now, st_atime=now, st_nlink=2)
        if '/' not in self.directories:
            self.directories['/'] = set()

    def _get(self, path):
        realpath = self._realpath(path)

        if not os.path.isfile(realpath):
            raise FuseOSError(ENOENT)

        logger.debug('file %s exists on disk', path)
        return realpath

    def _clean_locks(self):
        if os.path.isdir(fuse_metadata_dir):
            regex = os.path.join(fuse_metadata_dir, "*.lock")
            lockfiles = filter(lambda x: x.endswith('.lock'), glob(regex))
            for lockfile in lockfiles:
                logger.info("Delete %s", lockfile)
                try:
                    os.unlink(lockfile)
                except Exception:
                    logger.warning('cannot clean lockfile "%s"', lockfile)

    def _remove_from_parent_directory(self, path):
        directories = set(self.directories[os.path.dirname(path)])
        directories.remove(os.path.basename(path))
        self.directories[os.path.dirname(path)] = directories

        now = time()

        tempfile_parent = self.files[os.path.dirname(path)]
        tempfile_parent.update(dict(st_mtime=now, st_atime=now, st_nlink=tempfile_parent['st_nlink'] - 1))
        self.files[os.path.dirname(path)] = tempfile_parent

    def _append_in_parent_directory(self, path):
        directories = set(self.directories[os.path.dirname(path)])
        directories.add(os.path.basename(path))
        self.directories[os.path.dirname(path)] = directories

        now = time()

        tempfile_parent = self.files[os.path.dirname(path)]
        tempfile_parent.update(dict(st_mtime=now, st_atime=now, st_nlink=tempfile_parent['st_nlink'] + 1))
        self.files[os.path.dirname(path)] = tempfile_parent

    def _realpath(self, path):
        return self.root + path

    def _rename_uid_link(self, uuid, old, new):
        if uuid in self.uid_links:
            temp = self.uid_links[uuid]
            temp.remove(old)
            temp.add(new)
            self.uid_links[uuid] = temp
        else:
            self.uid_links[uuid] = {new}

    def __call__(self, op, path, *args):
        if op not in self.skip_operation_log:
            self.log.debug('-> %s %s %s', op, path, repr(args))
        ret = '[Unhandled Exception]'
        try:
            if op in self.freeze_operation:
                fuse_freeze_file = get_lock_filename()
                with locking(fuse_freeze_file, LOCK_SH):
                    ret = getattr(self, op)(path, *args)
            else:
                ret = getattr(self, op)(path, *args)
            return ret
        except OSError as e:
            ret = str(e)
            raise
        except Exception:
            logger.exception('Unhandled Exception')
            raise
        finally:
            if op not in self.skip_operation_log:
                self.log.debug('<- %s %s', op, repr(ret))
