"""Configuration service tests."""

import json
from contextlib import nullcontext as success
from os import chmod
from pathlib import Path

from freezegun import freeze_time
from pytest import fixture, mark, raises
from utils import MockConfigDataStore, load_resource

from wg_lazy.conf import (
    AppConfigService,
    ConfigRoot,
    WgConfigService,
    create_fs_app_config_service,
    create_fs_wg_config_service,
)

_RESOURCES = {
    "wg-mock.conf": load_resource("wg-mock.conf"),
    "wg-mock.json": load_resource("wg-mock.json"),
    "wg-peer-mock.conf": load_resource("wg-peer-mock.conf"),
}


class TestAppConfigService:
    """AppConfigService class tests."""

    @fixture
    def mock_ds(self):
        """Return a valid mock data store."""
        return MockConfigDataStore()

    @fixture
    def auto_chmod_tmp_path(self, tmp_path):
        """Fix tmp_path permissions before pytest cleans up."""
        yield tmp_path
        chmod(tmp_path, 0o0700)

    @mark.parametrize(
        ("sub_dir", "perms", "expectation"),
        [
            # successful creation
            (".", 0o0750, success()),
            # invalid permissions
            ("inaccessible", 0o0000, raises(PermissionError)),
            # directory not found
            ("not-found", 0o0750, raises(FileNotFoundError)),
        ],
    )
    def test_construction_fs(self, sub_dir, perms, expectation, tmp_path):
        """Test file-based service construction function."""
        base_dir = Path(tmp_path) / "test"
        base_dir.mkdir(mode=perms)
        config_dir = base_dir / sub_dir
        with expectation:
            svc = create_fs_app_config_service(config_dir, "wg0")
            assert isinstance(svc, AppConfigService)
        chmod(base_dir, 0o0700)  # fix permissions for pytest cleanup

    def test_exists(self, mock_ds):
        """Test backing store existence."""
        mock_ds.existent = True
        app_config_service = AppConfigService(config_ds=mock_ds)
        assert app_config_service.exists()

    def test_read(self, mock_ds):
        """Test reading an app config file."""
        mock_ds.content = _RESOURCES["wg-mock.json"]
        app_config_service = AppConfigService(config_ds=mock_ds)
        app_config = app_config_service.read()
        assert len(app_config.peers) == 2

    def test_write(self, mock_ds):
        """Test writing an app config file."""
        app_config_service = AppConfigService(config_ds=mock_ds)
        config_json = json.loads(_RESOURCES["wg-mock.json"])
        config = ConfigRoot(**config_json)
        app_config_service.write(config)
        expected_json = json.loads(_RESOURCES["wg-mock.json"])
        actual_json = json.loads(mock_ds.read())
        assert actual_json == expected_json


@freeze_time("2077-12-31 00:00:00", tz_offset=-5)  # EST
class TestWgConfigService:
    """WgConfigService class tests."""

    @fixture
    def mock_ds(self):
        """Return a valid mock data store."""
        return MockConfigDataStore()

    @mark.parametrize(
        ("sub_dir", "perms", "expectation"),
        [
            # successful creation
            (".", 0o0750, success()),
            # invalid permissions
            ("inaccessible", 0o0000, raises(PermissionError)),
            # directory not found
            ("not-found", 0o0750, raises(FileNotFoundError)),
        ],
    )
    def test_construction_fs(self, sub_dir, perms, expectation, tmp_path):
        """Test file-based service construction function."""
        base_dir = Path(tmp_path) / "test"
        base_dir.mkdir(mode=perms)
        config_dir = base_dir / sub_dir
        with expectation:
            svc = create_fs_wg_config_service(config_dir, "wg0")
            assert isinstance(svc, WgConfigService)
        chmod(base_dir, 0o0700)  # fix permissions for pytest cleanup

    def test_exists(self, mock_ds):
        """Test backing store existence."""
        mock_ds.existent = True
        wg_config_service = WgConfigService(config_ds=mock_ds)
        assert wg_config_service.exists()

    def test_read(self, mock_ds):
        """Test reading a WireGuard config file."""
        mock_ds.content = _RESOURCES["wg-mock.conf"]
        wg_config_service = WgConfigService(config_ds=mock_ds)
        wg_config = wg_config_service.read()
        assert len(wg_config.peers) == 2

    def test_write(self, mock_ds):
        """Test writing a WireGuard config file."""
        wg_config_service = WgConfigService(config_ds=mock_ds)
        config_json = json.loads(_RESOURCES["wg-mock.json"])
        config = ConfigRoot(**config_json)
        wg_config_service.write(config)
        assert mock_ds.read() == _RESOURCES["wg-mock.conf"]

    def test_generate_peer_config(self, mock_ds):
        """Test that peer configuration is generated successfully."""
        app_config_json = json.loads(_RESOURCES["wg-mock.json"])
        config = ConfigRoot(**app_config_json)
        peer = next(filter(lambda p: p.name == "Phone", config.peers))
        wg_config_service = WgConfigService(config_ds=mock_ds)
        peer_conf = wg_config_service.generate_peer_config(config, peer)
        assert peer_conf == _RESOURCES["wg-peer-mock.conf"]
