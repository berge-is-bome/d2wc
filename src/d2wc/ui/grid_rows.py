"""Pure row models and row builders for the GTK managed-section grid."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.event_data import WindowEventData
from d2wc.event_inventory import KnownWindowTarget, filter_known_window_targets_for_section
from d2wc.event_preview import build_event_rule_preview
from d2wc.test_config import TestConfigSnapshot

DEVELOPMENT_SELECTOR_VALUES = {"example"}


@dataclass(frozen=True)
class ManagedGridRow:
    """One editor row for configured entries or known-window proposals."""

    source: str
    section: str
    action: str
    existing_entry: str = ""
    target_entry: str = ""
    profile_filter: str = ""
    existing_profile: str = ""
    new_profile: str = ""
    workspace: str = ""
    geometry: str = ""

    def as_values(self) -> tuple[str, ...]:
        """Return values in a stable order for tests and future list models."""

        return (
            self.source,
            self.section,
            self.action,
            self.existing_entry,
            self.target_entry,
            self.profile_filter,
            self.existing_profile,
            self.new_profile,
            self.workspace,
            self.geometry,
        )

    @classmethod
    def from_values(cls, values: tuple[str, ...]) -> "ManagedGridRow":
        """Build a row from stable-order values."""

        return cls(*values)


@dataclass(frozen=True)
class RuleParts:
    """Parsed rule parts used by grid row builders and widgets."""

    domain: str = ""
    class_name: str = ""
    geometry_profile: str = ""
    left_edge_mode: str = ""


def build_configured_grid_rows(snapshot: TestConfigSnapshot | None) -> tuple[ManagedGridRow, ...]:
    """Flatten current test-config entries into configured editor rows."""

    if snapshot is None or snapshot.config is None:
        return ()

    rows: list[ManagedGridRow] = []
    config = snapshot.config

    rows.extend(
        ManagedGridRow(
            source="configured",
            section="EXCLUDE",
            action="Modify",
            existing_entry=rule,
            target_entry=rule,
        )
        for rule in config.exclude
    )
    rows.extend(
        ManagedGridRow(
            source="configured",
            section="PIN",
            action="Modify",
            existing_entry=rule,
            target_entry=rule,
        )
        for rule in config.pin
    )
    for route in config.workspace_routes:
        rows.extend(
            ManagedGridRow(
                source="configured",
                section="WORKSPACE_ROUTES",
                action="Modify",
                existing_entry=rule,
                target_entry=rule,
                workspace=str(route.workspace),
            )
            for rule in route.rules
        )
    rows.extend(
        ManagedGridRow(
            source="configured",
            section="GEOM",
            action="Modify",
            existing_entry=profile.name,
            existing_profile=profile.name,
            new_profile=profile.name,
            geometry=_geometry_text(profile.x, profile.y, profile.w, profile.h),
        )
        for profile in config.geom
    )
    rows.extend(
        ManagedGridRow(
            source="configured",
            section="WORKSPACE_PLACEMENT",
            action="Modify",
            existing_entry=rule,
            target_entry=rule,
            existing_profile=rule_parts(rule).geometry_profile,
        )
        for rule in config.workspace_placement
    )
    rows.extend(
        ManagedGridRow(
            source="configured",
            section="LEFT_EDGE_CORRECTION",
            action="Modify",
            existing_entry=rule,
            target_entry=rule,
        )
        for rule in config.left_edge_correction
    )
    return tuple(rows)


def build_known_window_grid_rows(
    event_data: WindowEventData | None = None,
    inventory_targets: tuple[KnownWindowTarget, ...] = (),
) -> tuple[ManagedGridRow, ...]:
    """Build not-configured rows from inventory targets or available event data."""

    if inventory_targets:
        return _known_window_target_grid_rows(inventory_targets)
    if event_data is None:
        return ()

    target_rule = _target_rule_from_event(event_data)
    preview = build_event_rule_preview(event_data)
    geometry = event_data.window_geometry
    geometry_text = _geometry_text(
        _event_number_to_text(geometry.x),
        _event_number_to_text(geometry.y),
        _event_number_to_text(geometry.w),
        _event_number_to_text(geometry.h),
    )
    profile_name = preview.geometry_profile_name or ""
    placement_rule = preview.placement_rule or (f"{target_rule} g:{profile_name}" if target_rule and profile_name else "")

    rows = [
        ManagedGridRow(
            source="not configured",
            section="EXCLUDE",
            action="Add",
            target_entry=target_rule,
        ),
        ManagedGridRow(
            source="not configured",
            section="PIN",
            action="Add",
            target_entry=target_rule,
        ),
        ManagedGridRow(
            source="not configured",
            section="WORKSPACE_ROUTES",
            action="Add",
            target_entry=target_rule,
        ),
        ManagedGridRow(
            source="not configured",
            section="GEOM",
            action="Add",
            new_profile=profile_name,
            geometry=geometry_text,
        ),
        ManagedGridRow(
            source="not configured",
            section="WORKSPACE_PLACEMENT",
            action="Add",
            target_entry=placement_rule,
            existing_profile=profile_name,
        ),
        ManagedGridRow(
            source="not configured",
            section="LEFT_EDGE_CORRECTION",
            action="Add",
            target_entry=f"{target_rule} le:pos1" if target_rule else "",
        ),
    ]
    return tuple(row for row in rows if _row_has_candidate_value(row))


def build_available_known_window_grid_rows(
    snapshot: TestConfigSnapshot | None,
    section: str,
    inventory_targets: tuple[KnownWindowTarget, ...],
) -> tuple[ManagedGridRow, ...]:
    """Build section-specific Not configured rows after config suppression."""

    config = snapshot.config if snapshot is not None else None
    available_targets = filter_known_window_targets_for_section(
        inventory_targets,
        config,
        section,
    )
    return tuple(row for row in _known_window_target_grid_rows(available_targets) if row.section == section)


def domain_values(
    snapshot: TestConfigSnapshot | None,
    event_data: WindowEventData | None,
    inventory_targets: tuple[KnownWindowTarget, ...] = (),
) -> tuple[str, ...]:
    """Return domain/machine selector values from config, event data, and inventory."""

    values = {rule_parts(row.target_entry or row.existing_entry).domain for row in build_configured_grid_rows(snapshot)}
    values.update(target.machine for target in inventory_targets)
    event_domain = event_data.display_domain.lower() if event_data and event_data.display_domain else ""
    if event_domain:
        values.add(event_domain)
    values.discard("")
    return tuple(sorted(values))


def class_values(
    snapshot: TestConfigSnapshot | None,
    event_data: WindowEventData | None,
    inventory_targets: tuple[KnownWindowTarget, ...] = (),
) -> tuple[str, ...]:
    """Return class/application selector values from config, event data, and inventory."""

    values = {rule_parts(row.target_entry or row.existing_entry).class_name for row in build_configured_grid_rows(snapshot)}
    values.update(target.application for target in inventory_targets)
    event_class = _class_from_event(event_data)
    if event_class:
        values.add(event_class)
    values.discard("")
    values.difference_update(DEVELOPMENT_SELECTOR_VALUES)
    return tuple(sorted(values))


def profile_names(snapshot: TestConfigSnapshot | None) -> tuple[str, ...]:
    """Return configured geometry profile names."""

    if snapshot is None or snapshot.config is None:
        return ()
    return tuple(profile.name for profile in snapshot.config.geom)


def rule_parts(rule: str) -> RuleParts:
    """Parse a prefixed rule for grid display, returning empty parts on invalid input."""

    if not rule.strip():
        return RuleParts()
    try:
        parsed = parse_prefixed_rule(rule)
    except RuleParseError:
        return RuleParts()
    return RuleParts(
        domain=parsed.domain or "",
        class_name=parsed.class_name or "",
        geometry_profile=parsed.geometry_profile or "",
        left_edge_mode=parsed.left_edge_mode or "",
    )


def _known_window_target_grid_rows(targets: tuple[KnownWindowTarget, ...]) -> tuple[ManagedGridRow, ...]:
    rows: list[ManagedGridRow] = []
    for target in targets:
        target_rule = target.rule
        rows.extend(
            (
                ManagedGridRow(
                    source="not configured",
                    section="EXCLUDE",
                    action="Add",
                    target_entry=target_rule,
                ),
                ManagedGridRow(
                    source="not configured",
                    section="PIN",
                    action="Add",
                    target_entry=target_rule,
                ),
                ManagedGridRow(
                    source="not configured",
                    section="WORKSPACE_ROUTES",
                    action="Add",
                    target_entry=target_rule,
                ),
                ManagedGridRow(
                    source="not configured",
                    section="WORKSPACE_PLACEMENT",
                    action="Add",
                    target_entry=target_rule,
                ),
                ManagedGridRow(
                    source="not configured",
                    section="LEFT_EDGE_CORRECTION",
                    action="Add",
                    target_entry=f"{target_rule} le:pos1",
                ),
            )
        )
    return tuple(rows)


def _geometry_text(x: object, y: object, w: object, h: object) -> str:
    values = tuple(str(value).strip() for value in (x, y, w, h))
    if not any(values):
        return ""
    return f"x={values[0]} y={values[1]} w={values[2]} h={values[3]}"


def _event_number_to_text(value: float | None) -> str:
    if value is None:
        return ""
    return str(int(round(value)))


def _row_has_candidate_value(row: ManagedGridRow) -> bool:
    return bool(row.target_entry or row.new_profile or row.geometry)


def _target_rule_from_event(event: WindowEventData) -> str:
    class_token = _class_from_event(event)
    if not class_token:
        return ""

    domain = event.display_domain
    if domain and not any(char.isspace() for char in domain):
        return f"d:{domain.lower()} c:{class_token}"
    return f"c:{class_token}"


def _class_from_event(event: WindowEventData | None) -> str:
    if event is None:
        return ""
    raw_class = event.class_instance_name or event.window_class or ""
    class_token = raw_class.rsplit(":", 1)[-1].lower()
    if not class_token or any(char.isspace() for char in class_token):
        return ""
    return class_token
