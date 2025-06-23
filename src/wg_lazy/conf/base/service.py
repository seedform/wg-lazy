"""Base configuration service."""

from abc import ABC

from .datastore import BaseConfigDataStore
from .format import BaseConfigFormat
from .models import ConfigRoot


class BaseConfigService(ABC):
    """Monolithic facade for managing configuration.

    Composed of a data store and format which use model objects defined
    in `wg_lazy.conf.base.models`.
    """

    def __init__(
        self,
        config_ds: BaseConfigDataStore,
        config_fmt: BaseConfigFormat,
    ):
        """Initialize this configuration file facility."""
        self._config_ds = config_ds
        self._config_fmt = config_fmt

    def exists(self) -> bool:
        """Return True if the configuration file exists.

        Useful for checking if an existing file will be overwritten.

        Returns:
            True if file exists.

        Raises:
            ConfigDataStoreError: Failed to check existence.
        """
        return self._config_ds.exists()

    def read(self) -> ConfigRoot:
        """Read and produce a Config from the backing data store.

        Raises:
            ConfigDataStoreError: Failed to read from data store.
            ConfigFormatError: Failed to parse configuration.

        Returns:
            A ConfigRoot instance based on the parsed content.
        """
        data = self._config_ds.read()
        return self._config_fmt.parse(data)

    def write(self, config: ConfigRoot) -> int:
        """Write a ConfigRoot instance to the data store.

        Args:
            config: A ConfigRoot instance.

        Raises:
            ConfigFormatError: Failed to format configuration.
            ConfigDataStoreError: Failed to write to data store.

        Returns:
            The number of characters written.
        """
        data = self._config_fmt.format(config)
        return self._config_ds.write(data)
