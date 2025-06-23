"""Utility methods for calling the wg executable."""

import logging
from subprocess import DEVNULL, CalledProcessError, check_output

LOG = logging.getLogger(__name__)

_WG_EXECUTABLE = "/usr/bin/wg"


def _wg_exec(subcmd, stdin=None):
    LOG.debug("subprocess: %s %s", _WG_EXECUTABLE, subcmd)
    cmd = [_WG_EXECUTABLE, subcmd]
    res = check_output(cmd, encoding="utf-8", input=stdin, stderr=DEVNULL)  # nosec
    return res.strip()


def genkey():
    """Return a new WireGuard private key."""
    return _wg_exec("genkey")


def genpsk():
    """Return a new WireGuard pre-shared key."""
    return _wg_exec("genpsk")


def pubkey(private_key):
    """Return a WireGuard public key for a given private key."""
    return _wg_exec("pubkey", stdin=private_key)


try:
    _wg_exec("version")
except CalledProcessError:
    raise SystemExit("ERROR - invalid WireGuard installation")
except FileNotFoundError:
    raise SystemExit("ERROR - could not find WireGuard tools")
