"""Configuration file manager for wg-quick.

TODO: Use type parameter syntax in future versions:
    https://docs.python.org/3/reference/compound_stmts.html#type-params
"""

import logging
import sys
from argparse import Namespace

from wg_lazy.cmd import CommandError, cmd_map, parse_cmdline

from .conf import create_fs_app_config_service, create_fs_wg_config_service

__version__ = "0.0.1"


LOG = logging.getLogger(__name__)


def _set_up_logging(args: Namespace):
    # set up root logger and handler
    LOG.setLevel(logging.WARNING)

    # log to stderr if user output is expected on stdout
    out_stream = sys.stdout
    if hasattr(args, "output_format") and args.output_format == "-":
        out_stream = sys.stderr
    _handler = logging.StreamHandler(out_stream)

    # use a simpler message format for INFO level logging
    _formatter = logging.Formatter("%(levelname)s - %(message)s")
    _handler.setFormatter(_formatter)
    LOG.addHandler(_handler)

    # setup logging specifics
    base_logger = logging.getLogger(__name__.split(".")[0])
    if args.log_level == 1:
        base_logger.setLevel(logging.INFO)
    elif args.log_level >= 2:
        # show slightly more detail for DEBUG logging
        base_logger.setLevel(logging.DEBUG)
        log_format = "%(levelname)s - %(name)s - %(message)s"
        for handler in base_logger.handlers:
            handler.setFormatter(logging.Formatter(log_format))


def main(argv=sys.argv) -> int:
    """Provide the main entrypoint for the y2a application.

    Args:
        argv: Command line arguments.

    Returns: 0 on success or non-zero on failure.
    """
    rc = 0
    args = parse_cmdline(argv, version=__version__)
    _set_up_logging(args)
    log = logging.getLogger(__name__)
    log.debug(args)

    if args.sub_command in cmd_map:
        try:
            app_config_service = create_fs_app_config_service(
                args.config_dir, args.interface_name
            )
            wg_config_service = create_fs_wg_config_service(
                args.config_dir, args.interface_name
            )
            cmd_cls = cmd_map[args.sub_command]
            command = cmd_cls(
                app_config_service,
                wg_config_service,
                **vars(args),
            )
            rc = command.run()
            log.info("done")
        except (PermissionError, FileNotFoundError, CommandError) as ce:
            msg = "; ".join(ce.args) if hasattr(ce, "args") else str(ce)
            if msg:
                log.error(msg)
            rc = 1
    else:
        rc = 255
    return rc


if __name__ == "__main__":
    main()


"""
Subcommands:
    init            initialize
        -f --from-file json file
    add             add a client
        -o --output  qr, file
    rm              remove a peer
        -a
    list            list all peers


"""
