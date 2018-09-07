import os

SEPARATOR = ","

FUSE_METADATA_DIR = "/var/lib/fuse/metadata"
FUSE_MOUNTPOINT = "/mnt/user/fuse/mountpoint"
FUSE_ROOT = "/mnt/user/fuse/root"
FUSE_ACQUIRE_LOCK_TIMEOUT = 0

FUSE_FREEZE_FILE_TIMEOUT = 300
FUSE_EXCLUDES_ROOT_DIRECTORIES = SEPARATOR.join([os.path.join("s3", ".minio.sys")])

DEFAULT_TIMEOUT = 0

DEFAULT_MINIO_METADATA_EXCLUDES = SEPARATOR.join(("tmp*", "multipart"))

DEFAULT_HASH_TYPE_FILE = "sha1"
DEFAULT_HASH_TYPE_SECURE = "sha1"
