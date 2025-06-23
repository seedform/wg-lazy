"""WireGuard configuration format."""

import logging
import re
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from inspect import cleandoc
from typing import TypeVar

from wg_lazy.utils import pubkey, raise_as, seconds_to_date_time

from ..base import (
    BaseConfigFormatter,
    ConfigFormatterError,
    ConfigRoot,
    ConfigValidationError,
    Peer,
    PeerValidationError,
)

_BaseConfigModel = TypeVar("_BaseConfigModel", ConfigRoot, Peer)

LOG = logging.getLogger(__name__)


_INVALID_CONTENT_MSG = "invalid WireGuard configuration file"
_IFACE_SECT_NOT_FOUND_MSG = "[Interface] section not found"
_IFACE_SECT_COUNT_ERR_MSG = "more than one [Interface] section found"
_INCOMPLETE_SECT_MSG = "missing required fields in section"

_SECT_HDR_RE = re.compile(r"(?:^|\r|\n|\r\n)(\[[a-zA-Z]+])(?:\r|\n|\r\n|$)")
_IFACE_HDR_RE = re.compile(r"(?:^|\r|\n|\r\n)(\[Interface])(?:\r|\n|\r\n|$)")
_PEER_HDR_RE = re.compile(r"(?:^|\r|\n|\r\n)(\[Peer])(?:\r|\n|\r\n|$)")

_IFACE_REQ_OPTS = ["PrivateKey", "Address", "ListenPort"]
_PEER_REQ_OPTS = ["PublicKey", "AllowedIPs"]


class WgPeerFormatter:
    """WireGuard configuration formatter for peers."""

    def format(self, config: ConfigRoot) -> str:
        """Generate WireGuard configuration for a peer.

        Args:
            config: A ConfigRoot instance that represents a peer's
                configuration with ONLY one peer.

        Returns:
            WireGuard configuration file contents as a string that can
            be imported by client devices.
        """
        (peer,) = config.peers

        pfx_len = config._network.prefixlen
        iface_sect = cleandoc(
            f"""
            [Interface]
            PrivateKey = {config.private_key}
            Address = {config.address}
            DNS = {config.dns}
            """
        )
        addr = config._network
        peer_sect = cleandoc(
            f"""
            [Peer]
            PublicKey = {pubkey(config.private_key)}
            PresharedKey = {peer.preshared_key}
            AllowedIPs = {addr.network_address}/{addr.prefixlen}
            PersistentKeepalive = 0
            Endpoint = {config.endpoint}
            """
        )
        return "\n\n".join([iface_sect, peer_sect]) + "\n"
