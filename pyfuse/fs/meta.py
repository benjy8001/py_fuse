from __future__ import print_function, absolute_import, division

import os
import logging


from pyfuse.exceptions import UnknownKey
from pyfuse.constants import (
    FUSE_METADATA_DIR,
)
from pyfuse.metadata import (
    Files,
    Deletes,
    IdLinks,
)

logger = logging.getLogger(__name__)


def get_lock_filename():
    fuse_metadata_dir = FUSE_METADATA_DIR
    return "%s.lock" % os.path.join(fuse_metadata_dir, 'fuse')


def update_file_uuid(path, uuid):
    files = Files()

    if path in files:
        tempfile = files[path]
        tempfile['uuid'] = uuid
        files[path] = tempfile
        logger.debug('update file uuid (path %s, uuid path, %s)', path, uuid)
    else:
        logger.exception("Cannot update uuid of file '%s'", path)


def file_is_modified(key, uuid):
    files = Files()
    if key not in files:
        logger.exception("Cannot know if file is modified '%s'", key)
        raise UnknownKey(key)

    f = files[key]

    if f['tmp_uuid']:  # case of file open in write mode
        if uuid != f['tmp_uuid']:
            return True
    return f['uuid'] != uuid


def add_uid_link(uuid, realpath):
    uid_links = IdLinks()
    deletes = Deletes()

    logger.debug('add link uuid: %s, realpath: %s', uuid, realpath)
    if uuid not in uid_links:
        uid_links[uuid] = {realpath}  # not use set()
    else:
        temp = uid_links[uuid]
        temp.add(realpath)
        uid_links[uuid] = temp

    d = dict(deletes.items())
    for realpath_to_delete, uuid_to_delete in d.items():
        if uuid_to_delete == uuid:
            del deletes[realpath_to_delete]


def remove_uid_link(uuid, realpath):
    if not uuid:
        logger.warning('cannot remove link for not initialized uuid for realpath: %s', realpath)
        return

    uid_links = IdLinks()

    logger.debug('remove link uuid: %s, realpath: %s', uuid, realpath)
    if uuid in uid_links:
        temp = uid_links[uuid]
        if realpath in temp:  # not symlink
            temp.remove(realpath)
            uid_links[uuid] = temp
    else:
        uid_links[uuid] = set()


def set_state(path, state, value):
    files = Files()
    if path not in files:
        logger.warning('%s set state failed %s -> %s', path, state, bool(value))
        return

    tempfile = files[path]
    tempfile[state] = bool(value)
    files[path] = tempfile

    logger.debug('%s set state %s -> %s', path, state, bool(value))


def get_state(path, state):
    files = Files()
    if path not in files:
        return False

    tempfile = files[path]

    return tempfile.get(state, False)
