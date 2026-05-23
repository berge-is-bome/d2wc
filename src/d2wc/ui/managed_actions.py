"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from d2wc.event_data import WindowEventData
from d2wc.event_preview import build_event_rule_preview
from d2wc.test_config import TestConfigSnapshot, format_action_result, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action

EDITOR_ACTIONS = ("Add", "Modify", "Delete")
SECTION_LABELS = {
    "EXCLUDE": "Exclude",
    "PIN": "Pin",
    "WORKSPACE_ROUTES": "Workspace routes",
    "GEOM": "Geometry",
    "WORKSPACE_PLACEMENT": "Workspace placement",
    "LEFT_EDGE_CORRECTION": "Left edge correction",
}
SECTION_BY_LABEL = {label: section for section, label in SECTION_LABELS.items()}
SECTION_COLUMNS = {
    "EXCLUDE": ("Action", "Existing entry", "Target entry"),
    "PIN": ("Action", "Existing entry", "Target entry"),
    "WORKSPACE_ROUTES": ("Action", "Existing entry", "Target entry", "Workspace"),
    "GEOM": ("Action", "Existing profile", "New profile", "Geometry"),
    "WORKSPACE_PLACEMENT": ("Action", "Existing entry", "Target entry", "Profile filter", "Existing profile"),
    "LEFT_EDGE_CORRECTION": ("Action", "Existing entry", "Target entry"),
}


@dataclass(frozen=True)
class ManagedSectionEditor:
    """Managed-section editor widget plus the Apply callback."""

    widget: object
    apply: Callable[[], None]


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
    def from_values(cls, values: tuple[str, ...]) -> ManagedGridRow:
        """Build a row from stable-order values."""

        return cls(*values)


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
            existing_profile=_profile_from_rule(rule),
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


def build_known_window_grid_rows(event_data: WindowEventData | None) -> tuple[ManagedGridRow, ...]:
    """Build not-configured rows from currently available event data."""

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


def build_managed_section_editor(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    sections_box,
    refresh_sections,
    event_data: WindowEventData | None = None,
) -> ManagedSectionEditor:
    """Build the section-focused managed editor for the dedicated test config."""

    frame = Gtk.Frame(label="Managed section editor")
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    main_box.set_margin_top(8)
    main_box.set_margin_bottom(8)
    main_box.set_margin_start(8)
    main_box.set_margin_end(8)
    frame.add(main_box)

    state: dict[str, object] = {
        "snapshot": snapshot,
        "show_not_configured": False,
        "row_controls": [],
    }

    top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    main_box.pack_start(top_bar, False, False, 0)

    section_combo = _section_combo(Gtk)
    top_bar.pack_start(section_combo, False, False, 0)

    mode_button = Gtk.Button(label="Not configured")
    top_bar.pack_start(mode_button, False, False, 0)

    rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    main_box.pack_start(rows_box, True, True, 0)

    status_label = _text_label(Gtk, format_action_result(None))
    main_box.pack_start(status_label, False, False, 0)

    def current_snapshot() -> TestConfigSnapshot | None:
        return state["snapshot"] if isinstance(state["snapshot"], TestConfigSnapshot) else None

    def current_section() -> str:
        return _section_from_combo(section_combo)

    def refresh_editor_rows() -> None:
        for child in rows_box.get_children():
            rows_box.remove(child)
        row_controls: list[_EditorControls] = []
        state["row_controls"] = row_controls

        section = current_section()
        show_not_configured = bool(state["show_not_configured"])
        rows = _rows_for_section(current_snapshot(), event_data, section, show_not_configured)
        if rows:
            rows_box.pack_start(
                _build_section_rows_grid(
                    Gtk,
                    current_snapshot(),
                    section,
                    rows,
                    status_label,
                    row_controls,
                    apply_row_action,
                ),
                True,
                True,
                0,
            )
        else:
            empty_text = (
                "No not-configured windows are available for this section yet."
                if show_not_configured
                else "No configured entries are available for this section."
            )
            rows_box.pack_start(_text_label(Gtk, empty_text), False, False, 0)

        rows_box.show_all()

    def apply_row_action(controls: _EditorControls) -> None:
        snapshot_value = current_snapshot()
        if snapshot_value is None:
            status_label.set_text("Action: managed section edit\nStatus: error\nNo test config is loaded.")
            return

        try:
            request = _request_from_controls(controls)
        except ValueError as exc:
            status_label.set_text(f"Action: managed section edit\nStatus: error\n{exc}")
            return

        result = apply_managed_section_action(snapshot_value.path, request)
        status_label.set_text(format_action_result(result))
        refreshed_snapshot = load_test_config_snapshot(snapshot_value.path)
        state["snapshot"] = refreshed_snapshot
        refresh_sections(Gtk, sections_box, refreshed_snapshot)
        if result.ok:
            refresh_editor_rows()

    def apply_first_row() -> None:
        row_controls = state["row_controls"]
        if isinstance(row_controls, list) and row_controls:
            apply_row_action(row_controls[0])
        else:
            status_label.set_text("Action: managed section edit\nStatus: error\nNo editable row is available.")

    def toggle_mode() -> None:
        state["show_not_configured"] = not bool(state["show_not_configured"])
        mode_button.set_label("Configured" if state["show_not_configured"] else "Not configured")
        refresh_editor_rows()

    section_combo.connect("changed", lambda _combo: refresh_editor_rows())
    mode_button.connect("clicked", lambda _button: toggle_mode())
    refresh_editor_rows()

    return ManagedSectionEditor(widget=frame, apply=apply_first_row)


class _EditorControls:
    def __init__(
        self,
        *,
        section: str,
        action_combo,
        existing_combo,
        target_entry,
        profile_filter_entry,
        profile_combo,
        new_profile_entry,
        workspace_entry,
        x_entry,
        y_entry,
        w_entry,
        h_entry,
        action_label,
    ) -> None:
        self.section = section
        self.action_combo = action_combo
        self.existing_combo = existing_combo
        self.target_entry = target_entry
        self.profile_filter_entry = profile_filter_entry
        self.profile_combo = profile_combo
        self.new_profile_entry = new_profile_entry
        self.workspace_entry = workspace_entry
        self.x_entry = x_entry
        self.y_entry = y_entry
        self.w_entry = w_entry
        self.h_entry = h_entry
        self.action_label = action_label


def _rows_for_section(
    snapshot: TestConfigSnapshot | None,
    event_data: WindowEventData | None,
    section: str,
    show_not_configured: bool,
) -> tuple[ManagedGridRow, ...]:
    if show_not_configured:
        return tuple(row for row in build_known_window_grid_rows(event_data) if row.section == section)

    configured_rows = tuple(row for row in build_configured_grid_rows(snapshot) if row.section == section)
    if snapshot is None or snapshot.config is None:
        return configured_rows
    return (_blank_add_row(section), *configured_rows)


def _blank_add_row(section: str) -> ManagedGridRow:
    return ManagedGridRow(source="configured", section=section, action="Add")


def _build_section_rows_grid(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    section: str,
    rows: tuple[ManagedGridRow, ...],
    status_label,
    row_controls: list[_EditorControls],
    apply_row_action,
):
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    scroller.set_size_request(-1, 220)

    grid = Gtk.Grid()
    grid.set_row_spacing(6)
    grid.set_column_spacing(8)
    grid.set_margin_top(8)
    grid.set_margin_bottom(8)
    grid.set_margin_start(8)
    grid.set_margin_end(8)
    scroller.add(grid)

    columns = SECTION_COLUMNS[section]
    for column_index, column_name in enumerate((*columns, "Apply")):
        label = Gtk.Label(label=column_name)
        label.set_xalign(0)
        grid.attach(label, column_index, 0, 1, 1)

    for row_index, row in enumerate(rows, start=1):
        controls = _build_row_controls(Gtk, snapshot, section, row, status_label)
        row_controls.append(controls)
        for column_index, column_name in enumerate(columns):
            grid.attach(_widget_for_column(Gtk, controls, column_name), column_index, row_index, 1, 1)

        apply_button = Gtk.Button(label="Apply")
        apply_button.connect("clicked", lambda _button, row_controls=controls: apply_row_action(row_controls))
        grid.attach(apply_button, len(columns), row_index, 1, 1)

    return scroller


def _build_row_controls(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    section: str,
    row: ManagedGridRow,
    status_label,
) -> _EditorControls:
    action_combo = _combo_box(Gtk, EDITOR_ACTIONS)
    existing_combo = Gtk.ComboBoxText()
    target_entry = _entry(Gtk, "Target entry", width=28)
    profile_filter_entry = _entry(Gtk, "Filter", width=12)
    profile_combo = Gtk.ComboBoxText()
    new_profile_entry = _entry(Gtk, "New profile", width=18)
    workspace_entry = _entry(Gtk, "Workspace", width=8)
    x_entry = _entry(Gtk, "x", width=6)
    y_entry = _entry(Gtk, "y", width=6)
    w_entry = _entry(Gtk, "w", width=6)
    h_entry = _entry(Gtk, "h", width=6)

    controls = _EditorControls(
        section=section,
        action_combo=action_combo,
        existing_combo=existing_combo,
        target_entry=target_entry,
        profile_filter_entry=profile_filter_entry,
        profile_combo=profile_combo,
        new_profile_entry=new_profile_entry,
        workspace_entry=workspace_entry,
        x_entry=x_entry,
        y_entry=y_entry,
        w_entry=w_entry,
        h_entry=h_entry,
        action_label=status_label,
    )

    _reset_combo(existing_combo, _entries_for_section(snapshot, section), include_blank=True)
    _refresh_profile_choices(snapshot, controls)
    _populate_controls_from_grid_row(snapshot, controls, row)

    action_combo.connect("changed", lambda _combo: _set_field_sensitivity(section, _active_action(controls), controls))
    profile_filter_entry.connect("changed", lambda _entry: _refresh_profile_choices(snapshot, controls))
    existing_combo.connect("changed", lambda _combo: _populate_fields_from_existing(snapshot, controls))
    profile_combo.connect("changed", lambda _combo: _populate_geom_fields_from_profile(snapshot, controls))
    _set_field_sensitivity(section, _active_action(controls), controls)
    return controls


def _widget_for_column(Gtk, controls: _EditorControls, column_name: str):
    if column_name == "Action":
        return controls.action_combo
    if column_name == "Existing entry":
        return controls.existing_combo
    if column_name == "Target entry":
        return controls.target_entry
    if column_name == "Profile filter":
        return controls.profile_filter_entry
    if column_name == "Existing profile":
        return controls.profile_combo
    if column_name == "New profile":
        return controls.new_profile_entry
    if column_name == "Workspace":
        return controls.workspace_entry
    if column_name == "Geometry":
        return _geometry_box(Gtk, controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry)
    return _text_label(Gtk, "")


def _request_from_controls(controls: _EditorControls) -> ManagedSectionActionRequest:
    section = controls.section
    action = _active_action(controls).lower()
    existing_entry = controls.existing_combo.get_active_text() or ""
    selected_profile = controls.profile_combo.get_active_text() or ""
    profile_name = controls.new_profile_entry.get_text().strip() or selected_profile
    target_entry = controls.target_entry.get_text().strip()

    if section == "WORKSPACE_PLACEMENT" and action == "modify" and existing_entry:
        if not profile_name:
            raise ValueError("WORKSPACE_PLACEMENT modify requires an existing profile selection")
        target_entry = _replace_rule_profile(existing_entry, profile_name)
    elif section == "WORKSPACE_PLACEMENT" and action == "add" and target_entry and " g:" not in f" {target_entry}":
        if profile_name:
            target_entry = f"{target_entry} g:{profile_name}"
    if section == "GEOM" and action in {"modify", "delete"} and not profile_name:
        profile_name = selected_profile or existing_entry

    return ManagedSectionActionRequest(
        section=section,
        operation=action,
        rule=target_entry,
        existing_rule=existing_entry,
        workspace=_optional_int(controls.workspace_entry.get_text()),
        profile_name=profile_name,
        x=_optional_int(controls.x_entry.get_text()),
        y=_optional_int(controls.y_entry.get_text()),
        w=_optional_int(controls.w_entry.get_text()),
        h=_optional_int(controls.h_entry.get_text()),
    )


def _clear_action_fields(controls: _EditorControls) -> None:
    controls.existing_combo.set_active(0)
    controls.target_entry.set_text("")
    controls.profile_filter_entry.set_text("")
    controls.profile_combo.set_active(0)
    controls.new_profile_entry.set_text("")
    controls.workspace_entry.set_text("")
    for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.set_text("")


def _set_field_sensitivity(section: str, action: str, controls: _EditorControls) -> None:
    is_rule_section = section in {"EXCLUDE", "PIN", "WORKSPACE_ROUTES", "WORKSPACE_PLACEMENT", "LEFT_EDGE_CORRECTION"}
    is_geom = section == "GEOM"
    normalized_action = action.lower()
    edits_values = normalized_action in {"add", "modify"}
    needs_existing = normalized_action in {"modify", "delete"}
    target_editable = is_rule_section and edits_values and not (section == "WORKSPACE_PLACEMENT" and normalized_action == "modify")
    needs_workspace = section == "WORKSPACE_ROUTES" and edits_values
    needs_profile = section in {"GEOM", "WORKSPACE_PLACEMENT"} and edits_values
    needs_geometry = is_geom and edits_values

    controls.existing_combo.set_sensitive(needs_existing)
    controls.target_entry.set_sensitive(target_editable)
    controls.workspace_entry.set_sensitive(needs_workspace)
    controls.profile_filter_entry.set_sensitive(needs_profile)
    controls.profile_combo.set_sensitive(needs_profile or (is_geom and needs_existing))
    controls.new_profile_entry.set_sensitive(is_geom and edits_values)
    for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.set_sensitive(needs_geometry)

    if not target_editable:
        controls.target_entry.set_text("")
    if not needs_workspace:
        controls.workspace_entry.set_text("")
    if not needs_profile and not is_geom:
        controls.profile_filter_entry.set_text("")
        controls.new_profile_entry.set_text("")
    if not needs_geometry:
        for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
            entry.set_text("")


def _entries_for_section(snapshot: TestConfigSnapshot | None, section: str) -> tuple[str, ...]:
    if snapshot is None or snapshot.config is None:
        return ()
    config = snapshot.config
    if section == "EXCLUDE":
        return config.exclude
    if section == "PIN":
        return config.pin
    if section == "WORKSPACE_ROUTES":
        return tuple(rule for route in config.workspace_routes for rule in route.rules)
    if section == "GEOM":
        return tuple(profile.name for profile in config.geom)
    if section == "WORKSPACE_PLACEMENT":
        return config.workspace_placement
    if section == "LEFT_EDGE_CORRECTION":
        return config.left_edge_correction
    return ()


def _refresh_profile_choices(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    current = controls.profile_combo.get_active_text() or ""
    profiles = _profile_names(snapshot)
    filter_text = controls.profile_filter_entry.get_text().strip().lower()
    if filter_text:
        profiles = tuple(profile for profile in profiles if filter_text in profile.lower())
    _reset_combo(controls.profile_combo, profiles, include_blank=True)
    if current:
        _set_combo_active_text(controls.profile_combo, current)


def _profile_names(snapshot: TestConfigSnapshot | None) -> tuple[str, ...]:
    if snapshot is None or snapshot.config is None:
        return ()
    return tuple(profile.name for profile in snapshot.config.geom)


def _populate_fields_from_existing(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    section = controls.section
    action = _active_action(controls).lower()
    existing = controls.existing_combo.get_active_text() or ""
    if action not in {"modify", "delete"} or not existing:
        return
    if section == "GEOM":
        controls.new_profile_entry.set_text(existing)
        _populate_geom_fields_from_profile(snapshot, controls, profile_name=existing)
        return
    if section == "WORKSPACE_PLACEMENT":
        controls.target_entry.set_text("")
        profile_name = _profile_from_rule(existing)
        if profile_name:
            _set_combo_active_text(controls.profile_combo, profile_name)
        return
    if action == "modify":
        controls.target_entry.set_text(existing)


def _populate_geom_fields_from_profile(snapshot: TestConfigSnapshot | None, controls: _EditorControls, *, profile_name: str | None = None) -> None:
    if snapshot is None or snapshot.config is None:
        return
    active_profile = profile_name or controls.profile_combo.get_active_text() or controls.existing_combo.get_active_text() or ""
    for profile in snapshot.config.geom:
        if profile.name == active_profile:
            controls.new_profile_entry.set_text(profile.name)
            controls.x_entry.set_text(str(profile.x))
            controls.y_entry.set_text(str(profile.y))
            controls.w_entry.set_text(str(profile.w))
            controls.h_entry.set_text(str(profile.h))
            return


def _populate_controls_from_grid_row(
    snapshot: TestConfigSnapshot | None,
    controls: _EditorControls,
    row: ManagedGridRow,
) -> None:
    _set_combo_active_text(controls.action_combo, row.action)
    if row.existing_entry:
        _set_combo_active_text(controls.existing_combo, row.existing_entry)
    controls.target_entry.set_text(row.target_entry)
    controls.profile_filter_entry.set_text(row.profile_filter)
    _refresh_profile_choices(snapshot, controls)
    if row.existing_profile:
        _set_combo_active_text(controls.profile_combo, row.existing_profile)
    controls.new_profile_entry.set_text(row.new_profile)
    controls.workspace_entry.set_text(row.workspace)
    _set_geometry_fields_from_text(controls, row.geometry)


def _row_has_candidate_value(row: ManagedGridRow) -> bool:
    return bool(row.target_entry or row.new_profile or row.geometry)


def _target_rule_from_event(event: WindowEventData) -> str:
    raw_class = event.class_instance_name or event.window_class or ""
    class_token = raw_class.rsplit(":", 1)[-1].lower()
    if not class_token or any(char.isspace() for char in class_token):
        return ""

    domain = event.display_domain
    if domain and not any(char.isspace() for char in domain):
        return f"d:{domain.lower()} c:{class_token}"
    return f"c:{class_token}"


def _profile_from_rule(rule: str) -> str:
    for token in rule.split():
        if token.startswith("g:"):
            return token[2:]
    return ""


def _replace_rule_profile(rule: str, profile_name: str) -> str:
    tokens = rule.split()
    replaced = False
    new_tokens = []
    for token in tokens:
        if token.startswith("g:"):
            new_tokens.append(f"g:{profile_name}")
            replaced = True
        else:
            new_tokens.append(token)
    if not replaced:
        new_tokens.append(f"g:{profile_name}")
    return " ".join(new_tokens)


def _section_combo(Gtk):
    combo = Gtk.ComboBoxText()
    for section in MANAGED_ACTION_SECTIONS:
        combo.append_text(SECTION_LABELS[section])
    combo.set_active(0)
    return combo


def _section_from_combo(combo) -> str:
    label = combo.get_active_text() or SECTION_LABELS[MANAGED_ACTION_SECTIONS[0]]
    return SECTION_BY_LABEL.get(label, MANAGED_ACTION_SECTIONS[0])


def _active_action(controls: _EditorControls) -> str:
    return controls.action_combo.get_active_text() or EDITOR_ACTIONS[0]


def _set_combo_active_text(combo, value: str) -> None:
    model = combo.get_model()
    if model is None:
        return
    for index, row in enumerate(model):
        if row[0] == value:
            combo.set_active(index)
            return


def _combo_box(Gtk, values: tuple[str, ...]):
    combo = Gtk.ComboBoxText()
    for value in values:
        combo.append_text(value)
    combo.set_active(0)
    combo.set_hexpand(True)
    return combo


def _reset_combo(combo, values: tuple[str, ...], *, include_blank: bool = False) -> None:
    combo.remove_all()
    if include_blank:
        combo.append_text("")
    for value in values:
        combo.append_text(value)
    combo.set_active(0)


def _entry(Gtk, placeholder: str, *, width: int | None = None):
    entry = Gtk.Entry()
    entry.set_placeholder_text(placeholder)
    entry.set_hexpand(True)
    if width is not None:
        entry.set_width_chars(width)
    return entry


def _text_label(Gtk, text: str):
    label = Gtk.Label(label=text)
    label.set_xalign(0)
    label.set_yalign(0)
    label.set_selectable(True)
    label.set_line_wrap(True)
    return label


def _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
    box.set_hexpand(True)
    for entry in (x_entry, y_entry, w_entry, h_entry):
        box.pack_start(entry, True, True, 0)
    return box


def _geometry_text(x: object, y: object, w: object, h: object) -> str:
    return f"x={x} y={y} w={w} h={h}"


def _set_geometry_fields_from_text(controls: _EditorControls, geometry: str) -> None:
    if not geometry:
        return

    values: dict[str, str] = {}
    for token in geometry.split():
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        values[key] = value

    controls.x_entry.set_text(values.get("x", ""))
    controls.y_entry.set_text(values.get("y", ""))
    controls.w_entry.set_text(values.get("w", ""))
    controls.h_entry.set_text(values.get("h", ""))


def _event_number_to_text(value: float | None) -> str:
    if value is None:
        return ""
    return str(int(round(value)))


def _optional_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)