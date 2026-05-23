"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from d2wc.event_data import WindowEventData
from d2wc.event_preview import build_event_rule_preview
from d2wc.test_config import TestConfigSnapshot, format_action_result, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action

EDITOR_ACTIONS = ("Add", "Modify", "Delete")
GRID_COLUMNS = (
    "Source",
    "Section",
    "Action",
    "Existing entry",
    "Target entry",
    "Profile filter",
    "Existing profile",
    "New profile",
    "Workspace",
    "Geometry",
)


@dataclass(frozen=True)
class ManagedSectionEditor:
    """Managed-section editor widget plus the Apply callback."""

    widget: object
    apply: Callable[[], None]


@dataclass(frozen=True)
class ManagedGridRow:
    """One landscape grid row for configured entries or known-window proposals."""

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
        """Return values in display-column order."""

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
        """Build a row from display-column values."""

        return cls(*values)


def build_configured_grid_rows(snapshot: TestConfigSnapshot | None) -> tuple[ManagedGridRow, ...]:
    """Flatten current test-config entries into top-grid rows."""

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
    """Build bottom-grid rows from currently available event data."""

    if event_data is None:
        return ()

    preview = build_event_rule_preview(event_data)
    if not preview.ok:
        return (
            ManagedGridRow(
                source="known window",
                section="WORKSPACE_PLACEMENT",
                action="Add",
                target_entry=preview.warning or "No safe proposal is available.",
            ),
        )

    geometry = event_data.window_geometry
    return (
        ManagedGridRow(
            source="known window",
            section="GEOM",
            action="Add",
            new_profile=preview.geometry_profile_name or "",
            geometry=_geometry_text(
                _event_number_to_text(geometry.x),
                _event_number_to_text(geometry.y),
                _event_number_to_text(geometry.w),
                _event_number_to_text(geometry.h),
            ),
        ),
        ManagedGridRow(
            source="known window",
            section="WORKSPACE_PLACEMENT",
            action="Add",
            target_entry=preview.placement_rule or "",
            existing_profile=preview.geometry_profile_name or "",
        ),
    )


def build_managed_section_editor(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    sections_box,
    refresh_sections,
    event_data: WindowEventData | None = None,
) -> ManagedSectionEditor:
    """Build the landscape managed-section grid editor for the dedicated test config."""

    frame = Gtk.Frame(label="Managed section grid editor")
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    main_box.set_margin_top(8)
    main_box.set_margin_bottom(8)
    main_box.set_margin_start(8)
    main_box.set_margin_end(8)
    frame.add(main_box)

    state: dict[str, TestConfigSnapshot | None] = {"snapshot": snapshot}
    selected_state: dict[str, ManagedGridRow | None] = {"row": None}

    section_combo = _combo_box(Gtk, MANAGED_ACTION_SECTIONS)
    action_combo = _combo_box(Gtk, EDITOR_ACTIONS)
    existing_combo = Gtk.ComboBoxText()
    target_entry = _entry(Gtk, "Target entry, e.g. d:work c:example", width=28)
    profile_filter_entry = _entry(Gtk, "Filter profiles", width=14)
    profile_combo = Gtk.ComboBoxText()
    new_profile_entry = _entry(Gtk, "New GEOM profile name", width=18)
    workspace_entry = _entry(Gtk, "Workspace", width=8)
    x_entry = _entry(Gtk, "x", width=6)
    y_entry = _entry(Gtk, "y", width=6)
    w_entry = _entry(Gtk, "w", width=6)
    h_entry = _entry(Gtk, "h", width=6)
    action_label = _text_label(Gtk, format_action_result(None))

    controls = _EditorControls(
        section_combo=section_combo,
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
        action_label=action_label,
    )

    selection_buttons = _SelectionButtons()

    def select_row(row: ManagedGridRow) -> None:
        selected_state["row"] = row
        _populate_controls_from_grid_row(state["snapshot"], controls, row)
        selection_buttons.set_sensitive(True)
        controls.action_label.set_text(
            "Selected row:\n"
            f"{row.source}: {row.section} {row.action}\n"
            "Use Apply selected row, adjust the row fields, or Cancel selection."
        )

    configured_rows = build_configured_grid_rows(snapshot)
    known_rows = build_known_window_grid_rows(event_data)

    main_box.pack_start(
        _build_rows_frame(
            Gtk,
            "Configured entries",
            configured_rows,
            "No configured entries are available. Load a valid test config first.",
            select_row,
        ),
        True,
        True,
        0,
    )
    main_box.pack_start(
        _build_rows_frame(
            Gtk,
            "Known windows",
            known_rows,
            "No known-window inventory is available yet. Event handoff will populate this area later.",
            select_row,
        ),
        False,
        False,
        0,
    )

    edit_frame = Gtk.Frame(label="Selected row editor")
    edit_grid = Gtk.Grid()
    edit_grid.set_row_spacing(6)
    edit_grid.set_column_spacing(8)
    edit_grid.set_margin_top(8)
    edit_grid.set_margin_bottom(8)
    edit_grid.set_margin_start(8)
    edit_grid.set_margin_end(8)
    edit_frame.add(edit_grid)
    main_box.pack_start(edit_frame, False, False, 0)

    _grid_attach_column(Gtk, edit_grid, 0, "Section", section_combo)
    _grid_attach_column(Gtk, edit_grid, 1, "Action", action_combo)
    _grid_attach_column(Gtk, edit_grid, 2, "Existing entry", existing_combo)
    _grid_attach_column(Gtk, edit_grid, 3, "Target entry", target_entry)
    _grid_attach_column(Gtk, edit_grid, 4, "Profile filter", profile_filter_entry)
    _grid_attach_column(Gtk, edit_grid, 5, "Existing profile", profile_combo)
    _grid_attach_column(Gtk, edit_grid, 6, "New profile", new_profile_entry)
    _grid_attach_column(Gtk, edit_grid, 7, "Workspace", workspace_entry)
    _grid_attach_column(Gtk, edit_grid, 8, "Geometry", _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry))

    row_button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    apply_row_button = Gtk.Button(label="Apply selected row")
    cancel_row_button = Gtk.Button(label="Cancel selection")
    row_button_box.pack_start(apply_row_button, False, False, 0)
    row_button_box.pack_start(cancel_row_button, False, False, 0)
    edit_grid.attach(row_button_box, 0, 2, 4, 1)
    edit_grid.attach(action_label, 4, 2, 5, 1)
    selection_buttons.apply_button = apply_row_button
    selection_buttons.cancel_button = cancel_row_button
    selection_buttons.set_sensitive(False)

    _refresh_dynamic_choices(state["snapshot"], controls)
    section_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(state["snapshot"], controls))
    action_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(state["snapshot"], controls))
    profile_filter_entry.connect("changed", lambda _entry: _refresh_profile_choices(state["snapshot"], controls))
    existing_combo.connect("changed", lambda _combo: _populate_fields_from_existing(state["snapshot"], controls))
    profile_combo.connect("changed", lambda _combo: _populate_geom_fields_from_profile(state["snapshot"], controls))

    def apply_action() -> None:
        _run_editor_action(Gtk, state, controls, sections_box, refresh_sections)

    def cancel_selection() -> None:
        selected_state["row"] = None
        selection_buttons.set_sensitive(False)
        _clear_action_fields(controls)
        controls.action_label.set_text(format_action_result(None))

    apply_row_button.connect("clicked", lambda _button: apply_action())
    cancel_row_button.connect("clicked", lambda _button: cancel_selection())

    return ManagedSectionEditor(widget=frame, apply=apply_action)


class _EditorControls:
    def __init__(
        self,
        *,
        section_combo,
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
        self.section_combo = section_combo
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


class _SelectionButtons:
    def __init__(self) -> None:
        self.apply_button = None
        self.cancel_button = None

    def set_sensitive(self, sensitive: bool) -> None:
        for button in (self.apply_button, self.cancel_button):
            if button is not None:
                button.set_sensitive(sensitive)


def _run_editor_action(
    Gtk,
    state: dict[str, TestConfigSnapshot | None],
    controls: _EditorControls,
    sections_box,
    refresh_sections,
) -> None:
    snapshot = state["snapshot"]
    if snapshot is None:
        controls.action_label.set_text("Action: managed section edit\nStatus: error\nNo test config is loaded.")
        return

    try:
        request = _request_from_controls(controls)
    except ValueError as exc:
        controls.action_label.set_text(f"Action: managed section edit\nStatus: error\n{exc}")
        return

    result = apply_managed_section_action(snapshot.path, request)
    controls.action_label.set_text(format_action_result(result))
    refreshed_snapshot = load_test_config_snapshot(snapshot.path)
    state["snapshot"] = refreshed_snapshot
    refresh_sections(Gtk, sections_box, refreshed_snapshot)
    _refresh_dynamic_choices(refreshed_snapshot, controls)
    if result.ok:
        _clear_action_fields(controls)


def _request_from_controls(controls: _EditorControls) -> ManagedSectionActionRequest:
    section = controls.section_combo.get_active_text() or ""
    action = (controls.action_combo.get_active_text() or "").lower()
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


def _refresh_dynamic_choices(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    section = controls.section_combo.get_active_text() or ""
    action = (controls.action_combo.get_active_text() or "").lower()
    entries = _entries_for_section(snapshot, section)
    _reset_combo(controls.existing_combo, entries, include_blank=True)
    _refresh_profile_choices(snapshot, controls)
    _set_field_sensitivity(section, action, controls)
    _populate_fields_from_existing(snapshot, controls)


def _set_field_sensitivity(section: str, action: str, controls: _EditorControls) -> None:
    is_rule_section = section in {"EXCLUDE", "PIN", "WORKSPACE_ROUTES", "WORKSPACE_PLACEMENT", "LEFT_EDGE_CORRECTION"}
    is_geom = section == "GEOM"
    edits_values = action in {"add", "modify"}
    needs_existing = action in {"modify", "delete"}
    target_editable = is_rule_section and edits_values and not (section == "WORKSPACE_PLACEMENT" and action == "modify")
    needs_workspace = section == "WORKSPACE_ROUTES" and edits_values
    needs_profile = section in {"GEOM", "WORKSPACE_PLACEMENT"} and edits_values
    needs_geometry = is_geom and edits_values

    controls.existing_combo.set_sensitive(needs_existing)
    controls.target_entry.set_sensitive(target_editable)
    controls.workspace_entry.set_sensitive(needs_workspace)
    controls.profile_filter_entry.set_sensitive(needs_profile)
    controls.profile_combo.set_sensitive(needs_profile)
    controls.new_profile_entry.set_sensitive(is_geom and edits_values)
    for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.set_sensitive(needs_geometry)

    if not target_editable:
        controls.target_entry.set_text("")
    if not needs_workspace:
        controls.workspace_entry.set_text("")
    if not needs_profile:
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
    profiles = _profile_names(snapshot)
    filter_text = controls.profile_filter_entry.get_text().strip().lower()
    if filter_text:
        profiles = tuple(profile for profile in profiles if filter_text in profile.lower())
    _reset_combo(controls.profile_combo, profiles, include_blank=True)


def _profile_names(snapshot: TestConfigSnapshot | None) -> tuple[str, ...]:
    if snapshot is None or snapshot.config is None:
        return ()
    return tuple(profile.name for profile in snapshot.config.geom)


def _populate_fields_from_existing(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    section = controls.section_combo.get_active_text() or ""
    action = (controls.action_combo.get_active_text() or "").lower()
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
    _set_combo_active_text(controls.section_combo, row.section)
    _set_combo_active_text(controls.action_combo, row.action)
    _refresh_dynamic_choices(snapshot, controls)

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


def _build_rows_frame(Gtk, title: str, rows: tuple[ManagedGridRow, ...], empty_text: str, on_select) -> object:
    frame = Gtk.Frame(label=title)
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.set_margin_top(8)
    box.set_margin_bottom(8)
    box.set_margin_start(8)
    box.set_margin_end(8)
    frame.add(box)

    if not rows:
        box.pack_start(_text_label(Gtk, empty_text), False, False, 0)
        return frame

    store = Gtk.ListStore(*(str for _column in GRID_COLUMNS))
    for row in rows:
        store.append(row.as_values())

    view = Gtk.TreeView(model=store)
    view.set_headers_visible(True)
    view.set_hexpand(True)
    view.set_vexpand(True)
    view.get_selection().set_mode(Gtk.SelectionMode.SINGLE)

    for index, column_name in enumerate(GRID_COLUMNS):
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn(column_name, renderer, text=index)
        column.set_resizable(True)
        column.set_min_width(90)
        view.append_column(column)

    view.get_selection().connect("changed", lambda selection: _handle_grid_selection(selection, on_select))

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    scroller.set_size_request(-1, 150)
    scroller.add(view)
    box.pack_start(scroller, True, True, 0)
    return frame


def _handle_grid_selection(selection, on_select) -> None:
    model, tree_iter = selection.get_selected()
    if tree_iter is None:
        return
    values = tuple(model[tree_iter][index] for index in range(len(GRID_COLUMNS)))
    on_select(ManagedGridRow.from_values(values))


def _grid_attach_column(Gtk, grid, column: int, label_text: str, widget) -> None:
    label = Gtk.Label(label=label_text)
    label.set_xalign(0)
    grid.attach(label, column, 0, 1, 1)
    grid.attach(widget, column, 1, 1, 1)


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