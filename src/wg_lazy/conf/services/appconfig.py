"""Facility for managing wg-lazy configuration."""

import logging

from ..base import (
    BaseConfigDataStore,
    BaseConfigService,
)
from ..formats import JsonConfigFormat

LOG = logging.getLogger(__name__)


class AppConfigService(BaseConfigService):
    """Configuration file service for this app."""

    def __init__(self, config_ds: BaseConfigDataStore):
        """Initialize app configuration file service."""
        super().__init__(config_ds=config_ds, config_fmt=JsonConfigFormat())
