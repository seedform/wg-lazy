"""Network tests."""


from pytest import mark, raises

from wg_lazy.utils.network import (
    AssignableIPv4Address,
    Port,
    PrivateIPv4Address,
    PublicHostPort,
)


class TestPort:
    """Test the Port class."""

    def test_valid(self):
        """Test valid port instantiation."""
        assert str(Port(2300)) == "2300"

    @mark.parametrize("value", ["bad", 0, 65536])
    def test_invalid(self, value):
        """Test instantiating an invalid port number."""
        with raises(ValueError):
            Port(value)


class TestPrivateIPv4Address:
    """Test the PrivateIPv4Address utility class."""

    @mark.parametrize(
        "addr",
        ["192.168.0.11/24", "10.0.0.254/8", "10.100.1.193/26"],
    )
    def test_valid(self, addr):
        """Test for valid network addresses."""
        PrivateIPv4Address(addr)

    @mark.parametrize(
        "addr",
        [
            "192.168.0.1",  # missing prefix length
            "192.0.0.1/8",  # invalid prefix length for private range
            "10.100.1.192/26",  # can't be the network address
            "10.0.0.255/24",  # can't be the broadcast address
            "8.8.0.0/16",  # public range
            "224.0.0.0/4",  # multicast
            "240.0.0.0/4",  # reserved
            "01189998819991197253",  # lyrics
            "FA20D",  # not a Miata
            "",  # empty
        ],
    )
    def test_invalid(self, addr):
        """Test for invalid network addresses."""
        with raises(ValueError):
            PrivateIPv4Address(addr)

    @mark.parametrize(
        ("builtin", "expected"),
        [
            (
                repr,
                (
                    "PrivateIPv4Address("
                    "network_address=10.86.0.0"
                    ", prefixlen=16"
                    ", is_private=True"
                    ", is_global=False"
                    ", is_link_local=False"
                    ", is_broadcast=False"
                    ", is_multicast=False"
                    ", is_reserved=False"
                    ", is_unspecified=False"
                    ", is_loopback=False"
                    ")"
                ),
            ),
            (str, "10.86.0.192/16"),
        ],
    )
    def test_repr_and_str(self, builtin, expected):
        """Test __repr__() and __str__() output."""
        net = PrivateIPv4Address("10.86.0.192/16")
        assert builtin(net) == expected


class TestPublicHostPort:
    """Test the PrivateIPv4Address utility class."""

    @mark.parametrize(
        "addr",
        [
            "",
            ":8601",
            "-.example.com:2000",  # invalid label
            "192.168.0.1:65536",  # invalid port
            f"{'a' * 64}.example.com:2560",  # large label
            f"{'a' * 63}." * 4 + ".example.com:1080",  # large domain
            "240.0.0.1:8080",  # multicast
            "224.0.0.2:8384",  # reserved
        ],
    )
    def test_invalid(self, addr):
        """Test for invalid host addresses."""
        with raises(ValueError):
            PublicHostPort(addr)

    @mark.parametrize(
        ("addr", "addr_type"),
        [
            ("[2607::1]:55555", "IPv6"),
            ("10.168.0.1:2319", "IPv4"),
            ("127.0.0.1:51820", "IPv4"),
            ("wg-lazy.example.com:51820", "domain"),
            ("computer:51820", "hostname"),
            (f"{'a' * 63}.example.com:2560", "domain"),
            ("example.com:3232", "domain"),
        ],
    )
    def test_valid(self, addr, addr_type):
        """Test for valid host addresses."""
        host_addr = PublicHostPort(addr)
        assert host_addr.addr_type == addr_type

    @mark.parametrize(
        ("builtin", "expected"),
        [
            (repr, "PublicHostPort(host=2607::1, port=51820, addr_type=IPv6)"),
            (str, "[2607::1]:51820"),
        ],
    )
    def test_repr_and_str(self, builtin, expected):
        """Test __repr__() and __str__() output."""
        host_addr = PublicHostPort("[2607::1]:51820")
        assert builtin(host_addr) == expected


class TestAssignableIPv4Address:
    """Test the AssignableIPv4Address class."""

    def test_valid(self):
        """Test valid instantiation."""
        assert str(AssignableIPv4Address("1.2.3.4")) == "1.2.3.4"

    def test_invalid(self):
        """Test invalid instantiation."""
        with raises(ValueError):
            AssignableIPv4Address("242.1.23.29")
