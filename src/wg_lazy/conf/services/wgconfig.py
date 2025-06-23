"""Facility for managing wg-lazy configuration."""

import logging

from ..base import (
    BaseConfigDataStore,
    BaseConfigService,
    ConfigRoot,
    Peer,
)
from ..formats import WgQuickConfigFormat

LOG = logging.getLogger(__name__)


class WgConfigService(BaseConfigService):
    """Configuration file service for WireGuard."""

    def __init__(self, config_ds: BaseConfigDataStore):
        """Initialize WireGuard configuration file service."""
        super().__init__(config_ds=config_ds, config_fmt=WgQuickConfigFormat())

    # TODO: move this to a different service
    def generate_peer_config(self, config: ConfigRoot, peer: Peer) -> str:
        """Generate configuration to be imported by a peer."""
        assert isinstance(self._config_fmt, WgQuickConfigFormat)
        return self._config_fmt.format_peer(config, peer)
