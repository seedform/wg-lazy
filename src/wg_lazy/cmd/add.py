"""New peer command."""

import logging
from io import StringIO
from pydoc import pager
from shutil import get_terminal_size
from sys import stdout

import qrcode  # type: ignore[import-untyped]

from wg_lazy.conf import (
    ConfigDataStoreError,
    ConfigFormatError,
    ConfigRoot,
    ConfigValidationError,
    PeerValidationError,
)
from wg_lazy.consts import defaults, limits
from wg_lazy.utils import raise_as

from .base import BaseCommand, CommandError

LOG = logging.getLogger(__name__)


class Add(BaseCommand):
    """Add a new peer to an existing tunnel."""

    def __init__(
        self,
        *args,
        peer_name=None,
        save_private_key=False,
        output_format=defaults.OUTPUT_FORMAT,
        force=False,
        **kwargs,
    ):
        """Initialize command.

        Args:
            peer_name: Name of the new peer to be added.
            save_private_key: Save the new peer's private key if True.
            output_format: "qr" to generate a QR code or "-" for stdout.
            force: Overwrite peer with the same name.
            args: Positional args sent to parent class.
            kwargs: Keyword args sent to parent class.
        """
        super().__init__(*args, **kwargs)
        self.peer_name = peer_name
        self.save_private_key = save_private_key
        self.output_format = output_format
        self.force = force

    # overridden
    @raise_as(
        CommandError,
        catch=(
            ConfigValidationError,
            PeerValidationError,
            ConfigDataStoreError,
            ConfigFormatError,
        ),
    )
    def run(self):
        """Run this command."""
        self._check_config_exists()
        self._check_term_size()

        LOG.info(
            "reading app configuration for WireGuard interface: %s",
            self.interface_name,
        )
        config = self.app_config_service.read()

        LOG.info(
            "creating new peer%s",
            f" with name: {self.peer_name}" if self.peer_name else "",
        )
        peer = config.create_peer(name=self.peer_name)

        self._resolve_name_conflicts(config)

        LOG.info("adding new peer: %s", str(peer))
        config.add_peer(peer)

        LOG.info("generating peer configuration")
        peer_conf = self.wg_config_service.generate_peer_config(config, peer)

        # don't save private key unless explicitly requested
        peer.private_key = peer.private_key if self.save_private_key else None
        self.sync(config)

        if self.output_format == "qr":
            self._print_qr(peer_conf, self.save_private_key)
        else:
            print(peer_conf.strip())

    @raise_as(CommandError, catch=ConfigDataStoreError)
    def _check_config_exists(self):
        LOG.debug("checking for existing configuration")
        if not self.app_config_service.exists():
            msg = (
                "app configuration not found for interface: "
                f"{self.interface_name}"
            )
            raise CommandError(msg)

    def _check_term_size(self):
        if self.output_format.lower() != "qr" or not stdout.isatty():
            LOG.debug("skipped checking terminal size")
            return True
        LOG.debug("checking terminal size")
        columns, lines = get_terminal_size()
        bad_cols = columns < limits.TERM_MIN_COLMS
        bad_lines = lines < limits.TERM_MIN_LINES
        invalid_term_size = bad_cols or bad_lines
        if invalid_term_size:
            msg = (
                f"Terminal size must be at least {limits.TERM_MIN_COLMS} "
                f"columns by {limits.TERM_MIN_LINES} lines to display QR "
                f"codes. Current terminal size is {columns} columns by "
                f'{lines} lines. Use "--output=-" to output configuration '
                " as text instead."
            )
            raise CommandError(msg)

    def _resolve_name_conflicts(self, config: ConfigRoot):
        if not self.peer_name:
            LOG.debug("skipping name conflict resolution (no name specified)")
            return

        existing_peer = config.get_peer_by_name(self.peer_name)
        if not existing_peer:
            LOG.debug("skipping name conflict resolution (no conflict)")
            return

        if self.force:
            LOG.info("replacing peer with name: %s", self.peer_name)
            config.remove_peer(existing_peer)
            return

        msg = (
            f"peer already exists: {self.peer_name} (use --force to overwrite)"
        )
        raise CommandError(msg)

    def _print_qr(self, content: str, save_private_key: bool):
        """Display a QR code containing exported peer configuration."""
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(content)
        qr.make(fit=True)

        # This horror exists to force the qrcode library's print_ascii
        # method into writing to a non tty stream. The QR code can then
        # be displayed via the pydoc pager.
        out_stream = StringIO()
        out_stream.isatty = lambda: True  # type: ignore[method-assign]
        qr.print_ascii(out=out_stream, tty=True, invert=True)
        out_stream.seek(0)

        trailer = "Use the WireGuard app to scan this QR code."
        pager_txt = "\n".join([out_stream.read(), trailer])
        pager(pager_txt)
