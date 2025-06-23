"""Base command classes."""

import logging
from abc import ABC, abstractmethod

from wg_lazy.conf import (
    AppConfigService,
    ConfigDataStoreError,
    ConfigFormatError,
    ConfigRoot,
    WgConfigService,
)
from wg_lazy.consts import defaults
from wg_lazy.utils import raise_as

LOG = logging.getLogger(__name__)


class CommandError(Exception):
    """Raised if initializing or running a command fails."""


class BaseCommand(ABC):
    """Base class for individual commands.

    Child classes are expected to call super().__init__() first
    and then proceed with initialization.

    Attributes:
        app_config_service: App configuration file service.
        wg_config_service: WireGuard configuration file service.
        interface_name: Name of the WireGuard interface to configure.
    """

    def __init__(
        self,
        app_config_service: AppConfigService,
        wg_config_service: WgConfigService,
        interface_name: str = defaults.WG_INTERFACE,
        **kwargs,
    ):
        """Initialize the command base.

        Args:
            app_config_service: App configuration file service.
            wg_config_service: WireGuard configuration file service.
            interface_name: WireGuard interface name.
            kwargs: catch-all keyword arguments that can be ignored.
        """
        self.app_config_service = app_config_service
        self.wg_config_service = wg_config_service
        self.interface_name = interface_name

    @abstractmethod
    def run(self):
        """Run this command.

        Raises:
            CommandError: Failed to run or complete command.
        """

    @raise_as(
        CommandError,
        catch=(
            ConfigDataStoreError,
            ConfigFormatError,
        ),
    )
    def sync(self, config: ConfigRoot):
        """Synchronize WireGuard configuration with app configuration.

        Args:
            config: ConfigRoot instance to provide to both app and
                WireGuard configuration services.

        Raises:
            CommandError: Failed to synchronize configuration.
        """
        LOG.info("writing app configuration")
        self.app_config_service.write(config)
        LOG.info("writing WireGuard configuration")
        self.wg_config_service.write(config)
