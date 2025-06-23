"""Configuration file format base."""

from abc import ABC, abstractmethod

from .models import ConfigRoot


class ConfigParserError(Exception):
    """Raised by BaseConfigParser implementations."""


class BaseConfigParser(ABC):
    """Configuration parser interface."""

    @abstractmethod
    def parse(self, data: str) -> ConfigRoot:
        """Parse a string to create a ConfigRoot instance.

        Args:
            data: Configuration data as a string.

        Returns:
            A ConfigRoot instance created from parsed data.

        Raises:
            ConfigParserError: Invalid input data.
        """
