"""Warning helpers for shadowed managed rules.

Shadowing is not a validation error. A broad rule can be useful as a default
while a more specific rule intentionally overrides it.
"""

from __future__ import annotations

from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.rule_grammar import PrefixedRule, RuleParseError, parse_prefixed_rule
from d2wc.core.section_validation import extract_active_rule_strings


def warn_shadowed_target_rules(block: ManagedBlock) -> list[str]:
    """Return warnings for broad target rules shadowed by exact target rules."""

    rules = _parse_valid_target_rules(block)
    return _shadow_warnings(block.name, rules)


def _parse_valid_target_rules(block: ManagedBlock) -> list[PrefixedRule]:
    rules: list[PrefixedRule] = []
    for text in extract_active_rule_strings(block.text):
        try:
            rule = parse_prefixed_rule(text)
        except RuleParseError:
            continue
        if rule.has_target:
            rules.append(rule)
    return rules


def _shadow_warnings(section_name: str, rules: list[PrefixedRule]) -> list[str]:
    warnings: list[str] = []
    domain_wide = {rule.domain for rule in rules if rule.domain is not None and rule.class_name is None}
    class_wide = {rule.class_name for rule in rules if rule.domain is None and rule.class_name is not None}
    exact_rules = [rule for rule in rules if rule.domain is not None and rule.class_name is not None]

    for rule in exact_rules:
        if rule.domain in domain_wide:
            warnings.append(
                f"{section_name}: exact rule d:{rule.domain} c:{rule.class_name} overrides broader d:{rule.domain}"
            )
        if rule.class_name in class_wide:
            warnings.append(
                f"{section_name}: exact rule d:{rule.domain} c:{rule.class_name} overrides broader c:{rule.class_name}"
            )

    return warnings
