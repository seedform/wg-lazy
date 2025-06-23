"""Configuration file format base."""

from abc import ABC, abstractmethod

from .models import ConfigRoot


class ConfigFormatError(Exception):
    """Raised by BaseConfigFormat implementations."""


class BaseConfigFormat(ABC):
    """Configuration parser and formatter.

    Failed operations must raise ConfigFormatError.
    """

    @abstractmethod
    def parse(self, data: str) -> ConfigRoot:
        """Parse a string to create a ConfigRoot instance.

        Args:
            data: Configuration data as a string.

        Returns:
            A ConfigRoot instance created from parsed data.

        Raises:
            ConfigFormatError: Invalid input data.
        """

    @abstractmethod
    def format(self, config: ConfigRoot) -> str:
        """Format a ConfigRoot instance into a string.

        Raises:
            ConfigFormatError: Incomplete or invalid configuration.
        """
