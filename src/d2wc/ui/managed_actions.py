"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Callable

from d2wc.core.rule_grammar import LEFT_EDGE_MODES, RuleParseError, parse_prefixed_rule
from d2wc.event_data import WindowEventData
from d2wc.event_preview import build_event_rule_preview
from d2wc.test_config import TestConfigSnapshot, format_action_result, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action

EDITOR_ACTIONS = ("Add", "Modify", "Delete")
ROW_CSS = """
eventbox.d2wc-row-add,
.d2wc-row-add {
  background-color: #159b63;
  border-radius: 8px;
}
eventbox.d2wc-row-modify,
.d2wc-row-modify {
  background-color: #6a35e8;
  border-radius: 8px;
}
eventbox.d2wc-row-delete,
.d2wc-row-delete {
  background-color: #cf2d56;
  border-radius: 8px;
}
button.d2wc-apply-add,
.d2wc-apply-add {
  background-image: none;
  background-color: #159b63;
  color: #ffffff;
}
button.d2wc-apply-modify,
.d2wc-apply-modify {
  background-image: none;
  background-color: #6a35e8;
  color: #ffffff;
}
button.d2wc-apply-delete,
.d2wc-apply-delete {
  background-image: none;
  background-color: #cf2d56;
  color: #ffffff;
}
button.d2wc-apply-dirty,
.d2wc-apply-dirty {
  background-image: none;
  background-color: #e0a323;
  color: #1d1d1d;
}
"""
SECTION_LABELS = {
    "EXCLUDE": "Exclude",
    "PIN": "Pin",
    "WORKSPACE_ROUTES": "Workspace routes",
    "GEOM": "Window geometry",
    "WORKSPACE_PLACEMENT": "Workspace placement",
    "LEFT_EDGE_CORRECTION": "Left edge correction",
}
SECTION_BY_LABEL = {label: section for section, label in SECTION_LABELS.items()}
SECTION_COLUMNS = {
    "EXCLUDE": ("Action", "Machine", "Application"),
    "PIN": ("Action", "Machine", "Application"),
    "WORKSPACE_ROUTES": ("Action", "Machine", "Application", "Workspace"),
    "GEOM": ("Action", "Profile name", "X", "Y", "W", "H"),
    "WORKSPACE_PLACEMENT": ("Action", "Machine", "Application", "Geometry profile"),
    "LEFT_EDGE_CORRECTION": ("Action", "Machine", "Application", "Left edge"),
}
WORKFLOW_HELP = {
    "EXCLUDE": (
        "Exclude\n\n"
        "Use this workflow for windows that d2wc should ignore completely. "
        "Excluded windows skip workspace routing, pinning, geometry, and left-edge correction.\n\n"
        "A machine-only rule affects every application from that machine. "
        "An application-only rule affects that application on every machine. "
        "Using both narrows the match to that application on that machine."
    ),
    "PIN": (
        "Pin\n\n"
        "Use this workflow for windows that should appear on all workspaces. "
        "Pinned windows are made sticky by Devilspie2.\n\n"
        "This is useful for small utility windows, monitors, or panels that should stay visible "
        "while you move between workspaces."
    ),
    "WORKSPACE_ROUTES": (
        "Workspace routes\n\n"
        "Use this workflow to send matching windows to a workspace. "
        "The workspace list is read from X11.\n\n"
        "A route can be broad, such as all windows from a machine, or narrow, such as one "
        "application on one machine."
    ),
    "GEOM": (
        "Window geometry\n\n"
        "Use this workflow to create or edit named geometry profiles. "
        "A profile stores x, y, width, and height values.\n\n"
        "Geometry profiles do not target windows by themselves. They become active when a "
        "workspace placement rule selects the profile."
    ),
    "WORKSPACE_PLACEMENT": (
        "Workspace placement\n\n"
        "Use this workflow to assign a window or group of windows to a named geometry profile. "
        "This is where machine, application, and geometry profile come together.\n\n"
        "If the Machine field shows All, the rule has no machine/domain part and applies to "
        "the selected application across all machines."
    ),
    "LEFT_EDGE_CORRECTION": (
        "Left edge correction\n\n"
        "Use this workflow for windows that do not land exactly on the left edge after "
        "Devilspie2 applies geometry.\n\n"
        "This is a correction layer for edge alignment problems, not a general geometry profile."
    ),
}


@dataclass(frozen=True)
class ManagedSectionEditor:
    """Managed-section editor widget plus callbacks used by the GTK shell."""

    widget: object
    apply: Callable[[], None]
    show_help: Callable[[], None]


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


@dataclass(frozen=True)
class _RuleParts:
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
            existing_profile=_rule_parts(rule).geometry_profile,
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
    event_data: WindowEventData | None = None,
) -> ManagedSectionEditor:
    """Build the section-focused managed editor for the dedicated test config."""

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    main_box.set_margin_top(8)
    main_box.set_margin_bottom(8)
    main_box.set_margin_start(8)
    main_box.set_margin_end(8)
    _install_row_css(Gtk, main_box)

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

    workspace_values = _workspace_values()

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
                _build_section_rows_panel(
                    Gtk,
                    current_snapshot(),
                    section,
                    rows,
                    row_controls,
                    apply_row_action,
                    event_data,
                    workspace_values,
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
            _show_message(Gtk, main_box, "No test config is loaded.")
            return

        try:
            request = _request_from_controls(controls)
        except ValueError as exc:
            _show_message(Gtk, main_box, str(exc))
            return

        result = apply_managed_section_action(snapshot_value.path, request)
        _show_message(Gtk, main_box, format_action_result(result))
        refreshed_snapshot = load_test_config_snapshot(snapshot_value.path)
        state["snapshot"] = refreshed_snapshot
        if result.ok:
            refresh_editor_rows()

    def apply_first_row() -> None:
        row_controls = state["row_controls"]
        if isinstance(row_controls, list) and row_controls:
            apply_row_action(row_controls[0])

    def toggle_mode() -> None:
        state["show_not_configured"] = not bool(state["show_not_configured"])
        mode_button.set_label("Configured" if state["show_not_configured"] else "Not configured")
        refresh_editor_rows()

    def show_help() -> None:
        _show_message(Gtk, main_box, WORKFLOW_HELP[current_section()])

    section_combo.connect("changed", lambda _combo: refresh_editor_rows())
    mode_button.connect("clicked", lambda _button: toggle_mode())
    refresh_editor_rows()

    return ManagedSectionEditor(widget=main_box, apply=apply_first_row, show_help=show_help)


class _EditorControls:
    def __init__(
        self,
        *,
        section: str,
        existing_rule: str,
        action_combo,
        domain_combo,
        class_combo,
        geometry_combo,
        left_edge_combo,
        new_profile_entry,
        workspace_combo,
        x_entry,
        y_entry,
        w_entry,
        h_entry,
    ) -> None:
        self.section = section
        self.existing_rule = existing_rule
        self.action_combo = action_combo
        self.domain_combo = domain_combo
        self.class_combo = class_combo
        self.geometry_combo = geometry_combo
        self.left_edge_combo = left_edge_combo
        self.new_profile_entry = new_profile_entry
        self.workspace_combo = workspace_combo
        self.x_entry = x_entry
        self.y_entry = y_entry
        self.w_entry = w_entry
        self.h_entry = h_entry
        self.apply_button = None
        self.undo_button = None
        self.initial_values: tuple[str, ...] = ()
        self.is_restoring = False


class _SearchableCombo:
    def __init__(self, Gtk, placeholder: str, *, width: int = 28) -> None:
        self.Gtk = Gtk
        self.placeholder = placeholder
        self.values: list[str] = []
        self.active_text = ""
        self.changed_callbacks: list[Callable[[object], None]] = []

        self.widget = Gtk.Button(label=placeholder)
        self.widget.set_hexpand(True)
        self.widget.connect("clicked", lambda _button: self._open_popover())

        self.popover = Gtk.Popover.new(self.widget)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_top(8)
        box.set_margin_bottom(8)
        box.set_margin_start(8)
        box.set_margin_end(8)
        self.popover.add(box)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Filter")
        self.search_entry.set_width_chars(width)
        self.search_entry.connect("changed", lambda _entry: self._refresh_list())
        box.pack_start(self.search_entry, False, False, 0)

        scroller = Gtk.ScrolledWindow()
        scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scroller.set_size_request(280, 180)
        box.pack_start(scroller, True, True, 0)

        self.list_box = Gtk.ListBox()
        self.list_box.connect("row-activated", self._select_row)
        scroller.add(self.list_box)

    def append_text(self, value: str) -> None:
        self.values.append(value)

    def remove_all(self) -> None:
        self.values = []
        self.active_text = ""
        self._update_button_label()
        self._refresh_list()

    def set_active(self, index: int) -> None:
        if 0 <= index < len(self.values):
            self._set_active_text(self.values[index], emit=True)
        else:
            self._set_active_text("", emit=True)

    def set_active_text(self, value: str) -> None:
        if value == "" or value in self.values:
            self._set_active_text(value, emit=True)

    def get_active_text(self) -> str:
        return self.active_text

    def set_placeholder(self, placeholder: str) -> None:
        self.placeholder = placeholder
        self._update_button_label()

    def set_sensitive(self, sensitive: bool) -> None:
        self.widget.set_sensitive(sensitive)

    def set_hexpand(self, expand: bool) -> None:
        self.widget.set_hexpand(expand)

    def connect(self, signal_name: str, callback) -> int:
        if signal_name == "changed":
            self.changed_callbacks.append(callback)
            return len(self.changed_callbacks)
        return self.widget.connect(signal_name, callback)

    def _open_popover(self) -> None:
        self.search_entry.set_text("")
        self._refresh_list()
        self.popover.show_all()
        self.popover.popup()
        self.search_entry.grab_focus()

    def _refresh_list(self) -> None:
        for child in self.list_box.get_children():
            self.list_box.remove(child)

        filter_text = self.search_entry.get_text().strip().lower() if hasattr(self, "search_entry") else ""
        for value in self.values:
            if filter_text and filter_text not in value.lower():
                continue
            row = self.Gtk.ListBoxRow()
            row._d2wc_value = value
            label = self.Gtk.Label(label=value or "(none)")
            label.set_xalign(0)
            label.set_margin_top(4)
            label.set_margin_bottom(4)
            label.set_margin_start(4)
            label.set_margin_end(4)
            row.add(label)
            self.list_box.add(row)
        self.list_box.show_all()

    def _select_row(self, _list_box, row) -> None:
        self._set_active_text(getattr(row, "_d2wc_value", ""), emit=True)
        self.popover.popdown()

    def _set_active_text(self, value: str, *, emit: bool) -> None:
        self.active_text = value
        self._update_button_label()
        if emit:
            for callback in self.changed_callbacks:
                callback(self)

    def _update_button_label(self) -> None:
        self.widget.set_label(self.active_text or self.placeholder)


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


def _build_section_rows_panel(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    section: str,
    rows: tuple[ManagedGridRow, ...],
    row_controls: list[_EditorControls],
    apply_row_action,
    event_data: WindowEventData | None,
    workspace_values: tuple[str, ...],
):
    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    scroller.set_size_request(-1, 260)

    panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    panel.set_hexpand(True)
    panel.set_margin_top(8)
    panel.set_margin_bottom(8)
    panel.set_margin_start(8)
    panel.set_margin_end(8)
    scroller.add(panel)

    columns = SECTION_COLUMNS[section]
    column_size_groups = _column_size_groups(Gtk, len(columns) + 2)
    header = Gtk.Grid()
    header.set_hexpand(True)
    header.set_column_homogeneous(False)
    header.set_column_spacing(8)
    for column_index, column_name in enumerate((*columns, "", "")):
        label = Gtk.Label(label=column_name)
        label.set_xalign(0.5)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_hexpand(_column_expands(column_name))
        if not _column_expands(column_name):
            label.set_width_chars(_column_width_chars(column_name))
        column_size_groups[column_index].add_widget(label)
        header.attach(label, column_index, 0, 1, 1)
    panel.pack_start(header, False, True, 0)

    for row in rows:
        controls = _build_row_controls(Gtk, snapshot, section, row, event_data, workspace_values)
        row_controls.append(controls)
        panel.pack_start(
            _build_action_row(Gtk, columns, controls, apply_row_action, column_size_groups),
            False,
            True,
            0,
        )

    return scroller


def _build_action_row(Gtk, columns: tuple[str, ...], controls: _EditorControls, apply_row_action, column_size_groups):
    row_box = Gtk.EventBox()
    row_box.set_visible_window(True)
    row_box.set_above_child(False)
    row_box.set_hexpand(True)
    _set_action_row_style(row_box, _active_action(controls))

    grid = Gtk.Grid()
    grid.set_hexpand(True)
    grid.set_column_homogeneous(False)
    grid.set_column_spacing(8)
    grid.set_margin_top(6)
    grid.set_margin_bottom(6)
    grid.set_margin_start(6)
    grid.set_margin_end(6)
    row_box.add(grid)

    for column_index, column_name in enumerate(columns):
        widget = _widget_for_column(Gtk, controls, column_name)
        widget.set_hexpand(_column_expands(column_name))
        if not _column_expands(column_name) and hasattr(widget, "set_width_chars"):
            widget.set_width_chars(_column_width_chars(column_name))
        column_size_groups[column_index].add_widget(widget)
        grid.attach(widget, column_index, 0, 1, 1)

    apply_button = Gtk.Button(label="Apply")
    apply_button.set_hexpand(False)
    column_size_groups[len(columns)].add_widget(apply_button)
    apply_button.connect("clicked", lambda _button: apply_row_action(controls))
    grid.attach(apply_button, len(columns), 0, 1, 1)

    undo_button = Gtk.Button(label="Undo")
    undo_button.set_hexpand(False)
    column_size_groups[len(columns) + 1].add_widget(undo_button)
    undo_button.connect("clicked", lambda _button: _restore_initial_values(controls))
    grid.attach(undo_button, len(columns) + 1, 0, 1, 1)

    controls.action_combo.connect("changed", lambda _combo: _set_action_row_style(row_box, _active_action(controls)))
    _initialize_row_state(controls, apply_button, undo_button)
    return row_box


def _build_row_controls(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    section: str,
    row: ManagedGridRow,
    event_data: WindowEventData | None,
    workspace_values: tuple[str, ...],
) -> _EditorControls:
    action_combo = _combo_box(Gtk, EDITOR_ACTIONS)
    domain_combo = _searchable_combo(Gtk, "Machine", width=18)
    class_combo = _searchable_combo(Gtk, "Application", width=22)
    geometry_combo = _searchable_combo(Gtk, "Geometry profile", width=18)
    left_edge_combo = _combo_box(Gtk, tuple(sorted(LEFT_EDGE_MODES)))
    new_profile_entry = _entry(Gtk, "Profile name", width=18)
    workspace_combo = _combo_box(Gtk, workspace_values)
    x_entry = _entry(Gtk, "x", width=5)
    y_entry = _entry(Gtk, "y", width=5)
    w_entry = _entry(Gtk, "w", width=5)
    h_entry = _entry(Gtk, "h", width=5)

    controls = _EditorControls(
        section=section,
        existing_rule=row.existing_entry,
        action_combo=action_combo,
        domain_combo=domain_combo,
        class_combo=class_combo,
        geometry_combo=geometry_combo,
        left_edge_combo=left_edge_combo,
        new_profile_entry=new_profile_entry,
        workspace_combo=workspace_combo,
        x_entry=x_entry,
        y_entry=y_entry,
        w_entry=w_entry,
        h_entry=h_entry,
    )

    _reset_combo(domain_combo, _domain_values(snapshot, event_data), include_blank=True)
    _reset_combo(class_combo, _class_values(snapshot, event_data), include_blank=True)
    _reset_combo(geometry_combo, _profile_names(snapshot), include_blank=True)
    _populate_controls_from_grid_row(controls, row)

    action_combo.connect("changed", lambda _combo: _set_field_sensitivity(section, _active_action(controls), controls))
    geometry_combo.connect("changed", lambda _combo: _populate_geom_fields_from_profile(snapshot, controls))
    _set_field_sensitivity(section, _active_action(controls), controls)
    return controls


def _widget_for_column(Gtk, controls: _EditorControls, column_name: str):
    if column_name == "Action":
        return controls.action_combo
    if column_name == "Machine":
        return controls.domain_combo.widget
    if column_name == "Application":
        return controls.class_combo.widget
    if column_name == "Geometry profile":
        return controls.geometry_combo.widget
    if column_name == "Profile name":
        return controls.new_profile_entry
    if column_name == "Workspace":
        return controls.workspace_combo
    if column_name == "Left edge":
        return controls.left_edge_combo
    if column_name == "X":
        return controls.x_entry
    if column_name == "Y":
        return controls.y_entry
    if column_name == "W":
        return controls.w_entry
    if column_name == "H":
        return controls.h_entry
    return _text_label(Gtk, "")


def _request_from_controls(controls: _EditorControls) -> ManagedSectionActionRequest:
    section = controls.section
    action = _active_action(controls).lower()
    profile_name = controls.new_profile_entry.get_text().strip() or controls.geometry_combo.get_active_text() or ""
    target_rule = _rule_from_controls(controls)

    return ManagedSectionActionRequest(
        section=section,
        operation=action,
        rule=target_rule,
        existing_rule=controls.existing_rule,
        workspace=_optional_int(controls.workspace_combo.get_active_text()),
        profile_name=profile_name,
        x=_optional_int(controls.x_entry.get_text()),
        y=_optional_int(controls.y_entry.get_text()),
        w=_optional_int(controls.w_entry.get_text()),
        h=_optional_int(controls.h_entry.get_text()),
    )


def _rule_from_controls(controls: _EditorControls) -> str:
    section = controls.section
    if section == "GEOM":
        return ""

    parts: list[str] = []
    domain = controls.domain_combo.get_active_text() or ""
    class_name = controls.class_combo.get_active_text() or ""
    if domain:
        parts.append(f"d:{domain}")
    if class_name:
        parts.append(f"c:{class_name}")
    if section == "WORKSPACE_PLACEMENT":
        geometry_profile = controls.geometry_combo.get_active_text() or ""
        if geometry_profile:
            parts.append(f"g:{geometry_profile}")
    if section == "LEFT_EDGE_CORRECTION":
        left_edge_mode = controls.left_edge_combo.get_active_text() or ""
        if left_edge_mode:
            parts.append(f"le:{left_edge_mode}")
    return " ".join(parts)


def _set_field_sensitivity(section: str, action: str, controls: _EditorControls) -> None:
    is_rule_section = section in {"EXCLUDE", "PIN", "WORKSPACE_ROUTES", "WORKSPACE_PLACEMENT", "LEFT_EDGE_CORRECTION"}
    is_geom = section == "GEOM"
    normalized_action = action.lower()
    edits_values = normalized_action in {"add", "modify"}
    needs_workspace = section == "WORKSPACE_ROUTES" and edits_values
    needs_geometry_profile = section == "WORKSPACE_PLACEMENT" and edits_values
    needs_left_edge = section == "LEFT_EDGE_CORRECTION" and edits_values
    edits_geom_values = is_geom and edits_values

    controls.domain_combo.set_sensitive(is_rule_section and edits_values)
    controls.class_combo.set_sensitive(is_rule_section and edits_values)
    controls.workspace_combo.set_sensitive(needs_workspace)
    controls.geometry_combo.set_sensitive(needs_geometry_profile)
    controls.left_edge_combo.set_sensitive(needs_left_edge)
    controls.new_profile_entry.set_sensitive(edits_geom_values)
    for entry in (controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.set_sensitive(edits_geom_values)


def _initialize_row_state(controls: _EditorControls, apply_button, undo_button) -> None:
    controls.apply_button = apply_button
    controls.undo_button = undo_button
    controls.initial_values = _control_values(controls)
    undo_button.set_sensitive(False)
    _set_apply_button_style(apply_button, _active_action(controls), dirty=False)
    _connect_dirty_tracking(controls)


def _connect_dirty_tracking(controls: _EditorControls) -> None:
    callback = lambda _widget: _refresh_row_dirty_state(controls)
    for combo in (
        controls.action_combo,
        controls.domain_combo,
        controls.class_combo,
        controls.geometry_combo,
        controls.left_edge_combo,
        controls.workspace_combo,
    ):
        combo.connect("changed", callback)
    for entry in (controls.new_profile_entry, controls.x_entry, controls.y_entry, controls.w_entry, controls.h_entry):
        entry.connect("changed", callback)


def _refresh_row_dirty_state(controls: _EditorControls) -> None:
    if controls.is_restoring:
        return
    dirty = _control_values(controls) != controls.initial_values
    if controls.undo_button is not None:
        controls.undo_button.set_sensitive(dirty)
    if controls.apply_button is not None:
        _set_apply_button_style(controls.apply_button, _active_action(controls), dirty=dirty)


def _restore_initial_values(controls: _EditorControls) -> None:
    controls.is_restoring = True
    _restore_control_values(controls, controls.initial_values)
    _set_field_sensitivity(controls.section, _active_action(controls), controls)
    controls.is_restoring = False
    _refresh_row_dirty_state(controls)


def _control_values(controls: _EditorControls) -> tuple[str, ...]:
    return (
        controls.action_combo.get_active_text() or "",
        controls.domain_combo.placeholder,
        controls.domain_combo.get_active_text() or "",
        controls.class_combo.placeholder,
        controls.class_combo.get_active_text() or "",
        controls.geometry_combo.placeholder,
        controls.geometry_combo.get_active_text() or "",
        controls.left_edge_combo.get_active_text() or "",
        controls.new_profile_entry.get_text(),
        controls.workspace_combo.get_active_text() or "",
        controls.x_entry.get_text(),
        controls.y_entry.get_text(),
        controls.w_entry.get_text(),
        controls.h_entry.get_text(),
    )


def _restore_control_values(controls: _EditorControls, values: tuple[str, ...]) -> None:
    (
        action,
        domain_placeholder,
        domain,
        class_placeholder,
        class_name,
        geometry_placeholder,
        geometry_profile,
        left_edge_mode,
        profile_name,
        workspace,
        x_value,
        y_value,
        w_value,
        h_value,
    ) = values
    controls.domain_combo.set_placeholder(domain_placeholder)
    controls.class_combo.set_placeholder(class_placeholder)
    controls.geometry_combo.set_placeholder(geometry_placeholder)
    _set_combo_active_text(controls.action_combo, action)
    _set_combo_active_text(controls.domain_combo, domain)
    _set_combo_active_text(controls.class_combo, class_name)
    _set_combo_active_text(controls.geometry_combo, geometry_profile)
    _set_combo_active_text(controls.left_edge_combo, left_edge_mode)
    controls.new_profile_entry.set_text(profile_name)
    _set_combo_active_text(controls.workspace_combo, workspace)
    controls.x_entry.set_text(x_value)
    controls.y_entry.set_text(y_value)
    controls.w_entry.set_text(w_value)
    controls.h_entry.set_text(h_value)


def _populate_geom_fields_from_profile(snapshot: TestConfigSnapshot | None, controls: _EditorControls) -> None:
    if controls.section != "GEOM" or snapshot is None or snapshot.config is None:
        return
    active_profile = controls.geometry_combo.get_active_text() or ""
    for profile in snapshot.config.geom:
        if profile.name == active_profile:
            controls.new_profile_entry.set_text(profile.name)
            controls.x_entry.set_text(str(profile.x))
            controls.y_entry.set_text(str(profile.y))
            controls.w_entry.set_text(str(profile.w))
            controls.h_entry.set_text(str(profile.h))
            return


def _populate_controls_from_grid_row(controls: _EditorControls, row: ManagedGridRow) -> None:
    _set_combo_active_text(controls.action_combo, row.action)

    parts = _rule_parts(row.target_entry or row.existing_entry)
    if parts.domain:
        _set_combo_active_text(controls.domain_combo, parts.domain)
    elif controls.section == "WORKSPACE_PLACEMENT" and parts.class_name:
        controls.domain_combo.set_placeholder("All")
    if parts.class_name:
        _set_combo_active_text(controls.class_combo, parts.class_name)
    if parts.geometry_profile:
        _set_combo_active_text(controls.geometry_combo, parts.geometry_profile)
    if parts.left_edge_mode:
        _set_combo_active_text(controls.left_edge_combo, parts.left_edge_mode)
    if row.existing_profile:
        _set_combo_active_text(controls.geometry_combo, row.existing_profile)
    if row.new_profile:
        controls.new_profile_entry.set_text(row.new_profile)
    if row.workspace:
        _set_combo_active_text(controls.workspace_combo, row.workspace)
    _set_geometry_fields_from_text(controls, row.geometry)


def _domain_values(snapshot: TestConfigSnapshot | None, event_data: WindowEventData | None) -> tuple[str, ...]:
    values = {_rule_parts(row.target_entry or row.existing_entry).domain for row in build_configured_grid_rows(snapshot)}
    event_domain = event_data.display_domain.lower() if event_data and event_data.display_domain else ""
    if event_domain:
        values.add(event_domain)
    values.discard("")
    return tuple(sorted(values))


def _class_values(snapshot: TestConfigSnapshot | None, event_data: WindowEventData | None) -> tuple[str, ...]:
    values = {_rule_parts(row.target_entry or row.existing_entry).class_name for row in build_configured_grid_rows(snapshot)}
    event_class = _class_from_event(event_data)
    if event_class:
        values.add(event_class)
    values.discard("")
    return tuple(sorted(values))


def _profile_names(snapshot: TestConfigSnapshot | None) -> tuple[str, ...]:
    if snapshot is None or snapshot.config is None:
        return ()
    return tuple(profile.name for profile in snapshot.config.geom)


def _workspace_values() -> tuple[str, ...]:
    try:
        result = subprocess.run(
            ["xprop", "-root", "_NET_NUMBER_OF_DESKTOPS"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (OSError, subprocess.SubprocessError):
        return ()

    if result.returncode != 0:
        return ()

    try:
        count = int(result.stdout.rsplit("=", 1)[-1].strip())
    except ValueError:
        return ()

    if count < 1:
        return ()
    return tuple(str(workspace) for workspace in range(1, count + 1))


def _install_row_css(Gtk, widget) -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(ROW_CSS.encode("utf-8"))
    Gtk.StyleContext.add_provider_for_screen(
        widget.get_screen(),
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


def _set_action_row_style(row_box, action: str) -> None:
    style = row_box.get_style_context()
    for css_class in ("d2wc-row-add", "d2wc-row-modify", "d2wc-row-delete"):
        style.remove_class(css_class)
    style.add_class(f"d2wc-row-{action.lower()}")


def _set_apply_button_style(apply_button, action: str, *, dirty: bool) -> None:
    style = apply_button.get_style_context()
    for css_class in (
        "d2wc-apply-add",
        "d2wc-apply-modify",
        "d2wc-apply-delete",
        "d2wc-apply-dirty",
    ):
        style.remove_class(css_class)
    style.add_class("d2wc-apply-dirty" if dirty else f"d2wc-apply-{action.lower()}")


def _column_size_groups(Gtk, count: int):
    return [Gtk.SizeGroup.new(Gtk.SizeGroupMode.HORIZONTAL) for _index in range(count)]


def _column_expands(column_name: str) -> bool:
    return column_name in {"Machine", "Application", "Geometry profile", "Profile name"}


def _column_width_chars(column_name: str) -> int:
    return {
        "Action": 8,
        "Workspace": 8,
        "Left edge": 8,
        "X": 5,
        "Y": 5,
        "W": 5,
        "H": 5,
    }.get(column_name, 8)


def _rule_parts(rule: str) -> _RuleParts:
    if not rule.strip():
        return _RuleParts()
    try:
        parsed = parse_prefixed_rule(rule)
    except RuleParseError:
        return _RuleParts()
    return _RuleParts(
        domain=parsed.domain or "",
        class_name=parsed.class_name or "",
        geometry_profile=parsed.geometry_profile or "",
        left_edge_mode=parsed.left_edge_mode or "",
    )


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


def _show_message(Gtk, parent, text: str) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent.get_toplevel(),
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=text,
    )
    dialog.run()
    dialog.destroy()


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
    if hasattr(combo, "set_active_text"):
        combo.set_active_text(value)
        return

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


def _searchable_combo(Gtk, placeholder: str, *, width: int = 28) -> _SearchableCombo:
    return _SearchableCombo(Gtk, placeholder, width=width)


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


def _optional_int(value: str | None) -> int | None:
    stripped = (value or "").strip()
    if not stripped:
        return None
    return int(stripped)