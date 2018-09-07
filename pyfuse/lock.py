from contextlib import contextmanager
from fcntl import flock, LOCK_UN, LOCK_NB
from time import sleep


@contextmanager
def locking(filename, lock_type, timeout=None):
    file_descriptor = open(filename, 'w')
    # try to acquire the lock
    if timeout:
        for _ in range(int(timeout * 10)):
            try:
                flock(file_descriptor.fileno(), lock_type | LOCK_NB)
                break
            except IOError:
                pass
            sleep(0.1)
        else:
            file_descriptor.close()
            raise IOError('Unable to acquire lock for %s' % filename)
    else:
        flock(file_descriptor.fileno(), lock_type)

    # execute the main function
    try:
        # ... right here
        yield
    finally:
        flock(file_descriptor.fileno(), LOCK_UN)  # release
        file_descriptor.close()  # release the lock by closing the file
