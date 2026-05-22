"""LEFT_EDGE_CORRECTION editing operations."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, extract_managed_config, render_managed_config
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class LeftEdgeOperationError(ValueError):
    """Raised when a LEFT_EDGE_CORRECTION edit cannot be applied."""


class LeftEdgeRuleExistsError(LeftEdgeOperationError):
    """Raised when adding a duplicate left-edge target."""


class LeftEdgeRuleNotFoundError(LeftEdgeOperationError):
    """Raised when modifying or deleting a missing left-edge rule."""


@dataclass(frozen=True)
class LeftEdgeEditResult:
    source: str
    validation: ValidationResult
    rule: str
    operation: str


@dataclass(frozen=True)
class LeftEdgeModifyResult:
    source: str
    validation: ValidationResult
    old_rule: str
    new_rule: str


def add_left_edge_rule_to_source(source: str, rule_text: str) -> LeftEdgeEditResult:
    """Add one LEFT_EDGE_CORRECTION rule to Lua source."""

    new_rule = _normalize_left_edge_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _add_rule(config.left_edge_correction, new_rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, updated_rules)
    return LeftEdgeEditResult(rendered_source, validation, new_rule, "add")


def modify_left_edge_rule_in_source(source: str, old_rule_text: str, new_rule_text: str) -> LeftEdgeModifyResult:
    """Modify one LEFT_EDGE_CORRECTION rule in Lua source."""

    old_rule = _normalize_left_edge_rule(old_rule_text)
    new_rule = _normalize_left_edge_rule(new_rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _modify_rule(config.left_edge_correction, old_rule, new_rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, updated_rules)
    return LeftEdgeModifyResult(rendered_source, validation, old_rule, new_rule)


def delete_left_edge_rule_from_source(source: str, rule_text: str) -> LeftEdgeEditResult:
    """Delete one LEFT_EDGE_CORRECTION rule from Lua source."""

    rule = _normalize_left_edge_rule(rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _delete_rule(config.left_edge_correction, rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, updated_rules)
    return LeftEdgeEditResult(rendered_source, validation, rule, "delete")


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
        workspace_placement=config.workspace_placement,
        left_edge_correction=updated_rules,
    )
    rendered_blocks = render_managed_config(updated_config, blocks)
    rendered_source = _replace_managed_blocks(source, blocks, rendered_blocks)
    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    validation = validate_managed_blocks(rendered_parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return rendered_source, validation


def _add_rule(rules: tuple[str, ...], new_rule: str) -> tuple[str, ...]:
    new_target = _rule_target(new_rule)
    for existing_rule in rules:
        if _rule_target(existing_rule) == new_target:
            raise LeftEdgeRuleExistsError(f"left-edge rule already exists for target: {_format_target(new_rule)}")
    return (*rules, new_rule)


def _modify_rule(rules: tuple[str, ...], old_rule: str, new_rule: str) -> tuple[str, ...]:
    old_signature = _rule_signature(old_rule)
    new_target = _rule_target(new_rule)
    updated: list[str] = []
    found = False
    for existing_rule in rules:
        existing_signature = _rule_signature(existing_rule)
        if existing_signature == old_signature:
            updated.append(new_rule)
            found = True
            continue
        if _rule_target(existing_rule) == new_target:
            raise LeftEdgeRuleExistsError(f"left-edge rule already exists for target: {_format_target(new_rule)}")
        updated.append(existing_rule)
    if not found:
        raise LeftEdgeRuleNotFoundError(f"left-edge rule not found: {old_rule}")
    return tuple(updated)


def _delete_rule(rules: tuple[str, ...], rule: str) -> tuple[str, ...]:
    signature = _rule_signature(rule)
    updated = tuple(existing_rule for existing_rule in rules if _rule_signature(existing_rule) != signature)
    if len(updated) == len(rules):
        raise LeftEdgeRuleNotFoundError(f"left-edge rule not found: {rule}")
    return updated


def _normalize_left_edge_rule(rule_text: str) -> str:
    if not rule_text.strip():
        raise LeftEdgeOperationError(f"left-edge rule must include d: or c:: {rule_text}")
    try:
        rule = parse_prefixed_rule(rule_text)
    except RuleParseError as exc:
        raise LeftEdgeOperationError(str(exc)) from exc
    if not rule.has_target:
        raise LeftEdgeOperationError(f"left-edge rule must include d: or c:: {rule_text}")
    if rule.geometry_profile is not None:
        raise LeftEdgeOperationError(f"left-edge rule must not include g:: {rule_text}")
    if rule.left_edge_mode is None:
        raise LeftEdgeOperationError(f"left-edge rule must include le:: {rule_text}")
    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    parts.append(f"le:{rule.left_edge_mode}")
    return " ".join(parts)


def _rule_signature(rule_text: str) -> tuple[str | None, str | None, str | None]:
    rule = parse_prefixed_rule(rule_text)
    return rule.domain, rule.class_name, rule.left_edge_mode


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
