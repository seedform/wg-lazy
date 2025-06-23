"""Configuration file formats."""

from .jsonformat import JsonConfigFormat
from .wgquickformat import WgQuickConfigFormat

__all__ = [
    "JsonConfigFormat",
    "WgQuickConfigFormat",
]
