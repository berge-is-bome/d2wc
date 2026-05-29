"""GTK widgets for editing managed sections in a d2wc managed config."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Callable

from d2wc.core.rule_grammar import LEFT_EDGE_MODES
from d2wc.event_data import WindowEventData
from d2wc.event_inventory import KnownWindowTarget, merge_known_window_targets
from d2wc.event_inventory_capture import stream_known_window_inventory
from d2wc.managed_config_file import (
    ManagedConfigSnapshot,
    format_managed_action_result,
    load_managed_config_snapshot,
)
from d2wc.test_config_actions import MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action
from d2wc.ui.grid_rows import (
    ManagedGridRow,
    build_configured_grid_rows,
    class_values,
    domain_values,
    profile_names,
    rule_parts,
)

EDITOR_ACTIONS = ("Add", "Modify", "Delete")
SUCCESS_TOAST_MESSAGE = "Operation completed successfully."
FALLBACK_WORKSPACES = ("1",)
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
button.d2wc-row-action-button,
.d2wc-row-action-button {
  min-width: 0;
  min-height: 0;
  padding-left: 4px;
  padding-right: 4px;
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
    stop: Callable[[], None]



def build_managed_section_editor(
    Gtk,
    snapshot: ManagedConfigSnapshot | None,
    event_data: WindowEventData | None = None,
    inventory_targets: tuple[KnownWindowTarget, ...] = (),
    *,
    GLib=None,
    inventory_stream=stream_known_window_inventory,
    toast_settings=lambda: (5, 0.5),
) -> ManagedSectionEditor:
    """Build the section-focused editor for a d2wc managed config."""

    main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
    main_box.set_margin_top(8)
    main_box.set_margin_bottom(8)
    main_box.set_margin_start(8)
    main_box.set_margin_end(8)
    _install_row_css(Gtk, main_box)

    state: dict[str, object] = {
        "snapshot": snapshot,
        "row_controls": [],
        "inventory_targets": inventory_targets,
    }

    top_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    main_box.pack_start(top_bar, False, False, 0)

    section_combo = _section_combo(Gtk)
    top_bar.pack_start(section_combo, False, False, 0)

    rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
    main_box.pack_start(rows_box, True, True, 0)

    workspace_values = _workspace_values()

    def current_snapshot() -> ManagedConfigSnapshot | None:
        return state["snapshot"] if isinstance(state["snapshot"], ManagedConfigSnapshot) else None

    def current_section() -> str:
        return _section_from_combo(section_combo)

    def refresh_editor_rows() -> None:
        for child in rows_box.get_children():
            rows_box.remove(child)
        row_controls: list[_EditorControls] = []
        state["row_controls"] = row_controls

        section = current_section()
        current_inventory_targets = state["inventory_targets"]
        if not isinstance(current_inventory_targets, tuple):
            current_inventory_targets = ()
        rows = _rows_for_section(current_snapshot(), current_inventory_targets, section)
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
                    current_inventory_targets,
                    workspace_values,
                ),
                True,
                True,
                0,
            )
        else:
            rows_box.pack_start(_text_label(Gtk, "No entries are available for this section."), False, False, 0)

        rows_box.show_all()

    def apply_row_action(controls: _EditorControls) -> None:
        snapshot_value = current_snapshot()
        if snapshot_value is None:
            _show_message(Gtk, main_box, "No managed config is loaded.")
            return

        try:
            request = _request_from_controls(controls)
        except ValueError as exc:
            _show_message(Gtk, main_box, str(exc))
            return

        result = apply_managed_section_action(snapshot_value.path, request)
        result_text = format_managed_action_result(result)
        if result.ok:
            timeout_seconds, opacity = toast_settings()
            _show_toast(
                Gtk,
                main_box,
                SUCCESS_TOAST_MESSAGE,
                timeout_seconds=timeout_seconds,
                opacity=opacity,
            )
        else:
            _show_message(Gtk, main_box, result_text)
        refreshed_snapshot = load_managed_config_snapshot(snapshot_value.path)
        state["snapshot"] = refreshed_snapshot
        if result.ok:
            refresh_editor_rows()

    def apply_first_row() -> None:
        row_controls = state["row_controls"]
        if isinstance(row_controls, list) and row_controls:
            apply_row_action(row_controls[0])

    def show_help() -> None:
        _show_message(Gtk, main_box, WORKFLOW_HELP[current_section()])

    inventory_stop_event = threading.Event()

    def merge_inventory_targets(targets: tuple[KnownWindowTarget, ...]) -> bool:
        if inventory_stop_event.is_set():
            return False
        current_inventory_targets = state["inventory_targets"]
        if not isinstance(current_inventory_targets, tuple):
            current_inventory_targets = ()
        merged_targets = merge_known_window_targets(current_inventory_targets, targets)
        if merged_targets == current_inventory_targets:
            return False
        state["inventory_targets"] = merged_targets

        row_controls = state["row_controls"]
        if isinstance(row_controls, list) and any(
            isinstance(control, _EditorControls) and control.is_dirty for control in row_controls
        ):
            return False

        refresh_editor_rows()
        return False

    def show_inventory_error(message: str) -> bool:
        if not inventory_stop_event.is_set():
            _show_message(Gtk, main_box, f"Inventory monitor failed:\n{message}")
        return False

    def monitor_inventory() -> None:
        try:
            for event in inventory_stream(stop_event=inventory_stop_event):
                if inventory_stop_event.is_set():
                    break
                if event.targets and GLib is not None:
                    GLib.idle_add(merge_inventory_targets, event.targets)
        except Exception as exc:  # pragma: no cover - exercised manually with real Devilspie2
            if GLib is not None:
                GLib.idle_add(show_inventory_error, str(exc))

    monitor_thread: threading.Thread | None = None
    if GLib is not None and inventory_stream is not None:
        monitor_thread = threading.Thread(
            target=monitor_inventory,
            name="d2wc-known-window-inventory",
            daemon=True,
        )
        monitor_thread.start()

    def stop_inventory_monitor() -> None:
        inventory_stop_event.set()
        if monitor_thread is not None and monitor_thread.is_alive():
            monitor_thread.join(timeout=1.0)

    section_combo.connect("changed", lambda _combo: refresh_editor_rows())
    refresh_editor_rows()

    return ManagedSectionEditor(
        widget=main_box,
        apply=apply_first_row,
        show_help=show_help,
        stop=stop_inventory_monitor,
    )


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
        self.is_dirty = False


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
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        self.popover.add(box)

        self.entry = Gtk.SearchEntry()
        self.entry.set_width_chars(width)
        box.pack_start(self.entry, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        box.pack_start(self.listbox, True, True, 0)

        self.entry.connect("search-changed", lambda _entry: self._refresh_list())
        self.entry.connect("activate", lambda _entry: self._choose_first_visible())
        self.listbox.connect("row-activated", self._activate_row)

    def set_values(self, values) -> None:
        self.values = sorted({str(value) for value in values if str(value)})
        self._refresh_list()

    def set_active_text(self, value: str) -> None:
        self.active_text = value or ""
        self.widget.set_label(self.active_text or self.placeholder)

    def get_active_text(self) -> str:
        return self.active_text

    def connect_changed(self, callback: Callable[[object], None]) -> None:
        self.changed_callbacks.append(callback)

    def set_hexpand(self, value: bool) -> None:
        self.widget.set_hexpand(value)

    def set_sensitive(self, value: bool) -> None:
        self.widget.set_sensitive(value)

    def _open_popover(self) -> None:
        self.entry.set_text("")
        self._refresh_list()
        self.popover.show_all()
        self.popover.popup()
        self.entry.grab_focus()

    def _refresh_list(self) -> None:
        query = self.entry.get_text().lower() if hasattr(self.entry, "get_text") else ""
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for value in self.values:
            if query and query not in value.lower():
                continue
            row = self.Gtk.ListBoxRow()
            label = self.Gtk.Label(label=value)
            label.set_xalign(0)
            row.add(label)
            row.d2wc_value = value
            self.listbox.add(row)
        self.listbox.show_all()

    def _choose_first_visible(self) -> None:
        rows = self.listbox.get_children()
        if rows:
            self._activate_row(self.listbox, rows[0])

    def _activate_row(self, _listbox, row) -> None:
        value = getattr(row, "d2wc_value", "")
        self.set_active_text(value)
        self.popover.popdown()
        for callback in self.changed_callbacks:
            callback(self)

# The remainder of this module is unchanged.
