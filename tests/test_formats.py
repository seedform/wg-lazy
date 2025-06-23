"""Test data store."""


import json
import re

from freezegun import freeze_time
from pytest import fixture, mark, raises
from utils import WG_TEST_KEYS, load_resource

from wg_lazy.conf import (
    ConfigFormatError,
    ConfigRoot,
    JsonConfigFormat,
    WgQuickConfigFormat,
)

_RESOURCES = {
    "wg-mock.conf": load_resource("wg-mock.conf"),
    "wg-mock.json": load_resource("wg-mock.json"),
    "wg-peer-mock.conf": load_resource("wg-peer-mock.conf"),
}


class TestJsonConfigFormat:
    """Test AppJsonConfigFormat operations.

    Tests are not comprehensive since Pydantic is used under the hood.
    """

    @fixture
    def app_json_fmt(self):
        """Return a new AppJsonConfigFormat instance."""
        return JsonConfigFormat()

    def test_parse(self, app_json_fmt):
        """Test successfully parsing an app config JSON file."""
        cr = app_json_fmt.parse(_RESOURCES["wg-mock.json"])
        assert len(cr.peers) == 2

    def test_invalid_parse(self, app_json_fmt):
        """Test parsing an invalid app config JSON file."""
        with raises(ConfigFormatError):
            app_json_fmt.parse('"created": "1984-10-21"')

    def test_format(self, app_json_fmt):
        """Test formatting into a JSON string."""
        cr = ConfigRoot()
        cr.add_peer(cr.create_peer())
        formatted = app_json_fmt.format(cr)
        assert len(json.loads(formatted)["Peers"]) == 1


@freeze_time("2077-12-31 00:00:00", tz_offset=-5)  # EST
class TestWgQuickConfigFormat:
    """Test WgConfConfigFormat operations."""

    @fixture
    def wg_conf_fmt(self):
        """Return a new WgConfConfigFormat instance."""
        return WgQuickConfigFormat()

    def test_parse(self, wg_conf_fmt):
        """Test successfully parsing an WireGuard config file."""
        cr = wg_conf_fmt.parse(_RESOURCES["wg-mock.conf"])
        assert len(cr.peers) == 2

    @mark.parametrize(
        ("content", "pattern"),
        [
            (  # no sections
                '{"created": "1984-10-21"}',
                "invalid WireGuard configuration",
            ),
            (  # invalid [Interface] section
                "\n".join(
                    [
                        "#header",
                        "[Interface]",
                        "PrivateKey=" + WG_TEST_KEYS[0].private,
                    ]
                ),
                r"missing required fields.*\[Interface\]",
            ),
            (  # invalid [Peer] section
                "\n".join(
                    [
                        "[Interface]",
                        "PrivateKey=" + WG_TEST_KEYS[0].private,
                        "Address=10.0.0.1/8",
                        "ListenPort=2015",
                        "[Peer]",
                    ]
                ),
                r"missing required fields.*\[Peer\]",
            ),
            (  # Config validation error
                "\n".join(
                    [
                        "[Interface]",
                        "PrivateKey=" + WG_TEST_KEYS[0].private,
                        "Address=192.168.86.1/24",
                        "ListenPort=Lobster",
                    ]
                ),
                "invalid configuration",
            ),
            (  # Peer validation error
                "\n".join(
                    [
                        "[Interface]",
                        "PrivateKey=" + WG_TEST_KEYS[0].private,
                        "Address=10.0.0.1/8",
                        "ListenPort=2015",
                        "[Peer]",
                        "PublicKey=" + WG_TEST_KEYS[1].public,
                        "AllowedIPs=FA20D",
                    ]
                ),
                "invalid configuration",
            ),
            (  # ConfigParser parsing error
                "#header\n[Interface]\n[",
                "parsing error",
            ),
            (  # missing [Interface] section
                "\n".join(
                    [
                        "[Peer]",
                        "PublicKey=" + WG_TEST_KEYS[1].public,
                        "AllowedIPs=10.168.0.2/32",
                    ]
                ),
                r"\[Interface\] section not found",
            ),
            (  # more than one [Interface] section
                "[Interface]\n[Interface]",
                r"more than one \[Interface\]",
            ),
        ],
    )
    def test_invalid_parse(self, content, wg_conf_fmt, pattern):
        """Test parsing an invalid WireGuard config file."""
        match = re.compile(pattern, re.DOTALL)
        with raises(ConfigFormatError, match=match):
            wg_conf_fmt.parse(content)

    def test_format(self, wg_conf_fmt):
        """Test formatting into a WireGuard conf file."""
        cr_params = json.loads(_RESOURCES["wg-mock.json"])
        cr = ConfigRoot(**cr_params)
        formatted = wg_conf_fmt.format(cr)
        assert formatted == _RESOURCES["wg-mock.conf"]

    def test_format_peer(self, wg_conf_fmt):
        """Test formatting into a WireGuard conf file."""
        cr_params = json.loads(_RESOURCES["wg-mock.json"])
        cr = ConfigRoot(**cr_params)
        peer = next(filter(lambda p: p.name == "Phone", cr.peers))
        formatted = wg_conf_fmt.format_peer(cr, peer)
        assert formatted == _RESOURCES["wg-peer-mock.conf"]
