"""Configuration base classes and interfaces."""

from .datastore import BaseConfigDataStore, ConfigDataStoreError
from .format import BaseConfigFormat, ConfigFormatError
from .formatter import BaseConfigFormatter, ConfigFormatterError
from .models import (
    BaseConfigModel,
    BaseModelError,
    ConfigRoot,
    ConfigValidationError,
    Peer,
    PeerValidationError,
)
from .parser import BaseConfigParser, ConfigParserError
from .service import BaseConfigService

__all__ = [
    # models
    "BaseConfigModel",
    "BaseModelError",
    "ConfigRoot",
    "ConfigValidationError",
    "Peer",
    "PeerValidationError",
    # datastore
    "BaseConfigDataStore",
    "ConfigDataStoreError",
    # format
    "BaseConfigFormat",
    "ConfigFormatError",
    # formatter
    "BaseConfigFormatter",
    "ConfigFormatterError",
    # parser
    "BaseConfigParser",
    "ConfigParserError",
    # service
    "BaseConfigService",
]
