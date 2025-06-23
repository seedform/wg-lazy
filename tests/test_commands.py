"""Test data store."""


import json
from contextlib import nullcontext as success
from types import SimpleNamespace

from pytest import fixture, mark, raises
from utils import MockConfigDataStore, load_resource

from wg_lazy.cmd import Add, CommandError, New, Rm, parse_cmdline
from wg_lazy.conf import AppConfigService, WgConfigService

_RESOURCES = {
    "wg-mock.conf": load_resource("wg-mock.conf"),
    "wg-mock.json": load_resource("wg-mock.json"),
    "wg-peer-mock.conf": load_resource("wg-peer-mock.conf"),
}


def test_parse_cmdline():
    """Test parsing the command line."""
    ns = parse_cmdline(
        ["test", "-d", "test-dir", "-vv", "new", "-a", "example.com:8192"],
        prog="test",
        version="0.0.0-test",
    )
    assert vars(ns) == {
        "config_dir": "test-dir",
        "interface_name": "wg0",
        "log_level": 2,
        "sub_command": "new",
        "public_address": "example.com:8192",
        "dns": "1.1.1.1",
        "listen_port": 51820,
    }


class TestNewCommand:
    """Tests for the "new" command."""

    @fixture
    def args_bundle(self):
        """Return valid partial parameters for initialization."""
        app_ds = MockConfigDataStore()
        wg_ds = MockConfigDataStore()
        args = dict(
            public_address="example.com:2824",
            listen_port=9015,
            dns="10.168.0.1",
            force=False,
            interface_name="wg-mock",
            app_config_service=AppConfigService(app_ds),
            wg_config_service=WgConfigService(wg_ds),
        )
        return SimpleNamespace(app_ds=app_ds, wg_ds=wg_ds, args=args)

    @mark.parametrize(
        ("overwrite", "expectation"),
        [
            (True, success()),  # overwrite
            (False, raises(CommandError)),  # don't overwrite
        ],
    )
    def test_run_overwrite(self, overwrite, expectation, args_bundle):
        """Test initialization with valid arguments."""
        args_bundle.app_ds.existent = True
        args_bundle.wg_ds.existent = True
        args_bundle.args["force"] = overwrite
        with expectation:
            New(**args_bundle.args).run()

    def test_run(self, args_bundle):
        """Test running the command."""
        with success():
            New(**args_bundle.args).run()


class TestAddCommand:
    """Tests for the "add" command."""

    @fixture
    def args_bundle(self):
        """Return valid partial parameters for initialization."""
        app_ds = MockConfigDataStore(content=_RESOURCES["wg-mock.json"])
        wg_ds = MockConfigDataStore(content=_RESOURCES["wg-mock.conf"])
        app_ds.existent = True
        args = dict(
            peer_name="Test Peer",
            save_private_key=True,
            output_format="-",
            force=False,
            interface_name="wg-mock",
            app_config_service=AppConfigService(app_ds),
            wg_config_service=WgConfigService(wg_ds),
        )
        return SimpleNamespace(app_ds=app_ds, wg_ds=wg_ds, args=args)

    def test_invalid_run_no_config(self, args_bundle):
        """Test with no configuration available."""
        args_bundle.app_ds.existent = False
        with raises(CommandError, match="configuration not found"):
            Add(**args_bundle.args).run()

    @mark.parametrize(
        ("peer_name", "overwrite", "expectation"),
        [
            # overwrite success
            ("Phone", True, success()),
            # no conflict
            ("Toaster", False, success()),
            # no name supplied
            (None, False, success()),
            # overwrite fail
            ("Phone", False, raises(CommandError, match="exists")),
        ],
    )
    def test_run_overwrite(
        self, peer_name, overwrite, expectation, args_bundle
    ):
        """Test overwriting a peer."""
        args_bundle.args["peer_name"] = peer_name
        args_bundle.args["force"] = overwrite
        with expectation:
            Add(**args_bundle.args).run()

    @mark.parametrize(
        ("save_private_key", "check_func"),
        [
            (True, lambda key: key is not None),  # save private key
            (False, lambda key: key is None),  # don't save private key
        ],
    )
    def test_run_save_private_key(
        self, save_private_key, check_func, args_bundle
    ):
        """Test saving a new peer's private key."""
        args_bundle.args["save_private_key"] = save_private_key
        Add(**args_bundle.args).run()
        peers_filtered = filter(
            lambda p: p["Name"] == args_bundle.args["peer_name"],
            json.loads(args_bundle.app_ds.read())["Peers"],
        )
        peer = list(peers_filtered)[0]
        assert check_func(peer.get("PrivateKey", None))

    @mark.parametrize(
        ("term_dims", "config_exists", "expectation"),
        [
            # valid
            ((80, 40), True, success()),
            # invalid terminal size
            ((80, 39), True, raises(CommandError, match="terminal size")),
        ],
    )
    def test_run_output_qr(
        self, term_dims, config_exists, expectation, args_bundle, mocker
    ):
        """Test QR output."""
        from wg_lazy.cmd import add

        args_bundle.args["output_format"] = "qr"
        mocker.patch.object(add, "get_terminal_size", return_value=term_dims)
        mocker.patch.object(add.stdout, "isatty", return_value=True)
        mocked = mocker.patch.object(add, "pager")
        with expectation:
            Add(**args_bundle.args).run()
            assert "scan this" in str(mocked.call_args)


class TestRmCommand:
    """Test for the "rm" command."""

    @fixture
    def args_bundle(self):
        """Return valid partial parameters for initialization."""
        app_ds = MockConfigDataStore(content=_RESOURCES["wg-mock.json"])
        wg_ds = MockConfigDataStore(content=_RESOURCES["wg-mock.conf"])
        app_ds.existent = True
        args = dict(
            interface_name="wg-mock",
            peer_name="Phone",
            force=False,
            app_config_service=AppConfigService(app_ds),
            wg_config_service=WgConfigService(wg_ds),
        )
        return SimpleNamespace(app_ds=app_ds, wg_ds=wg_ds, args=args)

    def test_invalid_config_not_found(self, args_bundle):
        """Test removing a peer with a non-existent configuration."""
        args_bundle.app_ds.existent = False
        with raises(CommandError, match="configuration not found"):
            Rm(**args_bundle.args).run()

    def test_invalid_peer_not_found(self, args_bundle):
        """Test removing a peer that does not exist."""
        args_bundle.args["peer_name"] = "Toaster"
        with raises(CommandError, match="peer not found"):
            Rm(**args_bundle.args).run()

    def test_run(self, args_bundle):
        """Test removing a peer."""
        args_bundle.args["peer_name"] = "Phone"
        with success():
            Rm(**args_bundle.args).run()
            updated_config = json.loads(args_bundle.app_ds.read())
            assert len(updated_config["Peers"]) == 1
