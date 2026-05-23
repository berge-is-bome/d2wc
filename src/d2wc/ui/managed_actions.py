"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

from d2wc.test_config import TestConfigSnapshot, format_action_result, format_test_config_status, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action

EDITOR_OPERATIONS = ("add", "modify", "delete")


def build_managed_section_form(Gtk, snapshot: TestConfigSnapshot | None, action_label, status_label, sections_box, refresh_sections):
    """Build a managed-section editor for the dedicated test config."""

    frame = Gtk.Frame(label="Managed section editor")
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

    grid = Gtk.Grid()
    grid.set_row_spacing(8)
    grid.set_column_spacing(8)
    grid.set_margin_top(8)
    grid.set_margin_bottom(8)
    grid.set_margin_start(8)
    grid.set_margin_end(8)
    frame.add(grid)

    section_combo = _combo_box(Gtk, MANAGED_ACTION_SECTIONS)
    operation_combo = _combo_box(Gtk, EDITOR_OPERATIONS)
    existing_combo = Gtk.ComboBoxText()
    target_entry = _entry(Gtk, "Target entry, e.g. d:work c:example")
    profile_filter_entry = _entry(Gtk, "Filter profiles")
    profile_combo = Gtk.ComboBoxText()
    new_profile_entry = _entry(Gtk, "New GEOM profile name")
    workspace_entry = _entry(Gtk, "Workspace number")
    x_entry = _entry(Gtk, "x", width=6)
    y_entry = _entry(Gtk, "y", width=6)
    w_entry = _entry(Gtk, "w", width=6)
    h_entry = _entry(Gtk, "h", width=6)

    _grid_attach_labeled(Gtk, grid, 0, "Section", section_combo)
    _grid_attach_labeled(Gtk, grid, 1, "Operation", operation_combo)
    _grid_attach_labeled(Gtk, grid, 2, "Existing entry", existing_combo)
    _grid_attach_labeled(Gtk, grid, 3, "Target entry", target_entry)
    _grid_attach_labeled(Gtk, grid, 4, "Profile filter", profile_filter_entry)
    _grid_attach_labeled(Gtk, grid, 5, "Existing profile", profile_combo)
    _grid_attach_labeled(Gtk, grid, 6, "New profile", new_profile_entry)
    _grid_attach_labeled(Gtk, grid, 7, "Workspace", workspace_entry)
    _grid_attach_labeled(Gtk, grid, 8, "Geometry", _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry))

    hint = Gtk.Label(
        label=(
            "Target entry is the d2wc target text for EXCLUDE, PIN, WORKSPACE_ROUTES, "
            "WORKSPACE_PLACEMENT, and LEFT_EDGE_CORRECTION.\n"
            "Use Existing entry for modify/delete. Use Existing profile or New profile for GEOM."
        )
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    grid.attach(hint, 0, 9, 2, 1)

    controls = _EditorControls(
        section_combo=section_combo,
        operation_combo=operation_combo,
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
    )

    _refresh_dynamic_choices(Gtk, snapshot, controls)
    section_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(Gtk, snapshot, controls))
    operation_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(Gtk, snapshot, controls))
    profile_filter_entry.connect("changed", lambda _entry: _refresh_profile_choices(snapshot, controls))
    existing_combo.connect("changed", lambda _combo: _populate_fields_from_existing(snapshot, controls))
    profile_combo.connect("changed", lambda _combo: _populate_geom_fields_from_profile(snapshot, controls))

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    save_button = Gtk.Button(label="Save selected operation")
    add_button = Gtk.Button(label="Add")
    modify_button = Gtk.Button(label="Modify")
    delete_button = Gtk.Button(label="Delete")
    for button in (save_button, add_button, modify_button, delete_button):
        button.set_sensitive(snapshot is not None and snapshot.ok)
        button_box.pack_start(button, False, False, 0)

    save_button.connect(
        "clicked",
        lambda _button: _run_editor_action(
            Gtk, snapshot, controls, action_label, status_label, sections_box, refresh_sections
        ),
    )
    add_button.connect(
        "clicked",
        lambda _button: _run_editor_action(
            Gtk, snapshot, controls, action_label, status_label, sections_box, refresh_sections, forced_operation="add"
        ),
    )
    modify_button.connect(
        "clicked",
        lambda _button: _run_editor_action(
            Gtk, snapshot, controls, action_label, status_label, sections_box, refresh_sections, forced_operation="modify"
        ),
    )
    delete_button.connect(
        "clicked",
        lambda _button: _run_editor_action(
            Gtk, snapshot, controls, action_label, status_label, sections_box, refresh_sections, forced_operation="delete"
        ),
    )
    grid.attach(button_box, 0, 10, 2, 1)

    return frame


class _EditorControls:
    def __init__(
        self,
        *,
        section_combo,
        operation_combo,
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
    ) -> None:
        self.section_combo = section_combo
        self.operation_combo = operation_combo
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


def _run_editor_action(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    controls: _EditorControls,
    action_label,
    status_label,
    sections_box,
    refresh_sections,
    *,
    forced_operation: str | None = None,
) -> None:
    if snapshot is None:
        action_label.set_text("Action: managed section edit\nStatus: error\nNo test config is loaded.")
        return

    try:
        request = _request_from_controls(controls, forced_operation=forced_operation)
    except ValueError as exc:
        action_label.set_text(f"Action: managed section edit\nStatus: error\n{exc}")
        return

    result = apply_managed_section_action(snapshot.path, request)
    action_label.set_text(format_action_result(result))
    refreshed_snapshot = load_test_config_snapshot(snapshot.path)
    status_label.set_text(format_test_config_status(refreshed_snapshot))
    refresh_sections(Gtk, sections_box, refreshed_snapshot)
    _refresh_dynamic_choices(Gtk, refreshed_snapshot, controls)


def _request_from_controls(controls: _EditorControls, *, forced_operation: str | None = None) -> ManagedSectionActionRequest:
    section = controls.section_combo.get_active_text() or ""
    operation = forced_operation or controls.operation_combo.get_active_text() or ""
    existing_entry = controls.existing_combo.get_active_text() or ""
    selected_profile = controls.profile_combo.get_active_text() or ""
    profile_name = controls.new_profile_entry.get_text().strip() or selected_profile
    target_entry = controls.target_entry.get_text().strip()

    if section == "WORKSPACE_PLACEMENT" and target_entry and " g:" not in f" {target_entry}":
        if profile_name:
            target_entry = f"{target_entry} g:{profile_name}"
    if section == "GEOM" and operation in {"modify", "delete"} and not profile_name:
        profile_name = selected_profile or existing_entry

    return ManagedSectionActionRequest(
        section=section,
        operation=operation,
        rule=target_entry,
        existing_rule=existing_entry,
        workspace=_optional_int(controls.workspace_entry.get_text()),
        profile_name=profile_name,
        x=_optional_int(controls.x_entry.get_text()),
        y=_optional_int(controls.y_entry.get_text()),
        w=_optional_int(controls.w_entry.get_text()),
        h=_optional_int(controls.h_entry.get_text()),
    )


def _refresh_dynamic_choices(Gtk, snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    section = controls.section_combo.get_active_text() or ""
    operation = controls.operation_combo.get_active_text() or ""
    entries = _entries_for_section(snapshot, section)
    _reset_combo(controls.existing_combo, entries)
    _refresh_profile_choices(snapshot, controls)
    controls.existing_combo.set_sensitive(operation in {"modify", "delete"} and bool(entries))
    controls.profile_filter_entry.set_sensitive(section in {"GEOM", "WORKSPACE_PLACEMENT"})
    controls.profile_combo.set_sensitive(section in {"GEOM", "WORKSPACE_PLACEMENT"})
    controls.new_profile_entry.set_sensitive(section in {"GEOM", "WORKSPACE_PLACEMENT"})
    _populate_fields_from_existing(snapshot, controls)


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
    _reset_combo(controls.profile_combo, profiles)


def _profile_names(snapshot: TestConfigSnapshot | None) -> tuple[str, ...]:
    if snapshot is None or snapshot.config is None:
        return ()
    return tuple(profile.name for profile in snapshot.config.geom)


def _populate_fields_from_existing(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    section = controls.section_combo.get_active_text() or ""
    existing = controls.existing_combo.get_active_text() or ""
    operation = controls.operation_combo.get_active_text() or ""
    if operation not in {"modify", "delete"} or not existing:
        return
    if section == "GEOM":
        controls.new_profile_entry.set_text(existing)
        _populate_geom_fields_from_profile(snapshot, controls)
        return
    controls.target_entry.set_text(existing)


def _populate_geom_fields_from_profile(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    if snapshot is None or snapshot.config is None:
        return
    profile_name = controls.profile_combo.get_active_text() or controls.existing_combo.get_active_text() or ""
    for profile in snapshot.config.geom:
        if profile.name == profile_name:
            controls.new_profile_entry.set_text(profile.name)
            controls.x_entry.set_text(str(profile.x))
            controls.y_entry.set_text(str(profile.y))
            controls.w_entry.set_text(str(profile.w))
            controls.h_entry.set_text(str(profile.h))
            return


def _combo_box(Gtk, values: tuple[str, ...]):
    combo = Gtk.ComboBoxText()
    for value in values:
        combo.append_text(value)
    combo.set_active(0)
    return combo


def _reset_combo(combo, values: tuple[str, ...]) -> None:
    combo.remove_all()
    for value in values:
        combo.append_text(value)
    if values:
        combo.set_active(0)


def _entry(Gtk, placeholder: str, *, width: int | None = None):
    entry = Gtk.Entry()
    entry.set_placeholder_text(placeholder)
    if width is not None:
        entry.set_width_chars(width)
    return entry


def _grid_attach_labeled(Gtk, grid, row: int, label_text: str, widget) -> None:
    label = Gtk.Label(label=label_text)
    label.set_xalign(0)
    grid.attach(label, 0, row, 1, 1)
    grid.attach(widget, 1, row, 1, 1)


def _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    for entry in (x_entry, y_entry, w_entry, h_entry):
        box.pack_start(entry, False, False, 0)
    return box


def _optional_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)
