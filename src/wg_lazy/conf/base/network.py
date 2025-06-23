"""Network helpers.

Hostname validator implementation shamelessly stolen from
https://github.com/python-validators/validators/
"""

import logging
import re
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
)

LOG = logging.getLogger(__name__)


class Port:
    """TCP/UDP port.

    Supports values from 1 to 65535, inclusive. This should not be used
    to represent UDP port 0 (no port).

    Attributes:
        value: Port number as an integer.
    """

    def __init__(self, port: int | str):
        """Validate and store port."""
        port_num = int(port) if str(port).isdigit() else 0
        if 1 <= port_num <= 65535:
            self.value = int(port)
        else:
            raise ValueError(f'invalid port: "{port}"')

    def __str__(self):
        """Return the port value."""
        return str(self.value)


class PrivateIPv4Address:
    """Private IPv4 network address with CIDR mask.

    Addresses with a /32 mask are considered to be standalone IPv4
    addressess and will not have network or broadcast address
    checks.
    """

    _ERROR_MSG_PREFIX = "invalid private IPv4 network address"

    def __init__(
        self,
        cidr_notation_addr: str,
        # min_prefixlen: int = 8,
        # max_prefixlen: int = 30,
    ):
        """Initialize a private IPv4 address with a mask.

        The default maximum network prefix length is 30 so that there
        can be at least 2 IPv4 addresses allocated in the network.

        Args:
            cidr_notation_addr: IPv4 address in CIDR notation.

        Raises:
            ValueError: Invalid IPv4 address or netmask.
        """
        _inst_err_msg = f"${self._ERROR_MSG_PREFIX}: {cidr_notation_addr}"
        try:
            self.network = IPv4Network(cidr_notation_addr, strict=False)
            self.value = self._cidr_addr.split("/")[0]
        except ValueError:
            raise ValueError(_inst_err_msg)

        # invalid_prefix_len_limits = not all(
        #     [
        #         min_prefixlen <= max_prefixlen,
        #         8 <= max_prefixlen <= 32,
        #         8 <= min_prefixlen <= 32,
        #     ]
        # )
        # if invalid_prefix_len_limits:
        #     raise ValueError("invalid ")

        # self.__min_prefixlen = min_prefixlen
        # self.__max_prefixlen = max_prefixlen
        self._cidr_addr = cidr_notation_addr
        self.value = self._cidr_addr.split("/")[0]

        if not self._is_valid():
            LOG.debug("%s: %s", _inst_err_msg, repr(self))
            raise ValueError(_inst_err_msg + repr(self))

    def _is_valid(self):
        return not any(
            [
                # has network prefix length
                not self._cidr_addr.endswith(f"/{self.prefixlen}"),
                # is legally assignable in a private network
                not self.is_private,
                self.is_network_address,
                self.is_global,
                self.is_link_local,
                self.is_broadcast,
                self.is_multicast,
                self.is_reserved,
                self.is_unspecified,
                self.is_loopback,
            ]
        )

    @property
    def is_broadcast(self):
        """Test if the address is the network broadcast address."""
        return self.prefixlen < 32 and self.value == str(
            self.broadcast_address
        )

    @property
    def is_network_address(self):
        """Test if the address is the network address."""
        return self.prefixlen < 32 and self.value == str(self.network_address)

    def __contains__(self, other: object):
        """Return True if `other` is in the same network.

        Network and broadcast addresses are not considered part of the
        same network as this address.
        """
        return (
            super().__contains__(other)
            and other != self.network_address
            and other != self.broadcast_address
        )

    def __repr__(self):
        """Return a string with all attributes of this network."""
        attrs = [
            f"network_address={self.network_address}",
            f"prefixlen={self.prefixlen}",
            f"is_private={self.is_private}",
            f"is_global={self.is_global}",
            f"is_link_local={self.is_link_local}",
            f"is_broadcast={self.is_broadcast}",
            f"is_multicast={self.is_multicast}",
            f"is_reserved={self.is_reserved}",
            f"is_unspecified={self.is_unspecified}",
            f"is_loopback={self.is_loopback}",
        ]
        joined = ", ".join(attrs)
        return f"{self.__class__.__name__}({joined})"

    def __str__(self):
        """Return network address in CIDR notation."""
        return self._cidr_addr


class PublicHostPort:
    """Public address with port.

    Attributes:
        host: Hostname, domain, or IP address.
        port: Port number.
        addr_type: One of "hostname", "domain", "IPv4", or "IPv6".
    """

    def __init__(self, addr: str):
        """Initialize this host address.

        Args:
            addr: Address in <host>:<port> form.

        Raises:
            ValueError: Invalid address.
        """
        self._raw_addr = addr
        self.host, self.port = self._split(addr)
        self.addr_type = "unknown"

        if not self._validate():
            raise ValueError(f'invalid host or port: "{addr}"')

    def _split(self, addr: str) -> tuple[str, str | None]:
        """Attempt to split an address's host and port."""
        host = addr
        port = None
        if addr.count("]:") == 1:  # IPv6
            host_seg, port = addr.rsplit(":", 1)
            host = host_seg.lstrip("[").rstrip("]")
        elif addr.count(":") == 1:  # IPv4 or domain
            host, port = addr.rsplit(":", 1)
        return host, port

    def _validate(self) -> bool:
        """Validate a host address."""
        return self._validate_port() and (
            self._validate_host_as_hostname()
            or self._validate_host_as_domain()
            or self._validate_host_as_ipv4_addr()
            or self._validate_host_as_ipv6_addr()
        )

    def _validate_port(self):
        try:
            return bool(Port(self.port))
        except ValueError:
            return False

    def _validate_host_as_hostname(self) -> bool:
        valid = bool(
            re.match(
                r"^(?!-)[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,59}[a-zA-Z0-9])?(?<!-)$",
                self.host,
            )
        )
        self.addr_type = "hostname" if valid else self.addr_type
        return valid

    def _validate_host_as_domain(self) -> bool:
        try:
            valid = bool(
                not re.search(r"\s", self.host)
                and len(self.host) <= 253
                and re.match(
                    # First character of the domain
                    r"^(?:[a-zA-Z0-9]"
                    # Sub domain + hostname
                    + r"(?:[a-zA-Z0-9-_]{0,61}[A-Za-z0-9])?\.)+"
                    # 63 characters of the gTLD
                    + r"[A-Za-z0-9][A-Za-z0-9-_]{0,61}[A-Za-z]$",
                    self.host.encode("idna").decode("utf-8"),
                    re.IGNORECASE,
                )
            )
            self.addr_type = "domain" if valid else self.addr_type
            return valid
        except UnicodeError:
            return False

    def _validate_host_as_ipv4_addr(self) -> bool:
        try:
            v4_addr = IPv4Address(self.host)
            valid = self._is_assignable_ip_addr(v4_addr)
            self.addr_type = "IPv4" if valid else self.addr_type
            return valid
        except ValueError:
            return False

    def _validate_host_as_ipv6_addr(self) -> bool:
        try:
            v6_addr = IPv6Address(self.host)
            valid = self._is_assignable_ip_addr(v6_addr)
            self.addr_type = "IPv6" if valid else self.addr_type
            return valid
        except ValueError:
            return False

    def _is_assignable_ip_addr(
        self, ip_addr: IPv4Address | IPv6Address
    ) -> bool:
        return not any(
            [
                ip_addr.is_multicast,
                ip_addr.is_reserved,
                ip_addr.is_unspecified,
            ]
        )

    def __repr__(self):
        """Return a string with all attributes of this host."""
        attrs = [
            f"host={self.host}",
            f"port={self.port}",
            f"addr_type={self.addr_type}",
        ]
        joined = ", ".join(attrs)
        return f"{self.__class__.__name__}({joined})"

    def __str__(self):
        """Return address in <host>:<port> form."""
        return f"{self._raw_addr}"


class AssignableIPv4Address(IPv4Address):
    """Assignable IPv4 address."""

    _ERROR_MSG_PREFIX = "unassignable IPv4 address"

    def __init__(self, addr: str):
        """Initialize IPv4 address and ensure assignability.

        Args:
            addr: Non-reserved, non-multicast IPv4 address.

        Raises:
            ValueError: Invalid IPv4 address.
        """
        _inst_err_msg = f'{self._ERROR_MSG_PREFIX}: "{addr}"'
        try:
            super().__init__(addr)
        except ValueError:
            raise ValueError(_inst_err_msg)

        invalid = any(
            [
                self.is_multicast,
                self.is_reserved,
                self.is_unspecified,
            ]
        )

        if invalid:
            LOG.debug("invalid address allocation type: %s", repr(self))
            raise ValueError(_inst_err_msg)

    def __repr__(self):
        """Return a string with all attributes of this address."""
        attrs = [
            f"address={self.packed}",
            f"is_multicast={self.is_multicast}",
            f"is_reserved={self.is_reserved}",
            f"is_unspecified={self.is_unspecified}",
        ]
        joined = ", ".join(attrs)
        return f"{self.__class__.__name__}({joined})"
