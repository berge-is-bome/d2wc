"""CLI handlers for LEFT_EDGE_CORRECTION edits."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

from d2wc.core.left_edge_operations import (
    LeftEdgeOperationError,
    LeftEdgeRuleExistsError,
    LeftEdgeRuleNotFoundError,
    add_left_edge_rule_to_source,
    delete_left_edge_rule_from_source,
    modify_left_edge_rule_in_source,
)
from d2wc.core.rendering import RenderValidationError
from d2wc.core.saving import SaveConfigError, SaveValidationError, preview_source_save_config, save_source_config


def add_left_edge_subcommands(subcommands: Any, add_common_write_arguments: Callable[[argparse.ArgumentParser], None]) -> None:
    """Register LEFT_EDGE_CORRECTION edit commands."""

    add_left_edge = subcommands.add_parser(
        "add-left-edge",
        help="Preview or add one LEFT_EDGE_CORRECTION rule. Writes only when --write is supplied.",
    )
    add_left_edge.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    add_left_edge.add_argument(
        "--rule",
        required=True,
        help="LEFT_EDGE_CORRECTION rule to add, for example d:dom0 c:qubes-qube-manager le:pos1.",
    )
    add_common_write_arguments(add_left_edge)
    add_left_edge.set_defaults(func=_cmd_add_left_edge)

    modify_left_edge = subcommands.add_parser(
        "modify-left-edge",
        help="Preview or modify one LEFT_EDGE_CORRECTION rule. Writes only when --write is supplied.",
    )
    modify_left_edge.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    modify_left_edge.add_argument("--old-rule", required=True, help="Existing LEFT_EDGE_CORRECTION rule to modify.")
    modify_left_edge.add_argument("--new-rule", required=True, help="Replacement LEFT_EDGE_CORRECTION rule.")
    add_common_write_arguments(modify_left_edge)
    modify_left_edge.set_defaults(func=_cmd_modify_left_edge)

    delete_left_edge = subcommands.add_parser(
        "delete-left-edge",
        help="Preview or delete one LEFT_EDGE_CORRECTION rule. Writes only when --write is supplied.",
    )
    delete_left_edge.add_argument("--config", type=Path, required=True, help="Path to the Lua config to edit.")
    delete_left_edge.add_argument("--rule", required=True, help="LEFT_EDGE_CORRECTION rule to delete.")
    add_common_write_arguments(delete_left_edge)
    delete_left_edge.set_defaults(func=_cmd_delete_left_edge)


def _cmd_add_left_edge(args: argparse.Namespace) -> int:
    return _run_left_edge_edit(
        args,
        operation="add",
        success_verb="added",
        edit_callback=lambda source: add_left_edge_rule_to_source(source, args.rule),
    )


def _cmd_modify_left_edge(args: argparse.Namespace) -> int:
    return _run_left_edge_edit(
        args,
        operation="modify",
        success_verb="modified",
        edit_callback=lambda source: modify_left_edge_rule_in_source(source, args.old_rule, args.new_rule),
    )


def _cmd_delete_left_edge(args: argparse.Namespace) -> int:
    return _run_left_edge_edit(
        args,
        operation="delete",
        success_verb="deleted",
        edit_callback=lambda source: delete_left_edge_rule_from_source(source, args.rule),
    )


def _run_left_edge_edit(
    args: argparse.Namespace,
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
    except LeftEdgeRuleExistsError as exc:
        print(f"ERROR: {exc}")
        print("Use modify-left-edge to update an existing LEFT_EDGE_CORRECTION rule.")
        return 2
    except LeftEdgeRuleNotFoundError as exc:
        print(f"ERROR: {exc}")
        return 2
    except LeftEdgeOperationError as exc:
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
        print(f"Planned backup: {preview.backup_path}")
        print(f"Planned LEFT_EDGE_CORRECTION {operation}: {rule_text}")
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
    print(f"Backup: {result.backup_path}")
    print(f"OK: LEFT_EDGE_CORRECTION rule {success_verb}: {rule_text}")
    return 0
