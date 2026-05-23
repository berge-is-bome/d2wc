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
from d2wc.cli_target_rules import add_target_rule_subcommands
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
from d2wc.core.placement_operations import (
    PlacementOperationError,
    PlacementRuleExistsError,
    PlacementRuleNotFoundError,
    add_placement_rule_to_source,
    delete_placement_rule_from_source,
    modify_placement_rule_in_source,
)
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.route_operations import (
    RouteOperationError,
    RouteRuleExistsError,
    RouteRuleNotFoundError,
    add_route_rule_to_source,
    delete_route_rule_from_source,
    modify_route_rule_in_source,
)
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
    _add_common_write_arguments(delete_geom)
    delete_geom.set_defaults(func=_cmd_delete_geom)

    add_placement = subcommands.add_parser(
        "add-placement",
        help="Preview or add one WORKSPACE_PLACEMENT rule. Writes only when --write is supplied.",
    )
    add_placement.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    add_placement.add_argument("--rule", required=True, help="Placement rule to add, for example c:okular g:half_left.")
    _add_common_write_arguments(add_placement)
    add_placement.set_defaults(func=_cmd_add_placement)

    modify_placement = subcommands.add_parser(
        "modify-placement",
        help="Preview or modify one WORKSPACE_PLACEMENT rule. Writes only when --write is supplied.",
    )
    modify_placement.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    modify_placement.add_argument("--old-rule", required=True, help="Existing placement rule to modify.")
    modify_placement.add_argument("--new-rule", required=True, help="Replacement placement rule.")
    _add_common_write_arguments(modify_placement)
    modify_placement.set_defaults(func=_cmd_modify_placement)

    delete_placement = subcommands.add_parser(
        "delete-placement",
        help="Preview or delete one WORKSPACE_PLACEMENT rule. Writes only when --write is supplied.",
    )
    delete_placement.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_placement.add_argument("--rule", required=True, help="Placement rule to delete.")
    _add_common_write_arguments(delete_placement)
    delete_placement.set_defaults(func=_cmd_delete_placement)

    add_route = subcommands.add_parser(
        "add-route",
        help="Preview or add one WORKSPACE_ROUTES rule. Writes only when --write is supplied.",
    )
    add_route.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    add_route.add_argument("--workspace", type=int, required=True, help="Workspace number to add the rule to.")
    add_route.add_argument("--rule", required=True, help="Route rule to add, for example d:personal c:navigator.")
    _add_common_write_arguments(add_route)
    add_route.set_defaults(func=_cmd_add_route)

    modify_route = subcommands.add_parser(
        "modify-route",
        help="Preview or modify one WORKSPACE_ROUTES rule. Writes only when --write is supplied.",
    )
    modify_route.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    modify_route.add_argument("--old-rule", required=True, help="Existing route rule to modify.")
    modify_route.add_argument("--new-workspace", type=int, required=True, help="Replacement workspace number.")
    modify_route.add_argument("--new-rule", required=True, help="Replacement route rule.")
    _add_common_write_arguments(modify_route)
    modify_route.set_defaults(func=_cmd_modify_route)

    delete_route = subcommands.add_parser(
        "delete-route",
        help="Preview or delete one WORKSPACE_ROUTES rule. Writes only when --write is supplied.",
    )
    delete_route.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_route.add_argument("--rule", required=True, help="Route rule to delete.")
    _add_common_write_arguments(delete_route)
    delete_route.set_defaults(func=_cmd_delete_route)

    add_target_rule_subcommands(subcommands, _add_common_write_arguments)

    return parser


def _add_geom_common_arguments(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    subparser.add_argument("--name", required=True, help="GEOM profile name.")
    subparser.add_argument("--x", type=int, required=True, help="Window x position.")
    subparser.add_argument("--y", type=int, required=True, help="Window y position.")
    subparser.add_argument("--w", type=int, required=True, help="Window width.")
    subparser.add_argument("--h", type=int, required=True, help="Window height.")
    _add_common_write_arguments(subparser)


def _add_common_write_arguments(subparser: argparse.ArgumentParser) -> None:
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
        print(f"Planned backup archive: {preview.backup_path}")
        print(f"Planned backup member: {preview.backup_member}")
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
    print(f"Backup archive: {result.backup_path}")
    print(f"Backup member: {result.backup_member}")
    print("OK: config saved.")
    return 0


def _cmd_add_geom(args: argparse.Namespace) -> int:
    profile = GeometryProfile(name=args.name, x=args.x, y=args.y, w=args.w, h=args.h)
    return _run_geom_edit(
        args,
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_geometry_profile_to_source(source, profile),
    )


def _cmd_modify_geom(args: argparse.Namespace) -> int:
    profile = GeometryProfile(name=args.name, x=args.x, y=args.y, w=args.w, h=args.h)
    return _run_geom_edit(
        args,
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_geometry_profile_in_source(source, profile),
    )


def _cmd_delete_geom(args: argparse.Namespace) -> int:
    return _run_geom_edit(
        args,
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_geometry_profile_from_source(source, args.name),
    )


def _cmd_add_placement(args: argparse.Namespace) -> int:
    return _run_placement_edit(
        args,
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_placement_rule_to_source(source, args.rule),
    )


def _cmd_modify_placement(args: argparse.Namespace) -> int:
    return _run_placement_edit(
        args,
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_placement_rule_in_source(source, args.old_rule, args.new_rule),
    )


def _cmd_delete_placement(args: argparse.Namespace) -> int:
    return _run_placement_edit(
        args,
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_placement_rule_from_source(source, args.rule),
    )


def _cmd_add_route(args: argparse.Namespace) -> int:
    return _run_route_edit(
        args,
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_route_rule_to_source(source, args.workspace, args.rule),
    )


def _cmd_modify_route(args: argparse.Namespace) -> int:
    return _run_route_edit(
        args,
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_route_rule_in_source(source, args.old_rule, args.new_workspace, args.new_rule),
    )


def _cmd_delete_route(args: argparse.Namespace) -> int:
    return _run_route_edit(
        args,
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_route_rule_from_source(source, args.rule),
    )


def _run_geom_edit(args: argparse.Namespace, operation: str, success_verb: str, edit_callback) -> int:
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
        print(f"Planned backup archive: {preview.backup_path}")
        print(f"Planned backup member: {preview.backup_member}")
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
    print(f"Backup archive: {result.backup_path}")
    print(f"Backup member: {result.backup_member}")
    print(f"OK: GEOM profile {success_verb}: {profile_name}")
    return 0


def _run_placement_edit(args: argparse.Namespace, operation: str, success_verb: str, edit_callback) -> int:
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
    except PlacementRuleExistsError as exc:
        print(f"ERROR: {exc}")
        print("Use modify-placement to update an existing WORKSPACE_PLACEMENT rule.")
        return 2
    except PlacementRuleNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    except PlacementOperationError as exc:
        print(f"ERROR: {exc}")
        return 2
    except RenderValidationError as exc:
        print(f"ERROR: cannot edit invalid config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1

    if operation == "modify":
        rule_text = edit.new_rule
        old_rule_text = edit.old_rule
    else:
        rule_text = edit.rule
        old_rule_text = None

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
        print(f"Planned backup archive: {preview.backup_path}")
        print(f"Planned backup member: {preview.backup_member}")
        print(f"Planned WORKSPACE_PLACEMENT {operation}: {rule_text}")
        if old_rule_text is not None:
            print(f"Old rule: {old_rule_text}")
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
    print(f"Backup archive: {result.backup_path}")
    print(f"Backup member: {result.backup_member}")
    print(f"OK: WORKSPACE_PLACEMENT rule {success_verb}: {rule_text}")
    return 0


def _run_route_edit(args: argparse.Namespace, operation: str, success_verb: str, edit_callback) -> int:
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
    except RouteRuleExistsError as exc:
        print(f"ERROR: {exc}")
        print("Use modify-route to update an existing WORKSPACE_ROUTES rule.")
        return 2
    except RouteRuleNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    except RouteOperationError as exc:
        print(f"ERROR: {exc}")
        return 2
    except RenderValidationError as exc:
        print(f"ERROR: cannot edit invalid config: {config_path}")
        for message in exc.validation.errors:
            print(f"- {message}")
        return 1

    if operation == "modify":
        rule_text = edit.new_rule
        workspace = edit.new_workspace
        old_rule_text = edit.old_rule
        old_workspace = edit.old_workspace
    else:
        rule_text = edit.rule
        workspace = edit.workspace
        old_rule_text = None
        old_workspace = None

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
        print(f"Planned backup archive: {preview.backup_path}")
        print(f"Planned backup member: {preview.backup_member}")
        print(f"Planned WORKSPACE_ROUTES {operation}: workspace={workspace} rule={rule_text}")
        if old_rule_text is not None:
            print(f"Old workspace: {old_workspace}")
            print(f"Old rule: {old_rule_text}")
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
    print(f"Backup archive: {result.backup_path}")
    print(f"Backup member: {result.backup_member}")
    print(f"OK: WORKSPACE_ROUTES rule {success_verb}: workspace={workspace} rule={rule_text}")
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
