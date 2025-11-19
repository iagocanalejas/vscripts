import argparse
from pathlib import Path

import vscripts.constants as C
from vscripts import cli
from vscripts.reporters.errors import error_handler
from vscripts.reporters.logs import logging_handler
from vscripts.reporters.output import print_logo


def main() -> int:
    parser = argparse.ArgumentParser(prog="VScripts", description="Video edition tool.")

    # https://stackoverflow.com/a/8521644/812183
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {C.VERSION}",
    )

    def _add_cmd(name: str, *, help: str) -> argparse.ArgumentParser:
        parser = subparsers.add_parser(name, help=help)
        return parser

    subparsers = parser.add_subparsers(dest="command")
    _cmd_do(_add_cmd("do", help="Run the given instructions on a file."))
    args = parser.parse_args()

    print_logo()

    with error_handler(), logging_handler(True):
        if not hasattr(args, "func"):
            parser.print_help()
            return 1

        if args.command == "do":
            return cli.cmd_do(
                Path(args.path),
                actions=args.actions,
                output=Path(args.output) if args.output else None,
                force_detection=args.force_detection,
                translation_mode=args.translation_mode,
            )
        else:
            parser.print_help()
            return 1


def _cmd_do(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("path", help="path to be handled")
    parser.add_argument("actions", type=str, nargs="*", help="list of actions to be ran")
    parser.add_argument("--force-detection", action="store_true", help="Force overwrite of metadata.", default=False)
    parser.add_argument(
        "--translation-mode",
        choices=["google", "local"],
        help="Choose translation backend: 'google' or 'local'.",
        default="local",
    )
    parser.set_defaults(func=cli.cmd_do)

    _set_io(parser)
    return parser


def _set_io(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument("-o", "--output", type=str, help="Output file name.", default=None)
    return parser
