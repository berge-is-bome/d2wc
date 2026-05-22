"""Read-only rule preview derivation from Devilspie2 event data."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, extract_managed_config
from d2wc.core.rule_grammar import PrefixedRule, RuleParseError, parse_prefixed_rule
from d2wc.core.validation import validate_managed_blocks
from d2wc.event_data import WindowEventData


@dataclass(frozen=True)
class EventRulePreview:
    """Read-only preview of candidate config entries derived from event data."""

    geometry_profile_name: str | None = None
    geometry_profile_line: str | None = None
    placement_rule: str | None = None
    warning: str | None = None

    @property
    def ok(self) -> bool:
        """Return whether the preview has both candidate entries."""

        return self.geometry_profile_line is not None and self.placement_rule is not None


@dataclass(frozen=True)
class EventConfigAwareness:
    """Read-only summary of whether the event target is already handled."""

    status: str
    profile_exists: bool = False
    matching_rules: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def has_existing_handling(self) -> bool:
        """Return whether the config already has matching handling for the target."""

        return self.profile_exists or bool(self.matching_rules)


def build_event_rule_preview(event: WindowEventData) -> EventRulePreview:
    """Build a read-only GEOM and WORKSPACE_PLACEMENT preview from event data.

    This function does not read or write any config file. It only prepares text
    that a later UI step can feed into the already-tested core edit operations.
    """

    class_token = _class_token_from_event(event)
    if class_token is None:
        return EventRulePreview(
            warning="No safe class token is available for a placement preview."
        )

    if not _is_safe_rule_token(class_token):
        return EventRulePreview(
            warning=(
                "The captured class contains whitespace or unsupported characters; "
                "placement preview is deferred until the rule grammar supports quoted values."
            )
        )

    geometry = event.window_geometry
    if None in (geometry.x, geometry.y, geometry.w, geometry.h):
        return EventRulePreview(
            warning="Window geometry is incomplete, so a GEOM preview cannot be built."
        )

    profile_name = _profile_name_from_class_token(class_token)
    x = _event_number_to_int(geometry.x)
    y = _event_number_to_int(geometry.y)
    w = _event_number_to_int(geometry.w)
    h = _event_number_to_int(geometry.h)

    geometry_line = f"{profile_name} = {{ x = {x}, y = {y}, w = {w}, h = {h} }}"
    placement_rule = _placement_rule(event, class_token, profile_name)

    return EventRulePreview(
        geometry_profile_name=profile_name,
        geometry_profile_line=geometry_line,
        placement_rule=placement_rule,
    )


def build_event_config_awareness(source: str, preview: EventRulePreview) -> EventConfigAwareness:
    """Inspect existing config text for matching entries without changing it."""

    if not preview.ok or not preview.placement_rule:
        return EventConfigAwareness(
            status="skipped",
            warnings=("No safe proposal was available, so the config was not inspected for matches.",),
        )

    try:
        candidate = parse_prefixed_rule(preview.placement_rule)
        parse_result = ManagedBlockParser().parse(source)
        validation = validate_managed_blocks(parse_result.blocks)
    except (RuleParseError, ValueError) as exc:
        return EventConfigAwareness(
            status="error",
            warnings=(f"Could not inspect config read-only: {exc}",),
        )

    if not validation.ok:
        return EventConfigAwareness(
            status="invalid-config",
            warnings=tuple(validation.errors),
        )

    config = extract_managed_config(parse_result.blocks)
    profile_exists = bool(
        preview.geometry_profile_name
        and preview.geometry_profile_name in {profile.name for profile in config.geom}
    )
    matching_rules = _matching_config_rules(config, candidate)

    return EventConfigAwareness(
        status="ok",
        profile_exists=profile_exists,
        matching_rules=matching_rules,
    )


def format_event_rule_preview(preview: EventRulePreview) -> str:
    """Format a read-only event-derived proposal for GTK display."""

    if not preview.ok:
        return "\n".join(
            [
                "Proposal status: unavailable",
                f"Reason: {preview.warning or 'unknown'}",
                "No config files are read or written from this preview.",
            ]
        )

    return "\n".join(
        [
            "Proposal status: ready for later edit wiring",
            "Candidate GEOM profile:",
            preview.geometry_profile_line or "unknown",
            "Candidate WORKSPACE_PLACEMENT rule:",
            preview.placement_rule or "unknown",
            "No config files are read or written from this preview.",
        ]
    )


def format_event_config_awareness(awareness: EventConfigAwareness | None) -> str:
    """Format the read-only existing-config awareness result."""

    if awareness is None:
        return "Config status: not inspected\nPass --config to inspect an existing d2wc.lua file read-only."

    lines = [f"Config status: {awareness.status}"]
    if awareness.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in awareness.warnings)
        lines.append("No config files were changed.")
        return "\n".join(lines)

    lines.append(f"Candidate GEOM profile already exists: {_yes_no(awareness.profile_exists)}")
    if awareness.matching_rules:
        lines.append("Existing target matches:")
        lines.extend(f"- {rule}" for rule in awareness.matching_rules)
    else:
        lines.append("Existing target matches: none")
    lines.append("No config files were changed.")
    return "\n".join(lines)


def proposal_clipboard_text(preview: EventRulePreview, awareness: EventConfigAwareness | None = None) -> str:
    """Return one plain-text block suitable for copying from the GTK UI."""

    parts = [format_event_rule_preview(preview)]
    if awareness is not None:
        parts.append(format_event_config_awareness(awareness))
    return "\n\n".join(parts)


def _matching_config_rules(config: ManagedConfig, candidate: PrefixedRule) -> tuple[str, ...]:
    matches: list[str] = []

    _extend_matching_rule_lines(matches, "EXCLUDE", config.exclude, candidate)
    _extend_matching_rule_lines(matches, "PIN", config.pin, candidate)
    for route in config.workspace_routes:
        _extend_matching_rule_lines(matches, f"WORKSPACE_ROUTES[{route.workspace}]", route.rules, candidate)
    _extend_matching_rule_lines(matches, "WORKSPACE_PLACEMENT", config.workspace_placement, candidate)
    _extend_matching_rule_lines(matches, "LEFT_EDGE_CORRECTION", config.left_edge_correction, candidate)

    return tuple(matches)


def _extend_matching_rule_lines(
    output: list[str],
    section: str,
    rules: tuple[str, ...],
    candidate: PrefixedRule,
) -> None:
    for rule_text in rules:
        try:
            rule = parse_prefixed_rule(rule_text)
        except RuleParseError:
            continue
        if _rule_matches_candidate_target(rule, candidate):
            output.append(f"{section}: {rule_text}")


def _rule_matches_candidate_target(rule: PrefixedRule, candidate: PrefixedRule) -> bool:
    if not rule.has_target:
        return False
    if rule.domain is not None and rule.domain != candidate.domain:
        return False
    if rule.class_name is not None and rule.class_name != candidate.class_name:
        return False
    return True


def _class_token_from_event(event: WindowEventData) -> str | None:
    raw_class = event.class_instance_name or event.window_class
    if raw_class is None or raw_class == "":
        return None
    return raw_class.rsplit(":", 1)[-1].lower()


def _placement_rule(event: WindowEventData, class_token: str, profile_name: str) -> str:
    domain = event.display_domain
    if domain and _is_safe_rule_token(domain):
        return f"d:{domain.lower()} c:{class_token} g:{profile_name}"
    return f"c:{class_token} g:{profile_name}"


def _profile_name_from_class_token(class_token: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in class_token.lower())
    normalized = "_".join(piece for piece in normalized.split("_") if piece)
    if not normalized:
        normalized = "window"
    if normalized[0].isdigit():
        normalized = f"window_{normalized}"
    return f"event_{normalized}"


def _is_safe_rule_token(value: str) -> bool:
    return bool(value) and not any(char.isspace() for char in value)


def _event_number_to_int(value: float | None) -> int:
    if value is None:
        raise TypeError("event number is missing")
    return int(round(value))


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
