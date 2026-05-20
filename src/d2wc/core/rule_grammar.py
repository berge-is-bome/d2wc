"""Parser for d2wc prefixed rule strings.

Rules use space-separated tokens with explicit prefixes:

- d:<domain>
- c:<class>
- g:<geometry-profile>
- le:<pos1|pos2>

This mirrors the Lua script's `parse_prefixed_rule()` behavior without
executing Lua.
"""

from __future__ import annotations

from dataclasses import dataclass


ALLOWED_PREFIXES: frozenset[str] = frozenset({"d", "c", "g", "le"})
LEFT_EDGE_MODES: frozenset[str] = frozenset({"pos1", "pos2"})


class RuleParseError(ValueError):
    """Raised when a rule string cannot be parsed safely."""


@dataclass(frozen=True)
class PrefixedRule:
    """Structured representation of one prefixed rule string."""

    raw: str
    domain: str | None = None
    class_name: str | None = None
    geometry_profile: str | None = None
    left_edge_mode: str | None = None

    @property
    def has_target(self) -> bool:
        """Return whether the rule has at least a domain or class target."""

        return self.domain is not None or self.class_name is not None


def parse_prefixed_rule(rule: str) -> PrefixedRule:
    """Parse one d2wc prefixed rule string.

    The parser is case-insensitive and normalizes values to lowercase, matching
    the current Lua script behavior.
    """

    normalized = rule.strip().lower()
    if not normalized:
        raise RuleParseError("rule is empty")

    values: dict[str, str] = {}
    for token in normalized.split():
        prefix, separator, value = token.partition(":")
        if separator != ":" or not prefix or not value:
            raise RuleParseError(f"invalid token '{token}' in rule '{rule}'")
        if prefix not in ALLOWED_PREFIXES:
            raise RuleParseError(f"unknown prefix '{prefix}:' in rule '{rule}'")
        if prefix in values:
            raise RuleParseError(f"duplicate prefix '{prefix}:' in rule '{rule}'")
        values[prefix] = value

    return PrefixedRule(
        raw=rule,
        domain=values.get("d"),
        class_name=values.get("c"),
        geometry_profile=values.get("g"),
        left_edge_mode=values.get("le"),
    )
