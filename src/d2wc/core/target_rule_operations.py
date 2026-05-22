"""PIN and EXCLUDE editing operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, extract_managed_config, render_managed_config
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.core.validation import ValidationResult, validate_managed_blocks

TargetSection = Literal["PIN", "EXCLUDE"]


class TargetRuleOperationError(ValueError):
    """Raised when a target-rule edit cannot be applied."""


class TargetRuleExistsError(TargetRuleOperationError):
    """Raised when adding a duplicate target rule."""


class TargetRuleNotFoundError(TargetRuleOperationError):
    """Raised when modifying or deleting a missing target rule."""


@dataclass(frozen=True)
class TargetRuleEditResult:
    source: str
    validation: ValidationResult
    section: TargetSection
    rule: str
    operation: str


@dataclass(frozen=True)
class TargetRuleModifyResult:
    source: str
    validation: ValidationResult
    section: TargetSection
    old_rule: str
    new_rule: str


def add_pin_rule_to_source(source: str, rule_text: str) -> TargetRuleEditResult:
    return _add_rule_to_source(source, "PIN", rule_text)


def modify_pin_rule_in_source(source: str, old_rule_text: str, new_rule_text: str) -> TargetRuleModifyResult:
    return _modify_rule_in_source(source, "PIN", old_rule_text, new_rule_text)


def delete_pin_rule_from_source(source: str, rule_text: str) -> TargetRuleEditResult:
    return _delete_rule_from_source(source, "PIN", rule_text)


def add_exclude_rule_to_source(source: str, rule_text: str) -> TargetRuleEditResult:
    return _add_rule_to_source(source, "EXCLUDE", rule_text)


def modify_exclude_rule_in_source(source: str, old_rule_text: str, new_rule_text: str) -> TargetRuleModifyResult:
    return _modify_rule_in_source(source, "EXCLUDE", old_rule_text, new_rule_text)


def delete_exclude_rule_from_source(source: str, rule_text: str) -> TargetRuleEditResult:
    return _delete_rule_from_source(source, "EXCLUDE", rule_text)


def _add_rule_to_source(source: str, section: TargetSection, rule_text: str) -> TargetRuleEditResult:
    new_rule = _normalize_target_rule(section, rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _add_rule(section, _rules_for_section(config, section), new_rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, section, updated_rules)
    return TargetRuleEditResult(rendered_source, validation, section, new_rule, "add")


def _modify_rule_in_source(
    source: str,
    section: TargetSection,
    old_rule_text: str,
    new_rule_text: str,
) -> TargetRuleModifyResult:
    old_rule = _normalize_target_rule(section, old_rule_text)
    new_rule = _normalize_target_rule(section, new_rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _modify_rule(section, _rules_for_section(config, section), old_rule, new_rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, section, updated_rules)
    return TargetRuleModifyResult(rendered_source, validation, section, old_rule, new_rule)


def _delete_rule_from_source(source: str, section: TargetSection, rule_text: str) -> TargetRuleEditResult:
    rule = _normalize_target_rule(section, rule_text)
    parsed, config = _parse_valid_config(source)
    updated_rules = _delete_rule(section, _rules_for_section(config, section), rule)
    rendered_source, validation = _render_updated_source(source, parsed.blocks, config, section, updated_rules)
    return TargetRuleEditResult(rendered_source, validation, section, rule, "delete")


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
    section: TargetSection,
    updated_rules: tuple[str, ...],
) -> tuple[str, ValidationResult]:
    updated_config = _replace_section_rules(config, section, updated_rules)
    rendered_blocks = render_managed_config(updated_config, blocks)
    rendered_source = _replace_managed_blocks(source, blocks, rendered_blocks)
    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    validation = validate_managed_blocks(rendered_parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return rendered_source, validation


def _replace_section_rules(config: ManagedConfig, section: TargetSection, rules: tuple[str, ...]) -> ManagedConfig:
    if section == "PIN":
        return ManagedConfig(config.exclude, rules, config.workspace_routes, config.geom, config.workspace_placement, config.left_edge_correction)
    return ManagedConfig(rules, config.pin, config.workspace_routes, config.geom, config.workspace_placement, config.left_edge_correction)


def _rules_for_section(config: ManagedConfig, section: TargetSection) -> tuple[str, ...]:
    return config.pin if section == "PIN" else config.exclude


def _add_rule(section: TargetSection, rules: tuple[str, ...], new_rule: str) -> tuple[str, ...]:
    new_sig = _rule_signature(new_rule)
    for existing_rule in rules:
        if _rule_signature(existing_rule) == new_sig:
            raise TargetRuleExistsError(f"{section} rule already exists for target: {_format_target(new_rule)}")
    return (*rules, new_rule)


def _modify_rule(section: TargetSection, rules: tuple[str, ...], old_rule: str, new_rule: str) -> tuple[str, ...]:
    old_sig = _rule_signature(old_rule)
    new_sig = _rule_signature(new_rule)
    updated: list[str] = []
    found = False
    for existing_rule in rules:
        existing_sig = _rule_signature(existing_rule)
        if existing_sig == old_sig:
            updated.append(new_rule)
            found = True
            continue
        if existing_sig == new_sig:
            raise TargetRuleExistsError(f"{section} rule already exists for target: {_format_target(new_rule)}")
        updated.append(existing_rule)
    if not found:
        raise TargetRuleNotFoundError(f"{section} rule not found: {old_rule}")
    return tuple(updated)


def _delete_rule(section: TargetSection, rules: tuple[str, ...], rule: str) -> tuple[str, ...]:
    sig = _rule_signature(rule)
    updated = tuple(existing_rule for existing_rule in rules if _rule_signature(existing_rule) != sig)
    if len(updated) == len(rules):
        raise TargetRuleNotFoundError(f"{section} rule not found: {rule}")
    return updated


def _normalize_target_rule(section: TargetSection, rule_text: str) -> str:
    if not rule_text.strip():
        raise TargetRuleOperationError(f"{section} rule must include d: or c:: {rule_text}")
    try:
        rule = parse_prefixed_rule(rule_text)
    except RuleParseError as exc:
        raise TargetRuleOperationError(str(exc)) from exc
    if not rule.has_target:
        raise TargetRuleOperationError(f"{section} rule must include d: or c:: {rule_text}")
    if rule.geometry_profile is not None:
        raise TargetRuleOperationError(f"{section} rule must not include g:: {rule_text}")
    if rule.left_edge_mode is not None:
        raise TargetRuleOperationError(f"{section} rule must not include le:: {rule_text}")
    parts: list[str] = []
    if rule.domain is not None:
        parts.append(f"d:{rule.domain}")
    if rule.class_name is not None:
        parts.append(f"c:{rule.class_name}")
    return " ".join(parts)


def _rule_signature(rule_text: str) -> tuple[str | None, str | None]:
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
