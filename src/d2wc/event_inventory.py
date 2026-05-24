"""Parse Devilspie2 debug/event text into known-window inventory candidates."""

from __future__ import annotations

from dataclasses import dataclass
import re

_NORMAL_WINDOW_TYPE = "WINDOW_TYPE_NORMAL"
_KEY_VALUE_PATTERN = re.compile(r"([A-Za-z0-9_.-]+)\s*[:=]\s*([^,;\n\r]+)")


@dataclass(frozen=True)
class KnownWindowCandidate:
    """Normalized known-window candidate parsed from a debug/event snippet."""

    machine: str
    application: str
    raw_class_instance_name: str
    window_type: str
    raw_source: str


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
        for key, value in _KEY_VALUE_PATTERN.findall(line):
            canonical = _canonical_key(key)
            if canonical is None:
                continue
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
    normalized = key.strip().lower().replace("-", "_").replace(".", "_")
    aliases = {
        "machine": "machine",
        "domain": "domain",
        "_qubes_vmname": "machine",
        "vmname": "machine",
        "application": "application",
        "application_name": "application",
        "class_instance_name": "class_instance_name",
        "class_instance": "class_instance_name",
        "wm_class_instance": "class_instance_name",
        "window_type": "window_type",
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
