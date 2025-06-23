"""App and WireGuard configuration facilities."""

from .base import (
    BaseConfigDataStore,
    BaseConfigFormat,
    BaseConfigService,
    BaseModelError,
    ConfigDataStoreError,
    ConfigFormatError,
    ConfigRoot,
    ConfigValidationError,
    Peer,
    PeerValidationError,
)
from .datastores import FsConfigDataStore
from .formats import JsonConfigFormat, WgQuickConfigFormat
from .services import (
    AppConfigService,
    WgConfigService,
    create_fs_app_config_service,
    create_fs_wg_config_service,
)

__all__ = [
    # models
    "BaseConfigModel",
    "ConfigRoot",
    "Peer",
    # formats
    "BaseConfigFormat",
    "JsonConfigFormat",
    "WgQuickConfigFormat",
    # data stores
    "BaseConfigDataStore",
    "FsConfigDataStore",
    # services
    "BaseConfigService",
    "AppConfigService",
    "WgConfigService",
    "create_fs_app_config_service",
    "create_fs_wg_config_service",
    # exceptions
    "BaseModelError",
    "ConfigDataStoreError",
    "ConfigFormatError",
    "ConfigValidationError",
    "PeerValidationError",
]
