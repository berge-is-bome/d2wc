"""Section-level validation helpers for managed d2wc blocks."""

from __future__ import annotations

from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.rule_grammar import LEFT_EDGE_MODES, RuleParseError, parse_prefixed_rule


def validate_target_section(block: ManagedBlock) -> list[str]:
    """Validate EXCLUDE or PIN style rules."""

    messages: list[str] = []
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
    return messages


def validate_placement_section(block: ManagedBlock, geometry_profiles: set[str]) -> list[str]:
    """Validate WORKSPACE_PLACEMENT rules."""

    messages: list[str] = []
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
    return messages


def validate_left_edge_section(block: ManagedBlock) -> list[str]:
    """Validate LEFT_EDGE_CORRECTION rules."""

    messages: list[str] = []
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
    return messages


def extract_geometry_profile_names(geom_block_text: str) -> set[str]:
    """Extract simple `name = { ... }` profile names from the GEOM block."""

    names: set[str] = set()
    for line in geom_block_text.splitlines():
        active = line.split("--", 1)[0].strip()
        if "=" not in active or "{" not in active:
            continue
        name = active.split("=", 1)[0].strip()
        if name and name.replace("_", "").isalnum() and not name[0].isdigit():
            names.add(name.lower())
    return names


def extract_active_rule_strings(block_text: str) -> list[str]:
    """Extract double-quoted strings from active, non-comment line segments."""

    strings: list[str] = []
    for line in block_text.splitlines():
        active = line.split("--", 1)[0]
        pieces = active.split('"')
        strings.extend(pieces[index] for index in range(1, len(pieces), 2))
    return strings
