"""Show configuration command."""

import logging
from inspect import cleandoc

from wg_lazy.conf import (
    ConfigDataStoreError,
    ConfigFormatError,
    PeerValidationError,
)
from wg_lazy.utils import (
    mask,
    pubkey,
    raise_as,
    seconds_to_date_time,
)

from .base import BaseCommand, CommandError

LOG = logging.getLogger(__name__)


# TODO: add args for search


class Show(BaseCommand):
    """Show tunnel details and peers."""

    @raise_as(CommandError, catch=(ConfigDataStoreError,))
    def __init__(self, *args, **kwargs):
        """Initialize command.

        Args:
            args: Positional args sent to parent class.
            kwargs: Keyword args sent to parent class.

        Raises:
            CommandError: Initialization failure.
        """
        super().__init__(*args, **kwargs)

    @raise_as(CommandError, catch=ConfigDataStoreError)
    def _check_config_exists(self):
        app_config_exists = self.app_config_service.exists()
        wg_config_exists = self.wg_config_service.exists()
        if not app_config_exists:
            msg = (
                "app configuration not found for interface: "
                f"{self.interface_name}"
            )
            raise CommandError(msg)
        if not wg_config_exists:
            msg_tpl = (
                "app configuration exists but corresponding WireGuard "
                "configuration not found for interface: %s"
            )
            LOG.warning(msg_tpl, self.interface_name)

    # overridden
    @raise_as(
        CommandError,
        catch=(PeerValidationError, ConfigDataStoreError, ConfigFormatError),
    )
    def run(self):
        """Run this command."""
        LOG.debug("checking for existing configuration")
        self._check_config_exists()
        LOG.info(
            "reading app configuration for WireGuard interface: %s",
            self.interface_name,
        )
        config = self.app_config_service.read()
        iface_output = cleandoc(
            f"""
            Interface "{self.interface_name}":
                Created:           {seconds_to_date_time(config.created)}
                Public address:    {config.endpoint}
                Interface address: {config.address}
                Public key:        {pubkey(config.private_key)}
                Peer DNS:          {config.dns}
        """
        )

        sections = [iface_output]

        for peer in config.peers:
            preshared_key = peer.preshared_key if peer.preshared_key else ""
            peer_output = cleandoc(
                f"""
                Peer "{peer.name}":
                    Added:         {seconds_to_date_time(peer.added)}
                    Public key:    {peer.public_key}
                    Preshared key: {mask(preshared_key)}
                    Allowed IPs:   {peer.allowed_ips}
            """
            )
            sections.append(peer_output)

        print("\n\n".join(sections))
