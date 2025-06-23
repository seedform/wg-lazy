"""Test data store."""


from os import chmod

from pytest import fixture, mark, raises

from wg_lazy.conf import ConfigDataStoreError, FsConfigDataStore


class TestFsConfigDataStore:
    """Test FsConfigDataStore operations."""

    @fixture
    def auto_chmod_tmp_path(self, tmp_path):
        """Fix tmp_path permissions before pytest cleans up."""
        yield tmp_path
        chmod(tmp_path, 0o0750)

    @mark.parametrize("exists", [True, False])
    def test_exists(self, exists, auto_chmod_tmp_path):
        """Test if a config file exists or can be accessed."""
        config_file_path = auto_chmod_tmp_path / "wg0.json"
        if exists:
            config_file_path.touch()
        store = FsConfigDataStore(config_file_path)
        assert store.exists() == exists

    def test_invalid_exists(self, auto_chmod_tmp_path):
        """Test that an inaccessible file raises an execption."""
        config_file_path = auto_chmod_tmp_path / "wg0.json"
        chmod(auto_chmod_tmp_path, 0o0000)
        store = FsConfigDataStore(config_file_path)
        with raises(ConfigDataStoreError, match="Permission"):
            store.exists()

    def test_read(self, tmp_path):
        """Test reading from a data store."""
        config_file_path = tmp_path / "wg0.json"
        config_file_path.touch()
        config_file_path.write_text("test")
        store = FsConfigDataStore(config_file_path)
        assert store.read() == "test"

    def test_invalid_read_nonexistent(self, tmp_path):
        """Test reading from a data store with a non-existent file."""
        config_file_path = tmp_path / "wg0.json"
        store = FsConfigDataStore(config_file_path)
        with raises(ConfigDataStoreError):
            store.read()

    def test_write(self, tmp_path):
        """Test reading from the data store."""
        config_file_path = tmp_path / "wg0.json"
        store = FsConfigDataStore(config_file_path)
        store.write("test")
        assert config_file_path.read_text("utf-8") == "test"
