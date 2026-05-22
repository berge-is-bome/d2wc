"""Read-only rule preview derivation from Devilspie2 event data."""

from __future__ import annotations

from dataclasses import dataclass

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
