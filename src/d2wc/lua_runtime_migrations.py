"""Versioned text migrations for d2wc managed Lua runtime code."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.saving import SaveConfigError, SaveValidationError, save_source_config
from d2wc.core.validation import validate_managed_blocks

MANAGED_MARKER = "d2wc managed"
USER_CONFIG_MARKER = "-- EXCLUDE, PIN, WORKSPACE_ROUTES, WORKSPACE_PLACEMENT, LEFT_EDGE_CORRECTION"
QUBES_DOMAIN_MARKER = "------------------------------------------------------------\n-- Qubes domain and class extraction"

LATEST_VERSION_LINES = """-- version 0.1.12.6
-- changes: launch action prompt for unconfigured window events
"""
HEADER_ANCHOR = "-- devilspie2 workspace configurator\n"

HANDOFF_COMMENT_BLOCK = '''-- Lua event handoff proof.
-- When enabled, supported window-open events launch the d2wc action prompt.
-- The d2wc configurator and action-prompt window classes are suppressed to avoid recursive launches.
'''
HANDOFF_SUPPRESSION_COMMENT = "-- Windows that already match a managed target rule are suppressed.\n"
HANDOFF_ENABLED_SETTING = "local D2WC_EVENT_HANDOFF_ENABLED = true\n"
HANDOFF_CLASS_SETTING = 'local D2WC_CONFIGURATOR_CLASS = "d2wc-configurator"\n'
ACTION_PROMPT_CLASS_SETTING = 'local D2WC_ACTION_PROMPT_CLASS = "d2wc-action-prompt"\n'
HANDOFF_SETTINGS = (
    HANDOFF_COMMENT_BLOCK
    + HANDOFF_SUPPRESSION_COMMENT
    + HANDOFF_ENABLED_SETTING
    + HANDOFF_CLASS_SETTING
    + ACTION_PROMPT_CLASS_SETTING
    + "\n"
)

OLD_WINDOW_TYPE_GATE = '''if (get_window_type() ~= "WINDOW_TYPE_NORMAL") then
  return
end'''

NEW_WINDOW_TYPE_GATE = '''local window_type = get_window_type()
if (window_type ~= "WINDOW_TYPE_NORMAL") then
  return
end'''

LC_HELPER = 'local function lc(s) return (s or ""):lower() end\n'

OLD_HANDOFF_HELPER = '''
local function launch_d2wc_event_handoff(event_class)
  if not D2WC_EVENT_HANDOFF_ENABLED then return end
  if event_class == D2WC_CONFIGURATOR_CLASS then return end

  os.execute("d2wc >/dev/null 2>&1 &")
end
'''

CONFIGURATOR_HANDOFF_HELPER = '''
local function launch_d2wc_event_handoff(event_class, is_configured)
  if not D2WC_EVENT_HANDOFF_ENABLED then return end
  if event_class == D2WC_CONFIGURATOR_CLASS then return end
  if is_configured then return end

  os.execute("d2wc >/dev/null 2>&1 &")
end
'''

HANDOFF_HELPER = '''
local function shell_quote(value)
  if value == nil then return nil end
  local s = tostring(value)
  return "'" .. s:gsub("'", "'\\''") .. "'"
end

local function append_shell_arg(parts, name, value)
  if value == nil then return end
  table.insert(parts, name)
  table.insert(parts, shell_quote(value))
end

local function launch_d2wc_event_handoff(event_class, is_configured, event_domain)
  if not D2WC_EVENT_HANDOFF_ENABLED then return end
  if event_class == D2WC_CONFIGURATOR_CLASS then return end
  if event_class == D2WC_ACTION_PROMPT_CLASS then return end
  if is_configured then return end

  local x, y, w, h = get_window_geometry()
  local class_instance = get_class_instance_name()

  local command_parts = { "d2wc", "prompt" }
  append_shell_arg(command_parts, "--domain", event_domain)
  append_shell_arg(command_parts, "--application-name", event_class)
  append_shell_arg(command_parts, "--window-type", window_type)
  append_shell_arg(command_parts, "--class-instance-name", class_instance)
  append_shell_arg(command_parts, "--window-class", event_class)
  append_shell_arg(command_parts, "--window-x", x)
  append_shell_arg(command_parts, "--window-y", y)
  append_shell_arg(command_parts, "--window-width", w)
  append_shell_arg(command_parts, "--window-height", h)

  os.execute(table.concat(command_parts, " ") .. " >/dev/null 2>&1 &")
end
'''

PICK_PROFILE_HELPER_END = '''local function pick_profile(map, actual_cls)
  if not map then return nil end
  local best_p, best_r = nil, 0
  for rule_cls, prof in pairs(map) do
    local r = class_match_rank(rule_cls, actual_cls)
    if r > best_r then best_r, best_p = r, prof end
  end
  return best_p
end
'''

SUPPRESSION_HELPERS = '''
local function exact_lookup_matches_window(exact_map, domain_map, class_map, d, c)
  if d then
    local key = d .. "." .. c
    if exact_map[key] or domain_map[d] then return true end
  end
  return class_map[c] == true
end

local function rule_matches_window(rule, d, c)
  local R, ok = parse_prefixed_rule(rule)
  if not ok then return false end

  local rd, rc = R.d, R.c
  if not rd and not rc then return false end
  if rd and rd ~= d then return false end
  if rc and class_match_rank(rc, c) == 0 then return false end

  return true
end

local function list_rule_matches_window(list, d, c)
  for _, rule in ipairs(list) do
    if rule and rule ~= "" and rule_matches_window(rule, d, c) then
      return true
    end
  end
  return false
end
'''

WINDOW_HAS_MANAGED_RULE_HELPER = '''
local function window_has_managed_rule(d, c)
  if exact_lookup_matches_window(EX_EXACT, EX_DOMAIN, EX_CLASS, d, c) then return true end
  if exact_lookup_matches_window(PIN_EXACT, PIN_DOMAIN, PIN_CLASS, d, c) then return true end
  if exact_lookup_matches_window(WS_EXACT, WS_DOMAIN, WS_CLASS, d, c) then return true end
  if list_rule_matches_window(WORKSPACE_PLACEMENT, d, c) then return true end
  if list_rule_matches_window(LEFT_EDGE_CORRECTION, d, c) then return true end
  return false
end

'''

CLASS_CAPTURE = 'local cls = get_lower_class()\n'
OLD_HANDOFF_CALL = '''
------------------------------------------------------------
-- Lua event handoff proof
------------------------------------------------------------
launch_d2wc_event_handoff(cls)
'''
CONFIGURATOR_HANDOFF_CALL = '''
------------------------------------------------------------
-- Lua event handoff proof
------------------------------------------------------------
launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls))
'''
HANDOFF_CALL = '''
------------------------------------------------------------
-- Lua event handoff proof
------------------------------------------------------------
launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls), domain)
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

    migrated = _ensure_latest_header_comments(source)
    migrated = _ensure_handoff_settings(migrated)

    if "local window_type = get_window_type()" not in migrated:
        if OLD_WINDOW_TYPE_GATE not in migrated:
            raise LuaRuntimeMigrationError("could not find supported-window gate")
        migrated = migrated.replace(OLD_WINDOW_TYPE_GATE, NEW_WINDOW_TYPE_GATE, 1)

    migrated = _ensure_handoff_helper(migrated)
    migrated = _ensure_suppression_helpers(migrated)
    migrated = _ensure_window_has_managed_rule_helper(migrated)
    migrated = _ensure_handoff_call(migrated)

    _validate_migrated_source(migrated)
    return migrated


def refresh_lua_runtime_file(path: Path) -> LuaRuntimeMigrationResult:
    """Apply runtime migrations to one managed Lua file."""

    path = Path(path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        return LuaRuntimeMigrationResult(path, "error", f"could not read: {exc}")

    if MANAGED_MARKER not in source:
        return LuaRuntimeMigrationResult(path, "skipped", "missing d2wc managed marker")

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


def _ensure_latest_header_comments(source: str) -> str:
    if "-- version 0.1.12.6" in source:
        return source

    anchor_index = source.find(HEADER_ANCHOR)
    if anchor_index != -1:
        insert_at = anchor_index + len(HEADER_ANCHOR)
        return source[:insert_at] + LATEST_VERSION_LINES + source[insert_at:]

    return source


def _ensure_handoff_settings(source: str) -> str:
    migrated = source
    has_enabled = "local D2WC_EVENT_HANDOFF_ENABLED" in migrated
    has_class = "local D2WC_CONFIGURATOR_CLASS" in migrated
    has_prompt_class = "local D2WC_ACTION_PROMPT_CLASS" in migrated

    if not has_enabled and not has_class:
        index = migrated.find(USER_CONFIG_MARKER)
        if index == -1:
            raise LuaRuntimeMigrationError("could not find user configuration marker")
        migrated = migrated[:index] + HANDOFF_SETTINGS + migrated[index:]
    elif not has_enabled:
        class_index = migrated.find("local D2WC_CONFIGURATOR_CLASS")
        if class_index == -1:
            raise LuaRuntimeMigrationError("could not find handoff class setting")
        migrated = migrated[:class_index] + HANDOFF_ENABLED_SETTING + migrated[class_index:]
    elif not has_class:
        enabled_line_start = migrated.find("local D2WC_EVENT_HANDOFF_ENABLED")
        if enabled_line_start == -1:
            raise LuaRuntimeMigrationError("could not find handoff enabled setting")
        enabled_line_end = migrated.find("\n", enabled_line_start)
        insert_at = len(migrated) if enabled_line_end == -1 else enabled_line_end + 1
        migrated = migrated[:insert_at] + HANDOFF_CLASS_SETTING + migrated[insert_at:]

    if not has_prompt_class:
        class_index = migrated.find("local D2WC_CONFIGURATOR_CLASS")
        if class_index == -1:
            raise LuaRuntimeMigrationError("could not find handoff class setting")
        class_line_end = migrated.find("\n", class_index)
        insert_at = len(migrated) if class_line_end == -1 else class_line_end + 1
        migrated = migrated[:insert_at] + ACTION_PROMPT_CLASS_SETTING + migrated[insert_at:]

    if HANDOFF_SUPPRESSION_COMMENT.strip() not in migrated:
        class_index = migrated.find("local D2WC_CONFIGURATOR_CLASS")
        if class_index == -1:
            raise LuaRuntimeMigrationError("could not find handoff class setting")
        migrated = migrated[:class_index] + HANDOFF_SUPPRESSION_COMMENT + migrated[class_index:]

    return migrated


def _ensure_handoff_helper(source: str) -> str:
    if "local function launch_d2wc_event_handoff(event_class, is_configured, event_domain)" in source:
        return source
    if CONFIGURATOR_HANDOFF_HELPER in source:
        return source.replace(CONFIGURATOR_HANDOFF_HELPER, HANDOFF_HELPER, 1)
    if OLD_HANDOFF_HELPER in source:
        return source.replace(OLD_HANDOFF_HELPER, HANDOFF_HELPER, 1)
    if "local function launch_d2wc_event_handoff" not in source:
        index = source.find(LC_HELPER)
        if index == -1:
            raise LuaRuntimeMigrationError("could not find lc helper")
        insert_at = index + len(LC_HELPER)
        return source[:insert_at] + HANDOFF_HELPER + source[insert_at:]
    raise LuaRuntimeMigrationError("could not migrate handoff helper")


def _ensure_suppression_helpers(source: str) -> str:
    if "local function exact_lookup_matches_window" in source:
        return source
    index = source.find(PICK_PROFILE_HELPER_END)
    if index == -1:
        raise LuaRuntimeMigrationError("could not find pick_profile helper")
    insert_at = index + len(PICK_PROFILE_HELPER_END)
    return source[:insert_at] + SUPPRESSION_HELPERS + source[insert_at:]


def _ensure_window_has_managed_rule_helper(source: str) -> str:
    if "local function window_has_managed_rule" in source:
        return source
    index = source.find(QUBES_DOMAIN_MARKER)
    if index == -1:
        raise LuaRuntimeMigrationError("could not find Qubes domain marker")
    return source[:index] + WINDOW_HAS_MANAGED_RULE_HELPER + source[index:]


def _ensure_handoff_call(source: str) -> str:
    if "launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls), domain)" in source:
        return source
    if CONFIGURATOR_HANDOFF_CALL in source:
        return source.replace(CONFIGURATOR_HANDOFF_CALL, HANDOFF_CALL, 1)
    if OLD_HANDOFF_CALL in source:
        return source.replace(OLD_HANDOFF_CALL, HANDOFF_CALL, 1)
    if "launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls))" in source:
        return source.replace(
            "launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls))",
            "launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls), domain)",
            1,
        )
    if "launch_d2wc_event_handoff(cls)" in source:
        return source.replace(
            "launch_d2wc_event_handoff(cls)",
            "launch_d2wc_event_handoff(cls, window_has_managed_rule(domain, cls), domain)",
            1,
        )

    index = source.find(CLASS_CAPTURE)
    if index == -1:
        raise LuaRuntimeMigrationError("could not find class capture")
    insert_at = index + len(CLASS_CAPTURE)
    return source[:insert_at] + HANDOFF_CALL + source[insert_at:]


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
