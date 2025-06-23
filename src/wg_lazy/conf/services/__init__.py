"""Configuration file services."""

from pathlib import Path as _Path
from typing import TypeVar

from ..datastores import FsConfigDataStore as _DataStore
from .appconfig import AppConfigService
from .wgconfig import WgConfigService

__all__ = [
    "AppConfigService",
    "WgConfigService",
    "create_fs_app_config_service",
    "create_fs_wg_config_service",
]

_ConfigService = TypeVar("_ConfigService", AppConfigService, WgConfigService)


def _create_file_config_service(
    service_cls: type[_ConfigService],
    config_dir: _Path | str,
    interface_name: str,
    ext: str,
) -> _ConfigService:
    """Create and return a file-based configuration service.

    Args:
        service_cls: Configuration service class.
        config_dir: Path to configuration directory.
        interface_name: WireGuard interface name.
        ext: Filename extension.

    Returns:
        Configuration service with preconfigurfed data store.

    Raises:
        PermissionError: No access to configuration directory.
        FileNotFoundError: Configuration directory not found.
    """
    config_dir = _Path(config_dir)
    if not config_dir.exists():
        raise FileNotFoundError(f"No such directory: {config_dir}")
    config_path = config_dir / f"{interface_name}.{ext}"
    ds = _DataStore(config_path)
    return service_cls(config_ds=ds)


def create_fs_app_config_service(
    config_dir: _Path | str, interface_name: str
) -> AppConfigService:
    """Construct a file-based AppConfigService instance.

    Args:
        config_dir: Path to WireGuard configuration file directory.
        interface_name: WireGuard interface name to operate on.

    Returns:
        Configuration service for managing configuration files used
        by this app.

    Raises:
        PermissionError: No access to configuration directory.
        FileNotFoundError: Configuration directory not found.
    """
    service = _create_file_config_service(
        AppConfigService, config_dir, interface_name, "json"
    )
    return service


def create_fs_wg_config_service(
    config_dir: _Path | str, interface_name: str
) -> WgConfigService:
    """Construct a file-based WgConfigService instance.

    Args:
        config_dir: Path to WireGuard configuration file directory.
        interface_name: WireGuard interface name to operate on.

    Returns:
        Configuration service for creating and managing configuration
        files compatible with wg-quick.

    Raises:
        PermissionError: No access to configuration directory.
        FileNotFoundError: Configuration directory not found.
    """
    service = _create_file_config_service(
        WgConfigService, config_dir, interface_name, "conf"
    )
    return service
