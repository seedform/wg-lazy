"""Configuration file format base."""

from abc import ABC, abstractmethod

from .models import ConfigRoot


class ConfigFormatterError(Exception):
    """Raised by BaseConfigFormatter implementations."""


# TODO: ConfigFormatterError may not be needed...
class BaseConfigFormatter(ABC):
    """Configuration formatter abstract class."""

    @abstractmethod
    def format(self, config: ConfigRoot) -> str:
        """Format a ConfigRoot instance into a string.

        Args:
            config: A valid ConfigRoot instance.

        Raises:
            ConfigFormatterError: Incomplete or invalid configuration.
        """
