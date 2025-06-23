"""New peer command."""

import logging

from wg_lazy.conf import (
    ConfigDataStoreError,
    ConfigFormatError,
)
from wg_lazy.utils import raise_as

from .base import BaseCommand, CommandError

LOG = logging.getLogger(__name__)


class Rm(BaseCommand):
    """Remove a peer from an existing tunnel."""

    @raise_as(CommandError, catch=(ValueError, ConfigDataStoreError))
    def __init__(
        self,
        *args,
        peer_name=None,
        force=False,
        **kwargs,
    ):
        """Initialize command.

        Args:
            peer_name: Name of the peer to be deleted.
            force: Delete without confirmation.
            args: Positional args sent to parent class.
            kwargs: Keyword args sent to parent class.

        Raises:
            CommandError: Initialization failure.
        """
        super().__init__(*args, **kwargs)
        self.peer_name = peer_name

    @raise_as(CommandError, catch=ConfigDataStoreError)
    def _check_config_exists(self):
        if not self.app_config_service.exists():
            msg = (
                "app configuration not found for interface: "
                f"{self.interface_name}"
            )
            raise CommandError(msg)

    # overridden
    @raise_as(CommandError, catch=(ConfigDataStoreError, ConfigFormatError))
    def run(self):
        """Run this command."""
        LOG.debug("checking for existing configuration")
        self._check_config_exists()
        LOG.info(
            "reading app configuration for WireGuard interface: %s",
            self.interface_name,
        )
        config = self.app_config_service.read()

        LOG.info("searching for peer with name: %s", self.peer_name)
        peer = config.get_peer_by_name(self.peer_name)
        if not peer:
            raise CommandError(f"peer not found: {self.peer_name}")

        LOG.info("removing peer: %s", self.peer_name)
        config.remove_peer(peer)
        LOG.debug("removed peer: %s", peer)

        self.sync(config)
