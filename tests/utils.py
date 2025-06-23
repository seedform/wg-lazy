"""Utility functions and constants for testing."""

from pathlib import Path
from types import SimpleNamespace
from typing import TypeVar

from wg_lazy.conf import BaseConfigDataStore, ConfigDataStoreError

RESOURCES_DIR = Path(__file__).parent / "resources"
_T = TypeVar("_T")

WG_TEST_KEYS = [  # WireGuard keys for default network
    SimpleNamespace(
        private="0OJDbbB2t3bYaHC3eKnsTgTsGC8eObiwrLX5ec3cxHc=",
        public="lSsl4qOPXP1ZfcSjqPqls8FhdkfMpXmOYMoDz03Y7l4=",
        preshared="VWrgAnTn/YYh61ANsh88/u4QM2DJ6213ul+rhsj5FtQ=",
    ),
    SimpleNamespace(
        private="YEMYDcsnqbDVRU77D7OSJHvXP5gEJwNoXqVJxTP802k=",
        public="FNcSXh3/ukoV7JoXy0gMAG4TDti18JStaNfid2EGOFI=",
        preshared="RGUCzdC7mQF3vbtYMqUAYLjQa51I/N4uCNgoL2/y+yg=",
    ),
    SimpleNamespace(
        private="mBDJTXCiCqNrIcydSFW/FlY74rPFiY1HMIgF/JKko1Q=",
        public="P6sQl5YExB7inOezTLClm3wbXu4H+qcc9ZMJ8cDOh38=",
        preshared="3b2fMl7E1dh4T4QKGCRjPpJ45KqOaNgCzX3Ro30jHDU=",
    ),
    SimpleNamespace(
        private="wCKNs60eai13k4aTGQlJnR/SPUPah4DdmQuBqKrlSHc=",
        public="zXjzqvNstxsIEjNocrD2fDNIUmeILPLe1ftKBxMvHys=",
        preshared="Cx/QjpG2oj42a9hNxY26SLThcaCgGePh7/sjZ4CPu3Y=",
    ),
    SimpleNamespace(
        private="GOcHis/f70uwDdsf5Iouli+G3V8Xi3xB+lNZjg9+HX0=",
        public="oF+QkZM6WHewvYMuQSxdo1ZXdwX7luzKXETQzaGupG4=",
        preshared="4LEkU4AAWynM9HJtYxTm7bS9dzlGmU9zrd6cDuh6HaI=",
    ),
    SimpleNamespace(
        private="YGfjvdGe+EZ5pw3hocOxqgm7oaar6NiETLHg6kP3mlU=",
        public="RB4HLT1hEY3V/GxB0SGreZ843LXwuiXnMgujYoXeOgc=",
        preshared="d2iHvUUaXY6hvw993D8yjubsMEQ9/g0brKbkFcyunzI=",
    ),
]


def load_resource(filename: str) -> str:
    """Return the contents of a resource file."""
    with open(RESOURCES_DIR / filename, "rt", encoding="utf-8") as resource:
        return resource.read()


class MockConfigDataStoreError(ConfigDataStoreError):
    """Exception class for MockConfigDataStore."""


class MockConfigDataStore(BaseConfigDataStore):
    """In-memory config file store for testing."""

    def __init__(
        self,
        content="",
        existent=False,
        fail_exists=False,
        fail_read=False,
        fail_write=False,
    ):
        """Initialize with empty content.

        content: Data store content.
        existent: exists() should return True.
        fail_exists: exists() should raise ConfigDataStoreError.
        fail_read: read() should raise ConfigDataStoreError.
        fail_write: write() should raise ConfigDataStoreError.
        """
        self.content = content
        self.existent = existent
        self.fail_exists = fail_exists
        self.fail_read = fail_read
        self.fail_write = fail_write

    def _check_fail(self, check, caller):
        if check:
            raise MockConfigDataStoreError(caller)

    def exists(self) -> bool:
        """Return True if backing store exists."""
        self._check_fail(self.fail_exists, "exists()")
        return self.existent

    def read(self) -> str:
        """Return stored string."""
        self._check_fail(self.fail_read, "read()")
        return self.content

    def write(self, data) -> int:
        """Store a string."""
        self._check_fail(self.fail_write, "write()")
        self.content = data
        return len(data)
