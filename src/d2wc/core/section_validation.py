"""Section-level validation helpers for managed d2wc blocks."""

from __future__ import annotations

from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.rule_grammar import LEFT_EDGE_MODES, PrefixedRule, RuleParseError, parse_prefixed_rule

REQUIRED_GEOMETRY_FIELDS: tuple[str, ...] = ("x", "y", "w", "h")
MIN_GEOMETRY_SIZE = 10


def validate_target_section(block: ManagedBlock) -> list[str]:
    """Validate EXCLUDE or PIN style rules."""

    messages: list[str] = []
    seen_targets: set[tuple[str | None, str | None]] = set()

    for text in extract_active_rule_strings(block.text):
        try:
            rule = parse_prefixed_rule(text)
        except RuleParseError as exc:
            messages.append(f"{block.name}: {exc}")
            continue
        if not rule.has_target:
            messages.append(f"{block.name}: rule must include d: or c:: {text}")
        if rule.geometry_profile is not None:
            messages.append(f"{block.name}: rule must not include g:: {text}")
        if rule.left_edge_mode is not None:
            messages.append(f"{block.name}: rule must not include le:: {text}")

        target = _rule_target(rule)
        if rule.has_target and target in seen_targets:
            messages.append(f"{block.name}: duplicate rule target: {_format_target(rule)}")
        seen_targets.add(target)

    return messages


def validate_workspace_routes_section(block: ManagedBlock) -> list[str]:
    """Validate WORKSPACE_ROUTES keys and route rules."""

    messages: list[str] = []
    seen_keys: set[int] = set()
    seen_targets: set[tuple[str | None, str | None]] = set()

    for line in block.text.splitlines():
        active = line.split("--", 1)[0].strip()
        if not active:
            continue

        for key in _extract_workspace_keys(active):
            if key in seen_keys:
                messages.append(f"{block.name}: duplicate workspace key: {key}")
            seen_keys.add(key)

        for text in extract_active_rule_strings(active):
            try:
                rule = parse_prefixed_rule(text)
            except RuleParseError as exc:
                messages.append(f"{block.name}: {exc}")
                continue
            if not rule.has_target:
                messages.append(f"{block.name}: rule must include d: or c:: {text}")
            if rule.geometry_profile is not None:
                messages.append(f"{block.name}: rule must not include g:: {text}")
            if rule.left_edge_mode is not None:
                messages.append(f"{block.name}: rule must not include le:: {text}")

            target = _rule_target(rule)
            if rule.has_target and target in seen_targets:
                messages.append(f"{block.name}: duplicate route target: {_format_target(rule)}")
            seen_targets.add(target)

    return messages


def validate_geom_section(block: ManagedBlock) -> list[str]:
    """Validate simple GEOM profile entries."""

    messages: list[str] = []
    seen_names: set[str] = set()

    for name, fields in extract_geometry_profile_entries(block.text):
        if name in seen_names:
            messages.append(f"{block.name}: duplicate geometry profile: {name}")
        seen_names.add(name)

        for field in REQUIRED_GEOMETRY_FIELDS:
            if field not in fields:
                messages.append(f"{block.name}: profile {name} missing {field}")
                continue
            value = fields[field]
            if not isinstance(value, int):
                messages.append(f"{block.name}: profile {name} field {field} must be an integer")

        for size_field in ("w", "h"):
            value = fields.get(size_field)
            if isinstance(value, int) and value < MIN_GEOMETRY_SIZE:
                messages.append(
                    f"{block.name}: profile {name} field {size_field} must be at least {MIN_GEOMETRY_SIZE}"
                )

    return messages


def validate_placement_section(block: ManagedBlock, geometry_profiles: set[str]) -> list[str]:
    """Validate WORKSPACE_PLACEMENT rules."""

    messages: list[str] = []
    seen_targets: set[tuple[str | None, str | None]] = set()

    for text in extract_active_rule_strings(block.text):
        try:
            rule = parse_prefixed_rule(text)
        except RuleParseError as exc:
            messages.append(f"{block.name}: {exc}")
            continue
        if not rule.has_target:
            messages.append(f"{block.name}: rule must include d: or c:: {text}")
        if rule.geometry_profile is None:
            messages.append(f"{block.name}: rule must include g:: {text}")
        elif rule.geometry_profile not in geometry_profiles:
            messages.append(f"{block.name}: geometry profile not found: {rule.geometry_profile}")
        if rule.left_edge_mode is not None:
            messages.append(f"{block.name}: rule must not include le:: {text}")

        target = _rule_target(rule)
        if rule.has_target and target in seen_targets:
            messages.append(f"{block.name}: duplicate placement target: {_format_target(rule)}")
        seen_targets.add(target)

    return messages


def validate_left_edge_section(block: ManagedBlock) -> list[str]:
    """Validate LEFT_EDGE_CORRECTION rules."""

    messages: list[str] = []
    seen_targets: set[tuple[str | None, str | None]] = set()

    for text in extract_active_rule_strings(block.text):
        try:
            rule = parse_prefixed_rule(text)
        except RuleParseError as exc:
            messages.append(f"{block.name}: {exc}")
            continue
        if not rule.has_target:
            messages.append(f"{block.name}: rule must include d: or c:: {text}")
        if rule.geometry_profile is not None:
            messages.append(f"{block.name}: rule must not include g:: {text}")
        if rule.left_edge_mode is None:
            messages.append(f"{block.name}: rule must include le:: {text}")
        elif rule.left_edge_mode not in LEFT_EDGE_MODES:
            messages.append(f"{block.name}: invalid left-edge mode: {rule.left_edge_mode}")

        target = _rule_target(rule)
        if rule.has_target and target in seen_targets:
            messages.append(f"{block.name}: duplicate left-edge target: {_format_target(rule)}")
        seen_targets.add(target)

    return messages


def extract_geometry_profile_names(geom_block_text: str) -> set[str]:
    """Extract simple `name = { ... }` profile names from the GEOM block."""

    return set(extract_geometry_profiles(geom_block_text))


def extract_geometry_profiles(geom_block_text: str) -> dict[str, dict[str, int | str]]:
    """Extract simple GEOM profile entries from a GEOM block."""

    return dict(extract_geometry_profile_entries(geom_block_text))


def extract_geometry_profile_entries(geom_block_text: str) -> list[tuple[str, dict[str, int | str]]]:
    """Extract simple GEOM profile entries while preserving duplicates."""

    profiles: list[tuple[str, dict[str, int | str]]] = []
    for line in geom_block_text.splitlines():
        active = _active_lua_segment(line)
        if not active or "=" not in active or "{" not in active or "}" not in active:
            continue
        parsed = _parse_geometry_profile_line(active)
        if parsed is None:
            continue
        name, fields = parsed
        profiles.append((name.lower(), fields))
    return profiles


def extract_active_rule_strings(block_text: str) -> list[str]:
    """Extract double-quoted strings from active, non-comment line segments."""

    strings: list[str] = []
    for line in block_text.splitlines():
        active = line.split("--", 1)[0]
        pieces = active.split('"')
        strings.extend(pieces[index] for index in range(1, len(pieces), 2))
    return strings


def _parse_geometry_profile_line(active_line: str) -> tuple[str, dict[str, int | str]] | None:
    candidate = active_line.strip()

    if candidate.startswith("local ") and "{" in candidate:
        candidate = candidate.split("{", 1)[1].strip()

    if "=" not in candidate or "{" not in candidate or "}" not in candidate:
        return None

    name = candidate.split("=", 1)[0].strip()
    if not _is_lua_identifier(name):
        return None

    body = candidate.split("{", 1)[1].split("}", 1)[0]
    fields: dict[str, int | str] = {}
    for chunk in body.split(","):
        if "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        key = key.strip()
        raw_value = value.strip()
        try:
            fields[key] = int(raw_value)
        except ValueError:
            fields[key] = raw_value

    return name, fields


def _extract_workspace_keys(active_line: str) -> list[int]:
    keys: list[int] = []
    remaining = active_line
    while "[" in remaining and "]" in remaining:
        before, after_open = remaining.split("[", 1)
        key_text, after_close = after_open.split("]", 1)
        remaining = after_close
        if "=" not in after_close:
            continue
        try:
            keys.append(int(key_text.strip()))
        except ValueError:
            continue
    return keys


def _rule_target(rule: PrefixedRule) -> tuple[str | None, str | None]:
    return rule.domain, rule.class_name


def _format_target(rule: PrefixedRule) -> str:
    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    return " ".join(parts)


def _active_lua_segment(line: str) -> str:
    return line.split("--", 1)[0].strip()


def _is_lua_identifier(value: str) -> bool:
    return bool(value) and not value[0].isdigit() and value.replace("_", "").isalnum()
