class Error(Exception):
    """Base class for exceptions in this module."""
    pass


class DirectoryAlreadyMounted(Error):
    """Fuse mountpoint already mounted"""
    pass


class UnknownKey(Error):
    """If metadata key doesn't exists"""
    pass


errno = {
    'Error': 1,
    'DirectoryAlreadyMounted': 2,
    'UnknownKey': 3,
}
