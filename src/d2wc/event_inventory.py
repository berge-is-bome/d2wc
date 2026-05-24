"""Parse Devilspie2 debug/event text into known-window inventory candidates."""

from __future__ import annotations

from dataclasses import dataclass
import re

from d2wc.core.managed_config import ManagedConfig
from d2wc.core.rule_grammar import PrefixedRule, RuleParseError, parse_prefixed_rule

_NORMAL_WINDOW_TYPE = "WINDOW_TYPE_NORMAL"
_KEY_VALUE_PATTERN = re.compile(r"^\s*([^:=]+?)\s*[:=]\s*(.*?)\s*$")
KNOWN_WINDOW_TARGET_SECTIONS = (
    "EXCLUDE",
    "PIN",
    "WORKSPACE_ROUTES",
    "WORKSPACE_PLACEMENT",
    "LEFT_EDGE_CORRECTION",
)


@dataclass(frozen=True)
class KnownWindowCandidate:
    """Normalized known-window candidate parsed from a debug/event snippet."""

    machine: str
    application: str
    raw_class_instance_name: str
    window_type: str
    raw_source: str


@dataclass(frozen=True)
class KnownWindowTarget:
    """Selectable rule target derived from one or more window observations."""

    machine: str
    application: str

    @property
    def rule(self) -> str:
        """Return the prefixed target rule for this known-window target."""

        return f"d:{self.machine} c:{self.application}"


def parse_known_window_candidates(raw_text: str) -> tuple[KnownWindowCandidate, ...]:
    """Parse raw Devilspie2/debug text into normalized normal-window candidates."""

    candidates: list[KnownWindowCandidate] = []
    for block in _event_blocks(raw_text):
        fields = _extract_event_fields(block)
        if fields.get("window_type") != _NORMAL_WINDOW_TYPE:
            continue

        machine = _normalize_machine(fields)
        application = _normalize_application(fields)
        raw_class = fields.get("class_instance_name")

        if machine is None or application is None or raw_class is None:
            continue

        candidates.append(
            KnownWindowCandidate(
                machine=machine,
                application=application,
                raw_class_instance_name=raw_class,
                window_type=_NORMAL_WINDOW_TYPE,
                raw_source=block,
            )
        )

    return tuple(candidates)


def build_known_window_targets(
    candidates: tuple[KnownWindowCandidate, ...],
) -> tuple[KnownWindowTarget, ...]:
    """Build unique selectable rule targets from parsed window observations.

    Repeated observations in `devilspie2 --debug` output are normal. They are
    collapsed into one selectable machine/application target without exposing an
    observation count to the UI.
    """

    targets: list[KnownWindowTarget] = []
    seen: set[KnownWindowTarget] = set()
    for candidate in candidates:
        machine = candidate.machine.strip().lower()
        application = candidate.application.strip().lower()
        if not _is_safe_rule_token(machine) or not _is_safe_rule_token(application):
            continue
        target = KnownWindowTarget(machine=machine, application=application)
        if target in seen:
            continue
        seen.add(target)
        targets.append(target)
    return tuple(targets)


def build_available_known_window_targets(
    candidates: tuple[KnownWindowCandidate, ...],
    config: ManagedConfig | None,
    section: str,
) -> tuple[KnownWindowTarget, ...]:
    """Build known-window targets not already configured for one section."""

    return filter_known_window_targets_for_section(
        build_known_window_targets(candidates),
        config,
        section,
    )


def filter_known_window_targets_for_section(
    targets: tuple[KnownWindowTarget, ...],
    config: ManagedConfig | None,
    section: str,
) -> tuple[KnownWindowTarget, ...]:
    """Suppress targets already covered by the selected managed section."""

    if section not in KNOWN_WINDOW_TARGET_SECTIONS:
        return ()
    if config is None:
        return targets

    configured_rules = _configured_rules_for_section(config, section)
    parsed_rules = tuple(_parse_rule_or_none(rule) for rule in configured_rules)
    return tuple(
        target
        for target in targets
        if not any(
            parsed_rule is not None and _rule_matches_known_window_target(parsed_rule, target)
            for parsed_rule in parsed_rules
        )
    )


def _event_blocks(raw_text: str) -> tuple[str, ...]:
    blocks: list[str] = []
    current: list[str] = []
    for line in raw_text.splitlines():
        if line.strip() == "":
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)

    if current:
        blocks.append("\n".join(current).strip())

    return tuple(block for block in blocks if block)


def _extract_event_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        lower = line.lower()
        match = _KEY_VALUE_PATTERN.match(line)
        if match:
            raw_key, value = match.groups()
            canonical = _canonical_key(raw_key)
            if canonical is not None:
                normalized_value = _clean_value(value)
                if normalized_value == "":
                    normalized_value = "dom0" if canonical in {"machine", "domain"} else ""
                fields[canonical] = normalized_value

        if "window_type" not in fields and "window_type_normal" in lower:
            fields["window_type"] = _NORMAL_WINDOW_TYPE

    if "machine" not in fields and "domain" in fields:
        fields["machine"] = fields["domain"]
    if "application" not in fields:
        class_instance = fields.get("class_instance_name")
        if class_instance:
            fields["application"] = class_instance
    return fields


def _canonical_key(key: str) -> str | None:
    normalized = key.strip().lower().replace("-", "_").replace(".", "_").replace(" ", "_")
    aliases = {
        "machine": "machine",
        "domain": "domain",
        "_qubes_vmname": "machine",
        "vmname": "machine",
        "application": "application",
        "application_name": "application",
        "window_name": "window_name",
        "class_instance_name": "class_instance_name",
        "class_instance": "class_instance_name",
        "wm_class_instance": "class_instance_name",
        "window_class": "window_class",
        "window_type": "window_type",
        "screen_geometry": "screen_geometry",
        "window_geometry": "window_geometry",
    }
    return aliases.get(normalized)


def _clean_value(value: str) -> str:
    trimmed = value.strip().strip("\"'")
    if trimmed.startswith("(") and trimmed.endswith(")"):
        trimmed = trimmed[1:-1].strip()
    return trimmed


def _normalize_machine(fields: dict[str, str]) -> str | None:
    raw = fields.get("machine") or fields.get("domain")
    if raw is None:
        return None
    if raw == "":
        return "dom0"
    return raw.lower()


def _normalize_application(fields: dict[str, str]) -> str | None:
    raw_class = fields.get("class_instance_name")
    raw_app = fields.get("application")
    chosen = raw_class or raw_app
    if not chosen:
        return None

    token = chosen.rsplit(":", 1)[-1].strip().lower()
    return token or None


def _configured_rules_for_section(config: ManagedConfig, section: str) -> tuple[str, ...]:
    if section == "EXCLUDE":
        return config.exclude
    if section == "PIN":
        return config.pin
    if section == "WORKSPACE_ROUTES":
        return tuple(rule for route in config.workspace_routes for rule in route.rules)
    if section == "WORKSPACE_PLACEMENT":
        return config.workspace_placement
    if section == "LEFT_EDGE_CORRECTION":
        return config.left_edge_correction
    return ()


def _parse_rule_or_none(rule: str) -> PrefixedRule | None:
    try:
        return parse_prefixed_rule(rule)
    except RuleParseError:
        return None


def _rule_matches_known_window_target(rule: PrefixedRule, target: KnownWindowTarget) -> bool:
    if not rule.has_target:
        return False
    if rule.domain is not None and rule.domain != target.machine:
        return False
    if rule.class_name is not None and rule.class_name != target.application:
        return False
    return True


def _is_safe_rule_token(value: str) -> bool:
    return bool(value) and not any(char.isspace() for char in value)
