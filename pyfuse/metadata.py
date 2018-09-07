import os
import shelve
from contextlib import closing
from fcntl import LOCK_SH, LOCK_EX
import logging

from pyfuse.constants import (
    FUSE_METADATA_DIR,
    FUSE_ACQUIRE_LOCK_TIMEOUT,
)
from pyfuse.lock import locking

logger = logging.getLogger(__name__)


fuse_metadata_dir = FUSE_METADATA_DIR
TIMEOUT = FUSE_ACQUIRE_LOCK_TIMEOUT


class UMetadata:
    __utypes__ = (
        'Files',
        'Directories',
        'Deletes',
        'GarbageCollector',
        'IdLinks',
    )
    __extension__ = '.db'

    def __init__(self, utype, metadata_path=None):
        if utype not in self.__utypes__:
            raise TypeError('utype (%s) must be in: %s' % (utype, self.__utypes__))
        if metadata_path:
            self.__metadata_path__ = metadata_path
        else:
            self.__metadata_path__ = FUSE_METADATA_DIR
        os.makedirs(self.__metadata_path__, exist_ok=True)
        self.metadata_file = os.path.join(self.__metadata_path__, utype)

    def __setitem__(self, key, item):
        with locking("%s.lock" % self.metadata_file, LOCK_EX, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                database[key] = item  # pylint: disable=E1137

    def __getitem__(self, key):
        with locking("%s.lock" % self.metadata_file, LOCK_SH, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                result = database[key]  # pylint: disable=E1136
        return result

    def __delitem__(self, key):
        with locking("%s.lock" % self.metadata_file, LOCK_EX, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                del database[key]  # pylint: disable=E1138

    def pop(self, *args):
        with locking("%s.lock" % self.metadata_file, LOCK_EX, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                result = database.pop(*args)  # pylint: disable=E1101
        return result

    def __contains__(self, item):
        with locking("%s.lock" % self.metadata_file, LOCK_SH, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                result = item in database  # pylint: disable=E1135
        return result

    def __iter__(self):
        with locking("%s.lock" % self.metadata_file, LOCK_SH, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                for k in database.keys():  # pylint: disable=E1101
                    yield (k, database[k])  # pylint: disable=E1136

    def items(self):
        with locking("%s.lock" % self.metadata_file, LOCK_SH, timeout=TIMEOUT):
            with closing(shelve.open(self.metadata_file)) as database:
                for k in database.keys():  # pylint: disable=E1101
                    yield (k, database[k])  # pylint: disable=E1136


class Files(UMetadata):
    def __init__(self, metadata_path=None):
        super().__init__(self.__class__.__name__, metadata_path)


class Directories(UMetadata):
    def __init__(self, metadata_path=None):
        super().__init__(self.__class__.__name__, metadata_path)


class Deletes(UMetadata):
    def __init__(self, metadata_path=None):
        super().__init__(self.__class__.__name__, metadata_path)


class GarbageCollector(UMetadata):
    def __init__(self, metadata_path=None):
        super().__init__(self.__class__.__name__, metadata_path)


class IdLinks(UMetadata):
    def __init__(self, metadata_path=None):
        super().__init__(self.__class__.__name__, metadata_path)
