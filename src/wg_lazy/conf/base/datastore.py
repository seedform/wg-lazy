"""Configuration data store base."""

from abc import ABC, abstractmethod


class ConfigDataStoreError(Exception):
    """Raised by BaseConfigDataStore implementations."""


class BaseConfigDataStore(ABC):
    """Persistence layer interface for configuration data.

    Failed operations must raise ConfigDataStoreError.
    """

    @abstractmethod
    def exists(self) -> bool:
        """Return True if the backing storage exists.

        Raises:
            ConfigDataStoreError: Failure to check for existence.
        """

    @abstractmethod
    def read(self) -> str:
        """Return contents as a string.

        Raises:
            ConfigDataStoreError: Read failure.
        """

    @abstractmethod
    def write(self, data: str) -> int:
        """Write text to the backing storage.

        Raises:
            ConfigDataStoreError: Write failure.
        """
