"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from d2wc.test_config import TestConfigSnapshot, format_action_result, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action

EDITOR_ACTIONS = ("Add", "Modify", "Delete")


@dataclass(frozen=True)
class ManagedSectionEditor:
    """Managed-section editor widget plus the Apply callback."""

    widget: object
    apply: Callable[[], None]


def build_managed_section_editor(Gtk, snapshot: TestConfigSnapshot | None, sections_box, refresh_sections) -> ManagedSectionEditor:
    """Build the main managed-section editor for the dedicated test config."""

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

    state: dict[str, TestConfigSnapshot | None] = {"snapshot": snapshot}

    section_combo = _combo_box(Gtk, MANAGED_ACTION_SECTIONS)
    action_combo = _combo_box(Gtk, EDITOR_ACTIONS)
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
    action_label = _text_label(Gtk, format_action_result(None))

    _grid_attach_labeled(Gtk, grid, 0, "Section", section_combo)
    _grid_attach_labeled(Gtk, grid, 1, "Action", action_combo)
    _grid_attach_labeled(Gtk, grid, 2, "Existing entry", existing_combo)
    _grid_attach_labeled(Gtk, grid, 3, "Target entry", target_entry)
    _grid_attach_labeled(Gtk, grid, 4, "Profile filter", profile_filter_entry)
    _grid_attach_labeled(Gtk, grid, 5, "Existing profile", profile_combo)
    _grid_attach_labeled(Gtk, grid, 6, "New profile", new_profile_entry)
    _grid_attach_labeled(Gtk, grid, 7, "Workspace", workspace_entry)
    _grid_attach_labeled(Gtk, grid, 8, "Geometry", _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry))
    grid.attach(action_label, 0, 9, 2, 1)

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

    _refresh_dynamic_choices(state["snapshot"], controls)
    section_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(state["snapshot"], controls))
    action_combo.connect("changed", lambda _combo: _refresh_dynamic_choices(state["snapshot"], controls))
    profile_filter_entry.connect("changed", lambda _entry: _refresh_profile_choices(state["snapshot"], controls))
    existing_combo.connect("changed", lambda _combo: _populate_fields_from_existing(state["snapshot"], controls))
    profile_combo.connect("changed", lambda _combo: _populate_geom_fields_from_profile(state["snapshot"], controls))

    def apply_action() -> None:
        _run_editor_action(Gtk, state, controls, sections_box, refresh_sections)

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


def _request_from_controls(controls: _EditorControls) -> ManagedSectionActionRequest:
    section = controls.section_combo.get_active_text() or ""
    action = (controls.action_combo.get_active_text() or "").lower()
    existing_entry = controls.existing_combo.get_active_text() or ""
    selected_profile = controls.profile_combo.get_active_text() or ""
    profile_name = controls.new_profile_entry.get_text().strip() or selected_profile
    target_entry = controls.target_entry.get_text().strip()

    if section == "WORKSPACE_PLACEMENT" and action in {"add", "modify"} and target_entry and " g:" not in f" {target_entry}":
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
    needs_workspace = section == "WORKSPACE_ROUTES" and edits_values
    needs_profile = section in {"GEOM", "WORKSPACE_PLACEMENT"} and edits_values
    needs_geometry = is_geom and edits_values

    controls.existing_combo.set_sensitive(needs_existing)
    controls.target_entry.set_sensitive(is_rule_section and edits_values)
    controls.workspace_entry.set_sensitive(needs_workspace)
    controls.profile_filter_entry.set_sensitive(needs_profile)
    controls.profile_combo.set_sensitive(needs_profile)
    controls.new_profile_entry.set_sensitive(is_geom and edits_values)
    for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.set_sensitive(needs_geometry)

    if not is_rule_section or not edits_values:
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


def _grid_attach_labeled(Gtk, grid, row: int, label_text: str, widget) -> None:
    label = Gtk.Label(label=label_text)
    label.set_xalign(0)
    grid.attach(label, 0, row, 1, 1)
    grid.attach(widget, 1, row, 1, 1)


def _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry):
    box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    box.set_hexpand(True)
    for entry in (x_entry, y_entry, w_entry, h_entry):
        box.pack_start(entry, True, True, 0)
    return box


def _optional_int(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    return int(stripped)
