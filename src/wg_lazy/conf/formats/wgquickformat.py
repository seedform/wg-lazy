"""WireGuard configuration format."""

import logging
import re
from configparser import ConfigParser
from configparser import Error as ConfigParserError
from inspect import cleandoc
from typing import TypeVar

from wg_lazy.utils import pubkey, raise_as, seconds_to_date_time

from ..base import (
    BaseConfigFormat,
    ConfigFormatError,
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


class WgQuickConfigFormat(BaseConfigFormat):
    """WireGuard configuration parser and formatter."""

    # abstractmethod
    @raise_as(
        ConfigFormatError, catch=(ConfigValidationError, PeerValidationError)
    )
    def parse(self, data: str) -> ConfigRoot:
        """Parse WireGuard configuration.

        WARNING: EXPERIMENTAL!!!

        Caveats:
        - Not reliable for parsing all possible cases of WireGuard
            configuration files.
        - Does NOT currently capture wg-lazy app-specific attributes
            from a WireGuard configuration file generated via this
            library.
        - Peer names are replaced with random UUIDs.
        - Cannot parse multiple AllowedIPs for individual peers.

        Expected file contents:
        - ONE [Interface] section that MUST have at least
            PrivateKey, Address, and ListenPort set.
        - Zero or more [Peer] sections, where every instance MUST
            have at least PublicKey and only ONE AllowedIPs set.

        Args:
            data: WireGuard configuration as a string, with attributes
                specifically recognized by wg-quick.

        Returns:
            A ConfigRoot instance created from parsed data.

        Raises:
            ConfigFormatError: Invalid configuration data in string.
        """
        sects = self._load_sects(data)
        iface_sect = self._get_iface_sect(sects)
        peer_sects = self._get_peer_sects(sects)

        config = self._parse_sect(
            "Interface", iface_sect, ConfigRoot, _IFACE_REQ_OPTS
        )
        for peer_sect in peer_sects:
            peer = self._parse_sect("Peer", peer_sect, Peer, _PEER_REQ_OPTS)
            config.add_peer(peer)

        return config

    def _load_sects(self, data: str) -> list[str]:
        """Load individual sections into a list."""
        sects = []
        current = []  # type: ignore[var-annotated]
        for raw_line in data.splitlines():
            line = raw_line.strip()
            if _SECT_HDR_RE.match(line):
                sects.append("\n".join(current))
                current = [line]
                LOG.debug("found section header: %s", line)
            else:
                current.append(line)
        sects.append("\n".join(current))

        # remove ignored content and clean up sections
        sects_filtered = filter(lambda s: _SECT_HDR_RE.match(s), sects)
        sects_stripped = map(lambda s: s.strip(), sects_filtered)
        sects = list(sects_stripped)

        if not sects:
            raise ConfigFormatError(_INVALID_CONTENT_MSG)

        return sects

    def _get_iface_sect(self, sects: list[str]) -> str:
        """Find and return the [Interface] section and contents.

        Raises:
            ConfigFormatError: More than one or no [Interface] sections
                were found.
        """
        iface_sects = list(filter(lambda s: _IFACE_HDR_RE.match(s), sects))
        if not iface_sects:
            raise ConfigFormatError(_IFACE_SECT_NOT_FOUND_MSG)
        elif len(iface_sects) > 1:
            raise ConfigFormatError(_IFACE_SECT_COUNT_ERR_MSG)
        return iface_sects[0]

    def _get_peer_sects(self, sects: list[str]) -> list[str]:
        """Find and return all [Peer] sections and contents."""
        return list(filter(lambda s: _PEER_HDR_RE.match(s), sects))

    def _parse_sect(
        self,
        sect_name: str,
        sect_data: str,
        sect_cls: type[_BaseConfigModel],
        req_fields: list[str],
    ) -> _BaseConfigModel:
        """Parse a section and return its respective model instance.

        Raises:
            ConfigFormatError: Failed to parse section, missing
                required fields, or error instatiating model.
            ConfigValidationError: Config instantiation failure.
            PeerValidationError: Peer instantiation failure.
        """
        parser = ConfigParser()
        parser.optionxform = str  # type: ignore[assignment]  # preserve case
        try:
            parser.read_string(sect_data)
        except ConfigParserError as cpe:
            raise ConfigFormatError(cpe.message)

        checks = map(lambda o: parser.has_option(sect_name, o), req_fields)
        if not all(checks):
            LOG.debug("%s: %s", _INCOMPLETE_SECT_MSG, sect_data)
            raise ConfigFormatError(f"{_INCOMPLETE_SECT_MSG}: [{sect_name}]")

        return sect_cls(**parser[sect_name])

    # abstractmethod
    def format(self, config: ConfigRoot) -> str:
        """Format a ConfigRoot instance into WireGuard configuration."""
        iface_sect = cleandoc(
            f"""
            ##
            # WARNING: Changes will be overwritten by wg-lazy.
            #
            # Created on: {seconds_to_date_time(config.created)}
            #
            [Interface]
            PrivateKey = {config.private_key}
            Address = {config.address}
            ListenPort = {config.listen_port}
            """
        )

        sections = [iface_sect]

        for peer in sorted(config.peers, key=lambda p: p.added):
            peer_sect = cleandoc(
                f"""
                # {peer.name} (added {seconds_to_date_time(peer.added)})
                [Peer]
                PublicKey = {peer.public_key}
                PresharedKey = {peer.preshared_key}
                AllowedIPs = {peer.allowed_ips}
                """
            )
            sections.append(peer_sect)

        return "\n\n".join(sections) + "\n"

    def format_peer(self, config: ConfigRoot, peer: Peer) -> str:
        """Generate WireGuard configuration for a peer.

        Args:
            config: A ConfigRoot instance to use as a base.
            peer: A Peer instance.

        Returns:
            WireGuard configuration file contents as a string that can
            be imported by client devices.
        """
        pfx_len = config._network.prefixlen
        iface_sect = cleandoc(
            f"""
            [Interface]
            PrivateKey = {peer.private_key}
            Address = {peer.allowed_ips.split("/")[0]}/{pfx_len}
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
