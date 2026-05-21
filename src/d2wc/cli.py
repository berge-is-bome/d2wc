"""Command-line interface for d2wc.

The first implementation phase is intentionally conservative. Commands that can
write a Lua configuration must require an explicit affirmative flag and must use
the tested safe-save core path.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from d2wc import __version__
from d2wc.core.geom_operations import (
    GeometryOperationError,
    GeometryProfileExistsError,
    GeometryProfileInUseError,
    GeometryProfileNotFoundError,
    add_geometry_profile_to_source,
    delete_geometry_profile_from_source,
    modify_geometry_profile_in_source,
)
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.managed_config import GeometryProfile
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.saving import (
    SaveConfigError,
    SaveValidationError,
    preview_save_config,
    preview_source_save_config,
    save_rendered_config,
    save_source_config,
)
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

    save = subcommands.add_parser(
        "save",
        help="Preview or save rendered Lua config. Writes only when --write is supplied.",
    )
    save.add_argument("--config", type=Path, required=True, help="Path to the Lua config to save.")
    save.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Optional directory for timestamped backups. Defaults to the config directory.",
    )
    save.add_argument("--write", action="store_true", help="Actually write after validation and backup.")
    save.set_defaults(func=_cmd_save)

    add_geom = subcommands.add_parser(
        "add-geom",
        help="Preview or add one new GEOM profile. Writes only when --write is supplied.",
    )
    _add_geom_common_arguments(add_geom)
    add_geom.set_defaults(func=_cmd_add_geom)

    modify_geom = subcommands.add_parser(
        "modify-geom",
        help="Preview or modify one existing GEOM profile. Writes only when --write is supplied.",
    )
    _add_geom_common_arguments(modify_geom)
    modify_geom.set_defaults(func=_cmd_modify_geom)

    delete_geom = subcommands.add_parser(
        "delete-geom",
        help="Preview or delete one unused GEOM profile. Writes only when --write is supplied.",
    )
    delete_geom.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_geom.add_argument("--name", required=True, help="GEOM profile name to delete.")
    delete_geom.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Optional directory for timestamped backups. Defaults to the config directory.",
    )
    delete_geom.add_argument("--write", action="store_true", help="Actually write after validation and backup.")
    delete_geom.set_defaults(func=_cmd_delete_geom)

    return parser


def _add_geom_common_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    subparser.add_argument("--name", required=True, help="GEOM profile name.")
    subparser.add_argument("--x", type=int, required=True, help="Window x position.")
    subparser.add_argument("--y", type=int, required=True, help="Window y position.")
    subparser.add_argument("--w", type=int, required=True, help="Window width.")
    subparser.add_argument("--h", type=int, required=True, help="Window height.")
    subparser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="Optional directory for timestamped backups. Defaults to the config directory.",
    )
    subparser.add_argument("--write", action="store_true", help="Actually write after validation and backup.")


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


def _cmd_save(args: argparse.Namespace) -> int:
    config_path: Path = args.config

    if not args.write:
        try:
            preview = preview_save_config(config_path, backup_dir=args.backup_dir)
        except SaveValidationError as exc:
            print(f"ERROR: cannot preview invalid config: {config_path}")
            for message in exc.validation.errors:
                print(f"- {message}")
            return 1
        except SaveConfigError as exc:
            print(f"ERROR: could not preview save: {exc}")
            return 2
        except OSError as exc:
            print(f"ERROR: could not preview save: {exc}")
            return 2

        print(f"Config: {preview.config_path}")
        print(f"Planned backup: {preview.backup_path}")
        print(f"Rendered bytes: {preview.bytes_written}")
        print("Preview only: no files were modified.")
        print("Run again with --write to save.")
        return 0

    try:
        result = save_rendered_config(config_path, backup_dir=args.backup_dir)
    except SaveValidationError as exc:
        print(f"ERROR: cannot save invalid config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1
    except SaveConfigError as exc:
        print(f"ERROR: could not save config: {exc}")
        return 2
    except OSError as exc:
        print(f"ERROR: could not save config: {exc}")
        return 2

    print(f"Config: {result.config_path}")
    print(f"Backup: {result.backup_path}")
    print("OK: config saved.")
    return 0


def _cmd_add_geom(args: argparse.Namespace) -> int:
    profile = GeometryProfile(name=args.name, x=args.x, y=args.y, w=args.w, h=args.h)
    return _run_geom_edit(
        args,
        operation="add",
        edit_callback=lambda source: add_geometry_profile_to_source(source, profile),
    )


def _cmd_modify_geom(args: argparse.Namespace) -> int:
    profile = GeometryProfile(name=args.name, x=args.x, y=args.y, w=args.w, h=args.h)
    return _run_geom_edit(
        args,
        operation="modify",
        edit_callback=lambda source: modify_geometry_profile_in_source(source, profile),
    )


def _cmd_delete_geom(args: argparse.Namespace) -> int:
    return _run_geom_edit(
        args,
        operation="delete",
        edit_callback=lambda source: delete_geometry_profile_from_source(source, args.name),
    )


def _run_geom_edit(args: argparse.Namespace, operation: str, edit_callback) -> int:
    config_path: Path = args.config

    try:
        source = config_path.read_text(encoding="utf-8")
        edit = edit_callback(source)
    except FileNotFoundError:
        print(f"ERROR: config file not found: {config_path}")
        return 2
    except OSError as exc:
        print(f"ERROR: could not read config file {config_path}: {exc}")
        return 2
    except GeometryProfileExistsError as exc:
        print(f"ERROR: {exc}")
        print("Use modify-geom to update an existing GEOM profile.")
        return 2
    except GeometryProfileNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    except GeometryProfileInUseError as exc:
        print(f"ERROR: {exc}")
        print("Remove or change the WORKSPACE_PLACEMENT rule before deleting this profile.")
        return 2
    except GeometryOperationError as exc:
        print(f"ERROR: {exc}")
        return 2
    except RenderValidationError as exc:
        print(f"ERROR: cannot edit invalid config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1

    profile_name = getattr(edit, "profile_name", None) or edit.profile.name

    if not args.write:
        try:
            preview = preview_source_save_config(config_path, edit.source, backup_dir=args.backup_dir)
        except SaveValidationError as exc:
            print(f"ERROR: cannot preview invalid edited config: {config_path}")
            for message in exc.validation.errors:
                print(f"- {message}")
            return 1
        except SaveConfigError as exc:
            print(f"ERROR: could not preview save: {exc}")
            return 2
        except OSError as exc:
            print(f"ERROR: could not preview save: {exc}")
            return 2

        print(f"Config: {preview.config_path}")
        print(f"Planned backup: {preview.backup_path}")
        print(f"Planned GEOM {operation}: {profile_name}")
        if operation != "delete":
            profile = edit.profile
            print(f"Geometry: x={profile.x} y={profile.y} w={profile.w} h={profile.h}")
        print(f"Rendered bytes: {preview.bytes_written}")
        print("Preview only: no files were modified.")
        print("Run again with --write to save.")
        return 0

    try:
        result = save_source_config(config_path, edit.source, backup_dir=args.backup_dir, validation=edit.validation)
    except SaveValidationError as exc:
        print(f"ERROR: cannot save invalid edited config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1
    except SaveConfigError as exc:
        print(f"ERROR: could not save config: {exc}")
        return 2
    except OSError as exc:
        print(f"ERROR: could not save config: {exc}")
        return 2

    print(f"Config: {result.config_path}")
    print(f"Backup: {result.backup_path}")
    print(f"OK: GEOM profile {operation}d: {profile_name}")
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
