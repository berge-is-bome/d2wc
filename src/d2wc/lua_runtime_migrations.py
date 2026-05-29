"""Versioned text migrations for d2wc managed Lua runtime code."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.saving import SaveConfigError, SaveValidationError, save_source_config
from d2wc.core.validation import validate_managed_blocks

HANDOFF_SETTINGS = '''-- Lua event handoff proof.
-- When enabled, supported window-open events launch the d2wc configurator.
-- The d2wc configurator window class is suppressed to avoid recursive configurator launches.
local D2WC_EVENT_HANDOFF_ENABLED = true
local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"

'''

OLD_WINDOW_TYPE_GATE = '''if (get_window_type() ~= "WINDOW_TYPE_NORMAL") then
  return
end'''

NEW_WINDOW_TYPE_GATE = '''local window_type = get_window_type()
if (window_type ~= "WINDOW_TYPE_NORMAL") then
  return
end'''

LC_HELPER = 'local function lc(s) return (s or ""):lower() end\n'

HANDOFF_HELPER = '''
local function launch_d2wc_event_handoff(event_class)
  if not D2WC_EVENT_HANDOFF_ENABLED then return end
  if event_class == D2WC_CONFIGURATOR_CLASS then return end

  os.execute("d2wc >/dev/null 2>&1 &")
end
'''

CLASS_CAPTURE = 'local cls = get_lower_class()\n'
HANDOFF_CALL = '''
------------------------------------------------------------
-- Lua event handoff proof
------------------------------------------------------------
launch_d2wc_event_handoff(cls)
'''


class LuaRuntimeMigrationError(RuntimeError):
    """Raised when a runtime migration cannot be applied safely."""


@dataclass(frozen=True)
class LuaRuntimeMigrationResult:
    """Result for one managed Lua file."""

    path: Path
    status: str
    message: str
    backup_path: Path | None = None
    backup_member: str | None = None

    @property
    def ok(self) -> bool:
        """Return whether this result should not fail the installer."""

        return self.status in {"updated", "unchanged", "skipped"}


def apply_lua_runtime_migrations(source: str) -> str:
    """Apply missing runtime-code migrations without editing existing comments."""

    migrated = source

    if "local D2WC_EVENT_HANDOFF_ENABLED" not in migrated:
        marker = "-- EXCLUDE, PIN, WORKSPACE_ROUTES, WORKSPACE_PLACEMENT, LEFT_EDGE_CORRECTION"
        index = migrated.find(marker)
        if index == -1:
            raise LuaRuntimeMigrationError("could not find user configuration marker")
        migrated = migrated[:index] + HANDOFF_SETTINGS + migrated[index:]

    if "local window_type = get_window_type()" not in migrated:
        if OLD_WINDOW_TYPE_GATE not in migrated:
            raise LuaRuntimeMigrationError("could not find supported-window gate")
        migrated = migrated.replace(OLD_WINDOW_TYPE_GATE, NEW_WINDOW_TYPE_GATE, 1)

    if "local function launch_d2wc_event_handoff" not in migrated:
        index = migrated.find(LC_HELPER)
        if index == -1:
            raise LuaRuntimeMigrationError("could not find lc helper")
        insert_at = index + len(LC_HELPER)
        migrated = migrated[:insert_at] + HANDOFF_HELPER + migrated[insert_at:]

    if "launch_d2wc_event_handoff(cls)" not in migrated:
        index = migrated.find(CLASS_CAPTURE)
        if index == -1:
            raise LuaRuntimeMigrationError("could not find class capture")
        insert_at = index + len(CLASS_CAPTURE)
        migrated = migrated[:insert_at] + HANDOFF_CALL + migrated[insert_at:]

    _validate_migrated_source(migrated)
    return migrated


def refresh_lua_runtime_file(path: Path) -> LuaRuntimeMigrationResult:
    """Apply runtime migrations to one managed Lua file."""

    path = Path(path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return LuaRuntimeMigrationResult(path, "error", f"could not read: {exc}")

    try:
        _validate_migrated_source(source)
        migrated = apply_lua_runtime_migrations(source)
    except LuaRuntimeMigrationError as exc:
        return LuaRuntimeMigrationResult(path, "skipped", str(exc))

    if migrated == source:
        return LuaRuntimeMigrationResult(path, "unchanged", "already current")

    try:
        saved = save_source_config(path, migrated)
    except SaveValidationError as exc:
        return LuaRuntimeMigrationResult(path, "error", "save validation failed: " + "; ".join(exc.validation.errors))
    except (SaveConfigError, OSError) as exc:
        return LuaRuntimeMigrationResult(path, "error", f"could not save: {exc}")

    return LuaRuntimeMigrationResult(
        path,
        "updated",
        "runtime code refreshed; existing comments and managed blocks preserved",
        saved.backup_path,
        saved.backup_member,
    )


def refresh_lua_runtime_dir(managed_dir: Path) -> tuple[LuaRuntimeMigrationResult, ...]:
    """Apply runtime migrations to every Lua file in the managed config directory."""

    managed_dir = Path(managed_dir)
    if not managed_dir.exists():
        return ()

    results: list[LuaRuntimeMigrationResult] = []
    for path in sorted(managed_dir.glob("*.lua")):
        if path.is_file() or path.is_symlink():
            results.append(refresh_lua_runtime_file(path))
    return tuple(results)


def _validate_migrated_source(source: str) -> None:
    try:
        parsed = ManagedBlockParser().parse(source)
    except ValueError as exc:
        raise LuaRuntimeMigrationError(str(exc)) from exc
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise LuaRuntimeMigrationError("managed blocks are not valid: " + "; ".join(validation.errors))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m d2wc.lua_runtime_migrations")
    parser.add_argument("managed_dir", type=Path)
    args = parser.parse_args(list(argv) if argv is not None else None)

    exit_code = 0
    for result in refresh_lua_runtime_dir(args.managed_dir):
        print(f"{result.status}: {result.path}: {result.message}")
        if result.backup_path is not None and result.backup_member is not None:
            print(f"  backup archive: {result.backup_path}")
            print(f"  backup member: {result.backup_member}")
        if result.status == "error":
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
