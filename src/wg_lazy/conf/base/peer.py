"""Classes and functions for managing wg-lazy configuration."""

import logging
import re
from time import time
from typing import Annotated
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SerializationInfo,
    ValidationError,
    field_serializer,
)
from pydantic.functional_validators import AfterValidator, BeforeValidator

from wg_lazy.consts import defaults, limits
from wg_lazy.utils import (
    AssignableIPv4Address,
    Port,
    PrivateIPv4Address,
    PublicHostPort,
    genkey,
    genpsk,
    pubkey,
    to_pascal_case,
)

LOG = logging.getLogger(__name__)

# https://lists.zx2c4.com/pipermail/wireguard/2020-December/006222.html
_WG_KEY_RE = re.compile(r"[A-Za-z0-9+/]{42}[A|E|I|M|Q|U|Y|c|g|k|o|s|w|4|8|0]=")


def _no_pfx(allowed_ips: str):
    """Remove the prefix length from an AllowedIPs value."""
    return allowed_ips.split("/")[0]


class BaseModelError(Exception):
    """Base class for model exceptions."""


class ConfigValidationError(BaseModelError):
    """Raised when a Config has invalid attribute values."""


class PeerValidationError(BaseModelError):
    """Raised when a Peer has invalid attribute values."""


class _Checks:
    @staticmethod
    def endpoint(host_port: str):
        return str(PublicHostPort(host_port))

    @staticmethod
    def private_address(cidr_addr: str):
        return str(PrivateIPv4Address(cidr_addr))  # handles /8 to /30

    @staticmethod
    def ipv4(v4_addr: str):
        return str(AssignableIPv4Address(v4_addr))

    @staticmethod
    def wg_key(key: str):
        if _WG_KEY_RE.match(key):
            return key
        raise ValueError(f'invalid WireGuard key: "{key}"')

    @staticmethod
    def listen_port(port: int):
        return Port(port).value

    @staticmethod
    def peer_name(name: str):
        if limits.PEER_NAME_MIN_LEN <= len(name) <= limits.PEER_NAME_MAX_LEN:
            return name
        msg = (
            f"invalid peer name length not between {limits.PEER_NAME_MIN_LEN} "
            f"and {limits.PEER_NAME_MAX_LEN} characters: {len(name)}"
        )
        raise ValueError(msg)


class _Types:
    Endpoint = Annotated[str, AfterValidator(_Checks.endpoint)]
    PeerAddress = Annotated[str, AfterValidator(_Checks.private_address)]
    IPv4Address = Annotated[str, AfterValidator(_Checks.ipv4)]
    WgKey = Annotated[str, AfterValidator(_Checks.wg_key)]
    ListenPort = Annotated[int, BeforeValidator(_Checks.listen_port)]
    PeerName = Annotated[str, BeforeValidator(_Checks.peer_name)]


class _Factories:
    @staticmethod
    def uuid():
        return str(uuid4())

    @staticmethod
    def time():
        return int(time())


def _to_camel_case(snake: str) -> str:
    if snake[0] == "_":  # leading underscore, ignore field
        return snake
    parts = re.split("_+", snake)
    words = [word.capitalize() for word in parts[1:]]
    return parts[0] + "".join(words)


class _BasePeer(BaseModel):
    """Configured base model for configuration."""

    model_config = ConfigDict(
        alias_generator=_to_camel_case, populate_by_name=True, extra="ignore"
    )

    def __init__(self, exception_cls: type[BaseModelError], *args, **kwargs):
        """Simplify ValidationError into a BaseModelError instance."""
        try:
            super().__init__(*args, **kwargs)
        except ValidationError as ve:
            msgs = []
            for error in ve.errors():
                field = error["loc"][0]
                msg = error["msg"]
                input_ = error["input"]
                msgs.append(f'{msg} -> "{field}" <- {input_}')
            raise exception_cls("invalid configuration: " + "; ".join(msgs))


class Peer(_BasePeer):
    """Individual peer representation.

    Attributes:
        address: The peer's IPv4 address (in CIDR notation) within the
            WireGuard network.
        public_key: The peer's public key.
        private_key: The peer's private key.
        preshared_key: A preshared key with the primary peer/server.
        name: The peer's name.
        added: The date and time this peer was added to the primary
            configuration, in seconds.
    """

    address: _Types.DnsAddress
    public_key: _Types.WgKey
    private_key: _Types.WgKey | None = Field(default=None)
    preshared_key: _Types.WgKey | None = Field(default=None)
    name: _Types.PeerName = Field(default_factory=_Factories.uuid)
    added: int = Field(default_factory=_Factories.time)

    def __init__(self, *args, **kwargs):
        """Initialize a Peer.

        Raises:
            PeerValidationError: Invalid arguments for instantiation.
        """
        super().__init__(PeerValidationError, *args, **kwargs)

    def __hash__(self):
        """Allow Peer instances to be used in sets."""
        return hash(self.public_key)


class SitePeer(_BasePeer):
    """Top-level configuration structure.

    Used as the primary domain object for operating within this
    package. Represent's the WireGuard "server" configuration.

    Peer names and public keys MUST be unique.

    Use create_peer() to create peers that are bound to this
    configuration. Use add_peer() to validate a peer's attributes
    before adding it to a configuration. To delete a peer, remove
    it from the peers dict.

    Attributes:
        endpoint: The server's public address.
        dns: DNS that peers will use.
        created: Configuration creation date and time in seconds.
        private_key: The server's private key.
        address: The server's WireGuard interface address.
        listen_port:  The server's WireGuard listen port.
        peers: Set of Peer instances.
    """

    # app-specific settings and info
    endpoint: _Types.Endpoint = Field(default=defaults.ENDPOINT)
    dns: _Types.DnsAddress = Field(default=defaults.DNS)
    created: int = Field(default_factory=_Factories.time)

    # [Interface] section
    private_key: _Types.WgKey = Field(default_factory=genkey)
    address: _Types.PeerAddress = Field(default=defaults.INTERFACE_ADDRESS)
    listen_port: _Types.ListenPort = Field(default=defaults.LISTEN_PORT)

    # [Peer] section
    peers: set[Peer] = Field(default_factory=set)

    def __init__(self, *args, **kwargs):
        """Initialize WireGuard configuration.

        Raises:
            ConfigValidationError: Invalid config attribute values.
            PeerValidationError: Invalid peer found.
        """
        super().__init__(ConfigValidationError, *args, **kwargs)
        self._network = PrivateIPv4Address(self.address)
        self._peer_names_map = {}
        self._peer_pubkeys_map = {}
        self._peer_ips_map = {}  # without /32 prefix length

        # validate peers and build integrity maps
        for peer in self.peers:
            self._validate_peer(peer)
            self._peer_names_map[peer.name] = peer
            self._peer_pubkeys_map[peer.public_key] = peer
            self._peer_ips_map[peer.address] = peer

    def create_peer(self, name: str | None = None) -> Peer:
        """Create and return a new peer in this peer's network.

        Should not be called multiple times in succession without
        calling add_peer() between calls.

        Args:
            name: Peer name (new UUID if set to None).

        Returns:
            Newly created Peer instance.

        Raises:
            ConfigValidationError: IP address space exhausted.
            PeerValidationError: Invalid peer name.
        """
        private_key = genkey()
        public_key = pubkey(private_key)
        preshared_key = genpsk()
        address = self._get_available_ip()

        kwargs = {
            "public_key": public_key,
            "private_key": private_key,
            "preshared_key": preshared_key,
            "address": address,
        }
        if name is not None:
            kwargs["name"] = str(name)

        return Peer(**kwargs)

    def add_peer(self, peer: Peer):
        """Add a generated peer to this configuration.

        Args:
            peer: Peer instance based on this configuration.

        Raises:
            PeerValidationError: Invalid peer or conflict.
        """
        self._validate_peer(peer)
        self.peers.add(peer)
        self._peer_names_map[peer.name] = peer
        self._peer_pubkeys_map[peer.public_key] = peer
        self._peer_ips_map[_no_pfx(peer.allowed_ips)] = peer

    def remove_peer(self, peer: Peer):
        """Remove a peer.

        Args:
            peer: Peer instance in this configuration.

        Raises:
            KeyError: Peer is not a part of this configuration.
        """
        self.peers.remove(peer)
        del self._peer_names_map[peer.name]
        del self._peer_pubkeys_map[peer.public_key]
        del self._peer_ips_map[_no_pfx(peer.allowed_ips)]

    def get_peer_by_name(self, name: str) -> Peer | None:
        """Search peer by name.

        Raises:
            ValueError: Invalid name.

        Returns:
            Peer instance with specified name, if found.
        """
        _Checks.peer_name(name)
        return self._peer_names_map.get(name)

    def get_peer_by_pubkey(self, public_key: str) -> Peer:
        """Search peer by public key.

        Raises:
            ValueError: Invalid public key.

        Returns:
            Peer instance with specified public key, if found.
        """
        search_pubkey = _Checks.wg_key(public_key)
        return self._peer_pubkeys_map.get(search_pubkey)

    # ensure peers are sorted by date/time added
    @field_serializer("peers", return_type=list)
    def _sort_peers(self, peers: set[Peer], _: SerializationInfo):
        return sorted(peers, key=lambda p: p.added)

    def _validate_peer(self, peer: Peer):
        # ensure unique name
        if peer.name in self._peer_names_map:
            msg = f"peer name conflict: {peer.name}"
            raise PeerValidationError(msg)

        # ensure unique public key
        if peer.public_key in self._peer_pubkeys_map:
            msg = f"peer public key conflict: {peer.public_key}"
            raise PeerValidationError(msg)

        # ensure unique allowed IPs value
        peer_ip = _no_pfx(peer.allowed_ips)
        if peer_ip in self._peer_ips_map:
            msg = f"peer IP conflict: {peer.allowed_ips}"
            raise PeerValidationError(msg)

        # ensure peer IP is in network
        if AssignableIPv4Address(peer_ip) not in self._network:
            msg = f"peer IP {peer_ip} not in network {self._network}"
            raise PeerValidationError(msg)

    def _get_available_ip(self) -> str:
        for host in self._network.hosts():  # TODO: ensure broadcast and network ip is not in this
            addr = str(host)
            if addr not in self._peer_ips_map and addr != self._network.value:
                return addr
        msg = f"IP address space exhausted: {self.address}"
        raise ConfigValidationError(msg)

    def inverted(self, peer: Peer):
        """Invert a ConfigRoot to Peer relationship.

        Args:
            peer: Peer to convert to a ConfigRoot instance.

        Returns:
            A ConfigRoot instance which represents the specified peer,
            with this ConfigRoot instance as the sole peer.
        """
        if peer not in self.peers:
            raise ValueError("peer not in configuration")
        elif not peer.private_key:
            raise ValueError("peer private key required")

        new_config = ConfigRoot(
            private_key=peer.private_key,
            address=f"{_no_pfx(peer.allowed_ips)}/{self._network.prefixlen}",
            DNS=self.ipv4,
        )
        new_peer = Peer(
            public_key=pubkey(self.private_key),
            preshared_key=peer.preshared_key,
            allowed_ips=peer.allowed_ips,
            endpoint=self.endpoint,
        )
        new_config.add_peer(new_peer)

        # TODO: what if a peer is inverted twice?

        return new_peer
