"""New configuration generation command."""

import logging

from wg_lazy.conf import (
    ConfigDataStoreError,
    ConfigRoot,
    ConfigValidationError,
)
from wg_lazy.consts import defaults
from wg_lazy.utils import PublicHostPort, raise_as

from .base import BaseCommand, CommandError

LOG = logging.getLogger(__name__)


class New(BaseCommand):
    """Generate a new WireGuard tunnel and configuration."""

    @raise_as(CommandError, catch=(ValueError, ConfigDataStoreError))
    def __init__(
        self,
        *args,
        endpoint: str = defaults.ENDPOINT,
        listen_port: int = defaults.LISTEN_PORT,
        dns: str = defaults.DNS,
        force: bool = False,
        **kwargs,
    ):
        """Initialize command.

        Args:
            endpoint: Tunnel public address.
            listen_port: WireGuard listen port.
            dns: DNS server address to provide to peers.
            force: Overwrite if configuration already exists.
            args: Positional args sent to parent class.
            kwargs: Keyword args sent to parent class.

        Raises:
            CommandError: Initialization failure.
        """
        super().__init__(*args, **kwargs)
        self.endpoint = PublicHostPort(endpoint)
        self.listen_port = listen_port
        self.dns = dns
        self.force = force

    @raise_as(CommandError, catch=ConfigDataStoreError)
    def _check_config_exists(self):
        app_config_exists = self.app_config_service.exists()
        wg_config_exists = self.wg_config_service.exists()
        exists = app_config_exists or wg_config_exists
        if exists and not self.force:
            msg = (
                f"configuration for {self.interface_name} "
                "already exists; use --force to overwrite"
            )
            raise CommandError(msg)
        elif exists and self.force:
            LOG.warning(
                "overwriting existing configuration for %s",
                self.interface_name,
            )

    # abstractmethod
    @raise_as(
        CommandError, catch=(ConfigValidationError, ConfigDataStoreError)
    )
    def run(self):
        """Run this command."""
        LOG.debug("checking for existing configuration")
        self._check_config_exists()
        LOG.info(
            "creating new configuration for WireGuard interface: %s",
            self.interface_name,
        )
        config = ConfigRoot(
            endpoint=str(self.endpoint),
            listen_port=self.listen_port,
            dns=self.dns,
        )
        LOG.debug("created configuration: %s", str(config))
        self.sync(config)
