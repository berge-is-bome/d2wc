"""WORKSPACE_PLACEMENT editing operations."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, extract_managed_config, render_managed_config
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class PlacementOperationError(ValueError):
    """Raised when a placement edit cannot be applied."""


class PlacementRuleExistsError(PlacementOperationError):
    """Raised when adding a duplicate placement target."""


class PlacementRuleNotFoundError(PlacementOperationError):
    """Raised when modifying or deleting a missing placement rule."""


@dataclass(frozen=True)
class PlacementEditResult:
    """Result of applying a WORKSPACE_PLACEMENT edit in memory."""

    source: str
    validation: ValidationResult
    rule: str
    operation: str


@dataclass(frozen=True)
class PlacementModifyResult:
    """Result of modifying a WORKSPACE_PLACEMENT rule in memory."""

    source: str
    validation: ValidationResult
    old_rule: str
    new_rule: str


def add_placement_rule_to_source(source: str, rule_text: str) -> PlacementEditResult:
    """Add one WORKSPACE_PLACEMENT rule to Lua source."""

    normalized_rule = _normalize_placement_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    _ensure_geometry_profile_exists(config, normalized_rule)
    updated_rules = _add_rule(config.workspace_placement, normalized_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_rules)

    return PlacementEditResult(
        source=rendered_source,
        validation=rendered_validation,
        rule=normalized_rule,
        operation="add",
    )


def modify_placement_rule_in_source(source: str, old_rule_text: str, new_rule_text: str) -> PlacementModifyResult:
    """Modify one WORKSPACE_PLACEMENT rule in Lua source.

    Matching is based on parsed rule meaning, not token order. The rendered rule
    is written in canonical prefix order.
    """

    old_rule = _normalize_placement_rule(old_rule_text)
    new_rule = _normalize_placement_rule(new_rule_text)
    parsed, config = _parse_valid_config(source)
    _ensure_geometry_profile_exists(config, new_rule)
    updated_rules = _modify_rule(config.workspace_placement, old_rule, new_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_rules)

    return PlacementModifyResult(
        source=rendered_source,
        validation=rendered_validation,
        old_rule=old_rule,
        new_rule=new_rule,
    )


def delete_placement_rule_from_source(source: str, rule_text: str) -> PlacementEditResult:
    """Delete one WORKSPACE_PLACEMENT rule from Lua source.

    Matching is based on parsed rule meaning, not token order.
    """

    normalized_rule = _normalize_placement_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _delete_rule(config.workspace_placement, normalized_rule)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_rules)

    return PlacementEditResult(
        source=rendered_source,
        validation=rendered_validation,
        rule=normalized_rule,
        operation="delete",
    )


def _parse_valid_config(source: str):
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return parsed, extract_managed_config(parsed.blocks)


def _render_updated_source(
    source: str,
    blocks: dict[str, object],
    config: ManagedConfig,
    updated_rules: tuple[str, ...],
) -> tuple[str, ValidationResult]:
    updated_config = ManagedConfig(
        exclude=config.exclude,
        pin=config.pin,
        workspace_routes=config.workspace_routes,
        geom=config.geom,
        workspace_placement=updated_rules,
        left_edge_correction=config.left_edge_correction,
    )

    rendered_blocks = render_managed_config(updated_config, blocks)
    rendered_source = _replace_managed_blocks(source, blocks, rendered_blocks)

    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    rendered_validation = validate_managed_blocks(rendered_parsed.blocks)
    if not rendered_validation.ok:
        raise RenderValidationError(rendered_validation)

    return rendered_source, rendered_validation


def _add_rule(rules: tuple[str, ...], new_rule: str) -> tuple[str, ...]:
    new_target = _rule_target(new_rule)
    for existing_rule in rules:
        if _rule_target(existing_rule) == new_target:
            raise PlacementRuleExistsError(f"placement rule already exists for target: {_format_target(new_rule)}")
    return (*rules, new_rule)


def _modify_rule(rules: tuple[str, ...], old_rule: str, new_rule: str) -> tuple[str, ...]:
    old_signature = _rule_signature(old_rule)
    new_target = _rule_target(new_rule)
    updated: list[str] = []
    found = False

    for existing_rule in rules:
        if _rule_signature(existing_rule) == old_signature:
            updated.append(new_rule)
            found = True
            continue
        if _rule_target(existing_rule) == new_target:
            raise PlacementRuleExistsError(f"placement rule already exists for target: {_format_target(new_rule)}")
        updated.append(existing_rule)

    if not found:
        raise PlacementRuleNotFoundError(f"placement rule not found: {old_rule}")

    return tuple(updated)


def _delete_rule(rules: tuple[str, ...], rule: str) -> tuple[str, ...]:
    signature = _rule_signature(rule)
    updated = tuple(existing_rule for existing_rule in rules if _rule_signature(existing_rule) != signature)
    if len(updated) == len(rules):
        raise PlacementRuleNotFoundError(f"placement rule not found: {rule}")
    return updated


def _ensure_geometry_profile_exists(config: ManagedConfig, rule_text: str) -> None:
    rule = parse_prefixed_rule(rule_text)
    profile_names = {profile.name for profile in config.geom}
    if rule.geometry_profile not in profile_names:
        raise PlacementOperationError(f"geometry profile not found: {rule.geometry_profile}")


def _normalize_placement_rule(rule_text: str) -> str:
    try:
        rule = parse_prefixed_rule(rule_text)
    except RuleParseError as exc:
        raise PlacementOperationError(str(exc)) from exc

    if not rule.has_target:
        raise PlacementOperationError(f"placement rule must include d: or c:: {rule_text}")
    if rule.geometry_profile is None:
        raise PlacementOperationError(f"placement rule must include g:: {rule_text}")
    if rule.left_edge_mode is not None:
        raise PlacementOperationError(f"placement rule must not include le:: {rule_text}")

    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    parts.append(f"g:{rule.geometry_profile}")
    return " ".join(parts)


def _rule_signature(rule_text: str) -> tuple[str | None, str | None, str | None]:
    rule = parse_prefixed_rule(rule_text)
    return rule.domain, rule.class_name, rule.geometry_profile


def _rule_target(rule_text: str) -> tuple[str | None, str | None]:
    rule = parse_prefixed_rule(rule_text)
    return rule.domain, rule.class_name


def _format_target(rule_text: str) -> str:
    rule = parse_prefixed_rule(rule_text)
    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    return " ".join(parts)


def _replace_managed_blocks(source: str, blocks: dict[str, object], replacements: dict[str, str]) -> str:
    rendered = source
    for name in reversed(MANAGED_BLOCK_NAMES):
        block = blocks[name]
        replacement = replacements[name]
        rendered = rendered[: block.start_index] + replacement + rendered[block.end_index :]
    return rendered
