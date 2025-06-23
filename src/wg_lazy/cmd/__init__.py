"""Command line interface for wg-lazy."""

from .add import Add
from .base import CommandError

# from .import_ import Import
from .cmdline import parse_cmdline
from .new import New
from .rm import Rm
from .show import Show

_cmds = [Add, New, Rm, Show]
cmd_map = {c.__name__.lower(): c for c in _cmds}

__all__ = ["CommandError", "parse_cmdline", "cmd_map"]
