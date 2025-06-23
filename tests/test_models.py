"""Test model objects."""

import re
from contextlib import nullcontext as success
from ipaddress import IPv4Network
from itertools import islice

from pytest import fixture, mark, raises
from utils import WG_TEST_KEYS

from wg_lazy.conf import (
    ConfigRoot,
    ConfigValidationError,
    Peer,
    PeerValidationError,
)

DEFAULT_TEST_NETWORK = "10.168.0.1/29"  # six usable IPv4 addresses


class TestPeer:
    """Test Peer creation."""

    def test_bare_init(self):
        """Test instantiation with minimal parameters."""
        public_key = WG_TEST_KEYS[0].public
        with success():
            Peer(public_key=public_key, allowed_ips="10.0.0.2/32")

    @mark.parametrize(
        ("params", "pattern"),
        [
            (
                {  # invalid IPv4 address for allowed_ips value
                    "name": "Test Peer",
                    "allowed_ips": "10.0.0.2/33",
                    "public_key": WG_TEST_KEYS[1].public,
                },
                "10.0.0.2/33",
            ),
            (
                {  # invalid subnet mask for allowed_ips value
                    "name": "Test Peer",
                    "allowed_ips": "10.0.0.2/30",
                    "public_key": WG_TEST_KEYS[1].public,
                },
                "invalid subnet mask.*10.0.0.2/30",
            ),
            (
                {  # invalid public key
                    "name": "Test Peer",
                    "allowed_ips": "192.168.0.2/32",
                    "public_key": "BAD_PUBLIC_KEY",
                },
                "BAD_PUBLIC_KEY",
            ),
            (
                {  # name too long
                    "name": "Test %40s Peer" % "",
                    "allowed_ips": "192.168.0.2/32",
                    "public_key": WG_TEST_KEYS[2].public,
                },
                "invalid.*name.*length",
            ),
            (
                {  # name too short
                    "name": "",
                    "allowed_ips": "192.168.0.2/32",
                    "public_key": WG_TEST_KEYS[2].public,
                },
                "invalid.*name.*length",
            ),
        ],
    )
    def test_invalid_custom_type_values(self, params, pattern):
        """Test instantiation with an invalid custom type values."""
        with raises(PeerValidationError, match=pattern):
            Peer(**params)


class TestConfigRoot:
    """Test ConfigRoot creation and operations."""

    @fixture
    def peers(self):
        """Generate raw Peer instances."""

        def generator():
            network = IPv4Network(DEFAULT_TEST_NETWORK, strict=False)
            hosts = network.hosts()
            next(hosts)  # drop Config address

            for i, host in enumerate(hosts):
                yield Peer(
                    name=f"Test Peer {i}",
                    private_key=WG_TEST_KEYS[i].private,
                    public_key=WG_TEST_KEYS[i].public,
                    allowed_ips=f"{str(host)}/32",
                )

        return generator

    @fixture
    def config(self, peers):
        """Return a ConfigRoot instance for tests."""
        return ConfigRoot(address=DEFAULT_TEST_NETWORK)

    def test_bare_init(self):
        """Test instantiation with minimal parameters."""
        assert ConfigRoot()

    @mark.parametrize("count", [0, 1, 2])
    def test_add_peer(self, count, peers, config):
        """Test adding a peer."""
        create_peer = peers()
        for i in range(count):
            config.add_peer(next(create_peer))
        assert len(config.peers) == count

    def test_inavlid_add_peer_not_in_network(self, peers, config):
        """Test adding a peer with an out-of-network address."""
        peer = next(peers())
        peer.allowed_ips = "10.168.0.7/32"
        with raises(PeerValidationError, match="not in network"):
            config.add_peer(peer)

    @mark.parametrize("attr", ["name", "public_key", "allowed_ips"])
    def test_invalid_add_peer_conflict(self, attr, peers, config):
        """Test adding a peer with a conflicting values."""
        peer1, peer2 = islice(peers(), 2)
        conflict_value = getattr(peer1, attr)
        setattr(peer2, attr, conflict_value)
        config.add_peer(peer1)
        with raises(PeerValidationError, match=re.escape(conflict_value)):
            config.add_peer(peer2)

    @mark.parametrize(
        ("config_address", "peer_name", "expected_peer_ips"),
        [
            ("192.168.50.1/24", "Named Peer", "192.168.50.2/32"),
            ("10.168.0.1/24", None, "10.168.0.2/32"),
        ],
    )
    def test_create_peer(self, config_address, peer_name, expected_peer_ips):
        """Test creating a peer in different networks."""
        config = ConfigRoot(address=config_address)
        new_peer = config.create_peer(name=peer_name)
        assert new_peer.allowed_ips == expected_peer_ips

    @mark.parametrize(
        ("params", "match_prefix"),
        [
            ({"public_address": "portless-address.local"}, "invalid host"),
            ({"dns": "bad-dns-address"}, "unassignable.*address"),
            ({"address": "10.0.0.0/24"}, "invalid.*address"),
            ({"private_key": "bad-key"}, "invalid.*key"),
            ({"listen_port": "ZERO"}, "invalid port"),
        ],
    )
    def test_invalid_custom_type_values(self, params, match_prefix):
        """Test instantiation with an invalid custom type values."""
        invalid_value = next(iter(params.values()))
        pattern = re.compile(f"{match_prefix}.*{invalid_value}", re.DOTALL)
        with raises(ConfigValidationError, match=pattern):
            ConfigRoot(**params)

    def test_invalid_create_peer_ips_exhausted(self):
        """Test creating a peer in an exhausted IPv4 address space."""
        cr = ConfigRoot(address=DEFAULT_TEST_NETWORK)
        for i in range(5):
            cr.add_peer(cr.create_peer())
        with raises(ConfigValidationError, match="exhausted"):
            cr.create_peer()

    def test_get_peer_by_name(self, config):
        """Test getting a peer by name."""
        config.add_peer(config.create_peer(name="unit"))
        found = config.get_peer_by_name("unit")
        assert found.name == "unit"

    def test_get_peer_by_name_not_found(self, config):
        """Test not finding a peer by name."""
        config.add_peer(config.create_peer(name="unit"))
        found = config.get_peer_by_name("unfindable")
        assert found is None

    def test_invalid_get_peer_by_name(self, config):
        """Test getting a peer using an invalid name."""
        config.add_peer(config.create_peer(name="unit"))
        with raises(ValueError):
            config.get_peer_by_name("")

    def test_get_peer_by_pubkey(self, config, peers):
        """Test getting a peer by public key."""
        peer = next(peers())
        config.add_peer(peer)
        found = config.get_peer_by_pubkey(peer.public_key)
        assert found.public_key == peer.public_key

    def test_get_peer_by_pubkey_not_found(self, config, peers):
        """Test not finding a peer by public key."""
        config.add_peer(next(peers()))
        found = config.get_peer_by_pubkey(WG_TEST_KEYS[-1].public)
        assert found is None

    def test_invalid_get_peer_by_pubkey(self, config, peers):
        """Test getting a peer by using an invalid public key."""
        config.add_peer(next(peers()))
        with raises(ValueError):
            config.get_peer_by_pubkey("invalid")
