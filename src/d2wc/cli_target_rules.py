"""CLI handlers for PIN, EXCLUDE, and LEFT_EDGE_CORRECTION rule edits."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

from d2wc.cli_left_edge import add_left_edge_subcommands
from d2wc.core.rendering import RenderValidationError
from d2wc.core.saving import SaveConfigError, SaveValidationError, preview_source_save_config, save_source_config
from d2wc.core.target_rule_operations import (
    TargetRuleExistsError,
    TargetRuleNotFoundError,
    TargetRuleOperationError,
    add_exclude_rule_to_source,
    add_pin_rule_to_source,
    delete_exclude_rule_from_source,
    delete_pin_rule_from_source,
    modify_exclude_rule_in_source,
    modify_pin_rule_in_source,
)


def add_target_rule_subcommands(subcommands: Any, add_common_write_arguments: Callable[[argparse.ArgumentParser], None]) -> None:
    """Register PIN, EXCLUDE, and LEFT_EDGE_CORRECTION edit commands."""

    add_pin = subcommands.add_parser(
        "add-pin",
        help="Preview or add one PIN rule. Writes only when --write is supplied.",
    )
    add_pin.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    add_pin.add_argument("--rule", required=True, help="PIN rule to add, for example d:dom0 c:xfce4-terminal.")
    add_common_write_arguments(add_pin)
    add_pin.set_defaults(func=_cmd_add_pin)

    modify_pin = subcommands.add_parser(
        "modify-pin",
        help="Preview or modify one PIN rule. Writes only when --write is supplied.",
    )
    modify_pin.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    modify_pin.add_argument("--old-rule", required=True, help="Existing PIN rule to modify.")
    modify_pin.add_argument("--new-rule", required=True, help="Replacement PIN rule.")
    add_common_write_arguments(modify_pin)
    modify_pin.set_defaults(func=_cmd_modify_pin)

    delete_pin = subcommands.add_parser(
        "delete-pin",
        help="Preview or delete one PIN rule. Writes only when --write is supplied.",
    )
    delete_pin.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_pin.add_argument("--rule", required=True, help="PIN rule to delete.")
    add_common_write_arguments(delete_pin)
    delete_pin.set_defaults(func=_cmd_delete_pin)

    add_exclude = subcommands.add_parser(
        "add-exclude",
        help="Preview or add one EXCLUDE rule. Writes only when --write is supplied.",
    )
    add_exclude.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    add_exclude.add_argument("--rule", required=True, help="EXCLUDE rule to add, for example c:qubes-app-menu.")
    add_common_write_arguments(add_exclude)
    add_exclude.set_defaults(func=_cmd_add_exclude)

    modify_exclude = subcommands.add_parser(
        "modify-exclude",
        help="Preview or modify one EXCLUDE rule. Writes only when --write is supplied.",
    )
    modify_exclude.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    modify_exclude.add_argument("--old-rule", required=True, help="Existing EXCLUDE rule to modify.")
    modify_exclude.add_argument("--new-rule", required=True, help="Replacement EXCLUDE rule.")
    add_common_write_arguments(modify_exclude)
    modify_exclude.set_defaults(func=_cmd_modify_exclude)

    delete_exclude = subcommands.add_parser(
        "delete-exclude",
        help="Preview or delete one EXCLUDE rule. Writes only when --write is supplied.",
    )
    delete_exclude.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_exclude.add_argument("--rule", required=True, help="EXCLUDE rule to delete.")
    add_common_write_arguments(delete_exclude)
    delete_exclude.set_defaults(func=_cmd_delete_exclude)

    add_left_edge_subcommands(subcommands, add_common_write_arguments)


def _cmd_add_pin(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="PIN",
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_pin_rule_to_source(source, args.rule),
    )


def _cmd_modify_pin(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="PIN",
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_pin_rule_in_source(source, args.old_rule, args.new_rule),
    )


def _cmd_delete_pin(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="PIN",
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_pin_rule_from_source(source, args.rule),
    )


def _cmd_add_exclude(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="EXCLUDE",
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_exclude_rule_to_source(source, args.rule),
    )


def _cmd_modify_exclude(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="EXCLUDE",
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_exclude_rule_in_source(source, args.old_rule, args.new_rule),
    )


def _cmd_delete_exclude(args: argparse.Namespace) -> int:
    return _run_target_rule_edit(
        args,
        section="EXCLUDE",
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_exclude_rule_from_source(source, args.rule),
    )


def _run_target_rule_edit(
    args: argparse.Namespace,
    section: str,
    operation: str,
    success_verb: str,
    edit_callback: Callable[[str], Any],
) -> int:
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
    except TargetRuleExistsError as exc:
        print(f"ERROR: {exc}")
        print(f"Use modify-{section.lower()} to update an existing {section} rule.")
        return 2
    except TargetRuleNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    except TargetRuleOperationError as exc:
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
        print(f"Planned {section} {operation}: {rule_text}")
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
    print(f"OK: {section} rule {success_verb}: {rule_text}")
    return 0
