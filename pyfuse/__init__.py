from __future__ import print_function, absolute_import, division

from time import time
from errno import EACCES, ENOENT, EEXIST, ENODATA, ENOTEMPTY
from stat import S_IFLNK
import os
import logging
from uuid import uuid4
from threading import Lock

from fuse import FUSE, FuseOSError, Operations

from pyfuse.exceptions import (
    DirectoryAlreadyMounted,
)

from pyfuse.fs.meta import get_state, set_state, remove_uid_link
from pyfuse.fs import BaseFS


logger = logging.getLogger(__name__)


class PyFuse(BaseFS, Operations):
    logger.debug('OK')
    def access(self, path, mode):  # pylint: disable=W0221
        real_path = self._realpath(path)
        if not os.path.isfile(real_path):
            return
        if not os.access(real_path, mode):
            raise FuseOSError(EACCES)

    def chmod(self, path, mode):
        real_path = self._realpath(path)
        if os.path.exists(real_path):
            os.chmod(real_path, mode)
        tempfile = self.files[path]
        tempfile['st_mode'] &= 0o770000
        tempfile['st_mode'] |= mode
        self.files[path] = tempfile

    def chown(self, path, uid, gid):
        real_path = self._realpath(path)
        if os.path.exists(real_path):
            os.chown(real_path, uid, gid)
        tempfile = self.files[path]
        tempfile['st_uid'] = uid
        tempfile['st_gid'] = gid
        self.files[path] = tempfile

    def create(self, path, mode, fi=None):
        real_path = self._realpath(path)
        os.makedirs(os.path.dirname(real_path), exist_ok=True)
        new_file = os.open(real_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
        self._append_in_parent_directory(path)

        lstat_tmp = os.lstat(real_path)

        lstat = {k: getattr(lstat_tmp, k) for k in self.lstat_attr}
        lstat['uuid'] = None
        lstat['tmp_uuid'] = str(uuid4())
        logger.info('create:  %s (%s): %s', path, mode, lstat)
        self.files[path] = lstat
        self.locks[path] = Lock()

        set_state(path, 'writing', True)
        return new_file

    def flush(self, path, fh):
        return os.fsync(fh)

    def fsync(self, path, datasync, fh):
        if datasync != 0:
            return os.fdatasync(fh)
        else:
            return os.fsync(fh)

    def getattr(self, path, fh=None):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        real_path = self._realpath(path)
        if os.path.isfile(real_path):
            lstat = os.lstat(real_path)
            return {k: getattr(lstat, k) for k in self.lstat_attr}

        tempfile = self.files[path]
        return {k: tempfile[k] for k in self.lstat_attr if k in tempfile}

    def fgetattr(self, path, stat=None, fi=None):  # pylint: disable=W0613
        return self.getattr(path)

    def getxattr(self, path, name, position=0):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        tempfile = self.files[path]
        attrs = tempfile.get('attrs', {})
        try:
            return attrs[name]
        except KeyError:
            raise FuseOSError(ENODATA)

    def listxattr(self, path):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        attrs = self.files[path].get('attrs', {})
        return attrs.keys()

    def removexattr(self, path, name):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        tempfile = self.files[path]
        attrs = tempfile.get('attrs', {})
        try:
            del attrs[name]
            self.files[path] = tempfile
        except KeyError:
            raise FuseOSError(ENODATA)

    def setxattr(self, path, name, value, options, position=0):
        if path not in self.files:
            raise FuseOSError(ENOENT)

        tempfile = self.files[path]
        tempfile.setdefault('attrs', {})
        tempfile['attrs'][name] = value
        self.files[path] = tempfile

        real_path = self._realpath(path)
        if os.path.isfile(real_path):
            try:
                os.setxattr(real_path, name, value, options)
            except Exception:
                pass

    def link(self, target, source):
        return os.link(self._realpath(source), target)

    def mkdir(self, path, mode):
        real_path = self._realpath(path)
        if path in self.directories:
            raise FuseOSError(EEXIST)

        os.makedirs(real_path, mode, exist_ok=True)

        self._append_in_parent_directory(path)

        self.directories[path] = set()

        lstat_tmp = os.lstat(real_path)
        lstat = {k: getattr(lstat_tmp, k) for k in self.lstat_attr}
        logger.info('%s (%s): %s', path, mode, lstat)
        self.files[path] = lstat

    def mknod(self, path, mode, dev):
        return os.mknod(self._realpath(path), mode, dev)

    def open(self, path, flags):
        self.locks[path] = Lock()
        real_path = self._get(path)

        if ((flags & os.O_RDWR) or (flags & os.O_WRONLY) or (flags & os.O_APPEND)):
            tempfile = self.files[path]
            logger.debug('%s opened in write mode', path)
            tempfile['tmp_uuid'] = str(uuid4())
            self.files[path] = tempfile

            set_state(path, 'writing', True)
            set_state(path, 'failed', False)
        else:
            logger.debug('%s opened in read mode', path)

        return os.open(real_path, flags)

    def read(self, path, size, offset, fh):
        with self.locks.get(path, self.rwlock):
            os.lseek(fh, offset, os.SEEK_SET)
            return os.read(fh, size)

    def readdir(self, path, fh):
        return ['.', '..'] + list(self.directories[path])

    def readlink(self, path):
        pathname = os.readlink(self._realpath(path))
        if pathname.startswith("/"):
            # Path name is absolute, sanitize it.
            return os.path.relpath(pathname, self.root)
        else:
            return pathname

    def release(self, path, fh):
        close_status = os.close(fh)

        real_path = self._realpath(path)
        lstat_tmp = os.lstat(real_path)
        lstat = {k: getattr(lstat_tmp, k) for k in self.lstat_attr}

        tempfile = self.files[path]
        tempfile.update(lstat)

        is_writing = get_state(path, 'writing')
        self.files[path] = tempfile

        set_state(path, 'writing', False)

        if path in self.locks:
            del self.locks[path]

        return close_status

    def rec_rename_directory(self, old, new):
        if new not in self.directories and old in self.directories:
            self.directories[new] = self.directories.pop(old)
            logger.debug('metadata rec directories %s -> %s', old, new)

        if new not in self.directories:
            return

        for sub_path in self.directories[new]:
            new_path = os.path.join(new, sub_path)
            old_path = os.path.join(old, sub_path)

            if new_path not in self.files and old_path in self.files:
                self.files[new_path] = self.files.pop(old_path)
                uuid = self.files[new_path].get('uuid', '')
                if uuid:
                    self._rename_uid_link(uuid, self._realpath(old_path), self._realpath(new_path))
                logger.debug('metadata rec files %s -> %s', old_path, new_path)
            if new_path not in self.directories and old_path in self.directories:
                self.directories[new_path] = self.directories.pop(old_path)
                logger.debug('metadata rec directories %s -> %s', old_path, new_path)
                self.rec_rename_directory(old_path, new_path)

    def rename(self, old, new):
        new_realpath = self._realpath(new)
        old_realpath = self._realpath(old)
        if os.path.exists(old_realpath):
            os.rename(old_realpath, new_realpath)
            logger.debug('rename %s -> %s on %s', old, new, self.root)

        if old not in self.files:
            raise FuseOSError(ENOENT)

        self._remove_from_parent_directory(old)
        self._append_in_parent_directory(new)
        self.files[new] = self.files.pop(old)
        uuid = self.files[new].get('uuid', '')
        if uuid:
            self._rename_uid_link(uuid, old_realpath, new_realpath)
        logger.debug('metadata files %s -> %s', old, new)

        if old in self.directories:
            self.rec_rename_directory(old, new)

    def rmdir(self, path):
        real_path = self._realpath(path)
        self.deletes[real_path] = None

        if self.directories[path]:
            raise FuseOSError(ENOTEMPTY)

        self._remove_from_parent_directory(path)
        self.directories.pop(path)
        self.files.pop(path)
        if os.path.isdir(real_path):
            os.rmdir(real_path)

    def statfs(self, path):
        stv = os.statvfs(self._realpath(path))
        return dict((key, getattr(stv, key)) for key in self.statfs_attr)

    def symlink(self, target, source):
        f = os.symlink(self._realpath(source), self._realpath(target))
        self.files[target] = dict(st_mode=(S_IFLNK | 0o777), st_nlink=1,
                                  st_size=len(source))
        self._append_in_parent_directory(target)
        return f

    def truncate(self, path, length, fh=None):
        tempfile = self.files[path]
        if tempfile['st_size'] != length:
            tempfile['st_size'] = length
            tempfile['st_mtime'] = time()
        tempfile['st_atime'] = time()
        self.files[path] = tempfile

        real_path = self._realpath(path)
        if os.path.isfile(real_path):
            with open(real_path, 'r+') as truncate_file:
                truncate_file.truncate(length)

    def unlink(self, path):
        real_path = self._realpath(path)
        descriptor = None
        if os.path.islink(real_path):
            descriptor = os.unlink(real_path)
        self._remove_from_parent_directory(path)
        tmpfile = self.files.pop(path)
        uuid = tmpfile.get('uuid', '')
        # uuid can be None
        if uuid:
            remove_uid_link(uuid, real_path)
            if not self.uid_links[uuid]:
                logger.debug('add %s (%s) to UDeletes', uuid, real_path)
                self.deletes[real_path] = uuid

        # we unlink file on root
        if os.path.exists(real_path):
            os.unlink(real_path)

        return descriptor

    def utimens(self, path, times=None):
        now = time()
        atime, mtime = times if times else (now, now)
        tempfile = self.files[path]
        tempfile['st_atime'] = atime
        tempfile['st_mtime'] = mtime
        self.files[path] = tempfile

    def write(self, path, data, offset, fh):
        with self.locks.get(path, self.rwlock):
            os.lseek(fh, offset, os.SEEK_SET)
            return os.write(fh, data)


def run(root, mountpoint):
    if os.path.ismount(mountpoint):
        raise DirectoryAlreadyMounted(mountpoint)

    FUSE(PyFuse(root), mountpoint, debug=True, foreground=True, nonempty=True,
         allow_other=True, nothreads=False, big_writes=True,
         max_read=131072, max_write=131072)
