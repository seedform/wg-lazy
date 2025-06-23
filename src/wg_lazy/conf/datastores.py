"""Facility base for reading and writing app configuration."""

import logging
from io import IOBase
from pathlib import Path

from wg_lazy.utils import raise_as

from .base.datastore import (
    BaseConfigDataStore,
    ConfigDataStoreError,
)

LOG = logging.getLogger(__name__)


class FsConfigDataStore(BaseConfigDataStore):
    """Filesystem-based configuration file."""

    def __init__(self, path: Path | str):
        """Initialize this data store."""
        self.path = Path(path)

    # abstractmethod
    @raise_as(ConfigDataStoreError, catch=(OSError, ValueError))
    def exists(self) -> bool:
        """Return True if the file exists.

        Raises:
            ConfigDataStoreError: Failure to check for existence.
        """
        return self.path.exists() and self.path.is_file()

    def __open(self, mode) -> IOBase:
        return open(self.path, mode, encoding="utf-8")

    # abstractmethod
    @raise_as(ConfigDataStoreError, catch=OSError)
    def read(self) -> str:
        """Return file contents as a string.

        Raises:
            ConfigDataStoreError: Read failure.
        """
        with self.__open("rt") as stream:
            LOG.debug('reading from "%s"', self.path)
            return stream.read()

    # abstractmethod
    @raise_as(ConfigDataStoreError, catch=OSError)
    def write(self, data) -> int:
        """Write text to the file.

        Raises:
            ConfigDataStoreError: Write failure.
        """
        with self.__open("wt") as stream:
            LOG.debug('writing to "%s"', self.path)
            return stream.write(data)
