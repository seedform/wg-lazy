"""App configuration format."""


import json

from pydantic import ValidationError

from wg_lazy.utils import raise_as

from ..base import (
    BaseConfigFormat,
    ConfigFormatError,
    ConfigRoot,
)


class JsonConfigFormat(BaseConfigFormat):
    """App configuration parser and formatter."""

    # TODO: see if it's possible to switch back to model_validate_json
    # abstractmethod
    @raise_as(ConfigFormatError, catch=(ValidationError, json.JSONDecodeError))
    def parse(self, data: str) -> ConfigRoot:
        """Parse JSON app configuration.

        Args:
            data: App configuration as a JSON string.

        Returns:
            A ConfigRoot instance created from parsed data.

        Raises:
            ConfigFormatError: Invalid configuration data in string.
        """
        try:
            config_dict = json.loads(data)
            return ConfigRoot(**config_dict)
        except json.JSONDecodeError as de:
            raise ConfigFormatError(f"invalid configuration: {str(de)}")
        # return ConfigRoot.model_validate_json(data, strict=True)

    # abstractmethod
    def format(self, config: ConfigRoot) -> str:
        """Format a ConfigRoot instance into a JSON string."""
        formatted = config.model_dump_json(
            by_alias=True, indent=2, exclude_none=True
        )
        return f"{formatted}\n"
