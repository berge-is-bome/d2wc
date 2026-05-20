"""Command-line interface for d2wc.

The first implementation phase is intentionally read-only. Commands added here
must not modify a user's real Lua configuration until the parser, validator,
renderer, and backup safety gates exist.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from d2wc import __version__
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import ValidationResult, validate_managed_blocks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="d2wc",
        description="Devilspie2 Workspace Configurator",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"d2wc {__version__}",
    )

    subcommands = parser.add_subparsers(dest="command")

    configure = subcommands.add_parser(
        "configure",
        help="Open the configurator UI. Placeholder until the GTK proof stage.",
    )
    configure.set_defaults(func=_cmd_configure)

    validate = subcommands.add_parser(
        "validate",
        help="Read and validate managed Lua blocks without writing anything.",
    )
    validate.add_argument(
        "--config",
        type=Path,
        default=Path("src/d2wc.lua"),
        help="Path to the Lua config to validate. Defaults to src/d2wc.lua.",
    )
    validate.set_defaults(func=_cmd_validate)

    render = subcommands.add_parser(
        "render",
        help="Render managed Lua config as a dry run. Writes only to stdout.",
    )
    render.add_argument(
        "--config",
        type=Path,
        default=Path("src/d2wc.lua"),
        help="Path to the Lua config to render. Defaults to src/d2wc.lua.",
    )
    render.add_argument(
        "--stdout",
        action="store_true",
        help="Print rendered Lua to stdout. Required because render is currently dry-run only.",
    )
    render.set_defaults(func=_cmd_render)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not hasattr(args, "func"):
        parser.print_help()
        return 0

    return int(args.func(args))


def _cmd_configure(_args: argparse.Namespace) -> int:
    print("d2wc configurator UI is not implemented yet.")
    print("Next step: build parser/validator core before GTK UI work.")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    config_path: Path = args.config

    try:
        text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: config file not found: {config_path}")
        return 2
    except OSError as exc:
        print(f"ERROR: could not read config file {config_path}: {exc}")
        return 2

    parser = ManagedBlockParser()
    parse_result = parser.parse(text)
    validation = validate_managed_blocks(parse_result.blocks)

    _print_validation_result(config_path, validation)
    return 0 if validation.ok else 1


def _cmd_render(args: argparse.Namespace) -> int:
    config_path: Path = args.config

    if not args.stdout:
        print("ERROR: render is dry-run only for now; pass --stdout to print rendered Lua")
        return 2

    try:
        text = config_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"ERROR: config file not found: {config_path}")
        return 2
    except OSError as exc:
        print(f"ERROR: could not read config file {config_path}: {exc}")
        return 2

    try:
        result = render_source(text)
    except RenderValidationError as exc:
        print(f"ERROR: cannot render invalid config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1

    print(result.source, end="")
    return 0


def _print_validation_result(config_path: Path, result: ValidationResult) -> None:
    print(f"Config: {config_path}")

    if result.ok:
        print("OK: managed Lua blocks parsed and validated.")
    else:
        print("ERROR: managed Lua block validation failed.")
        for message in result.errors:
            print(f"- {message}")

    if result.warnings:
        print("WARNINGS:")
        for warning in result.warnings:
            print(f"- {warning}")
