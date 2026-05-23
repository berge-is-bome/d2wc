"""GTK widgets for editing managed sections in the dedicated test config."""

from __future__ import annotations

from d2wc.test_config import TestConfigSnapshot, format_action_result, format_test_config_status, load_test_config_snapshot
from d2wc.test_config_actions import MANAGED_ACTION_OPERATIONS, MANAGED_ACTION_SECTIONS, ManagedSectionActionRequest, apply_managed_section_action


def build_managed_section_form(Gtk, snapshot: TestConfigSnapshot | None, action_label, status_label, sections_box, refresh_sections):
    """Build a compact add/remove form for all managed sections."""

    frame = Gtk.Frame(label="Managed section edit")
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
    operation_combo = _combo_box(Gtk, MANAGED_ACTION_OPERATIONS)
    rule_entry = _entry(Gtk, "Rule, e.g. d:work c:example")
    profile_entry = _entry(Gtk, "GEOM profile name")
    workspace_entry = _entry(Gtk, "Workspace number")
    x_entry = _entry(Gtk, "x", width=6)
    y_entry = _entry(Gtk, "y", width=6)
    w_entry = _entry(Gtk, "w", width=6)
    h_entry = _entry(Gtk, "h", width=6)

    _grid_attach_labeled(Gtk, grid, 0, "Section", section_combo)
    _grid_attach_labeled(Gtk, grid, 1, "Operation", operation_combo)
    _grid_attach_labeled(Gtk, grid, 2, "Rule", rule_entry)
    _grid_attach_labeled(Gtk, grid, 3, "Profile", profile_entry)
    _grid_attach_labeled(Gtk, grid, 4, "Workspace", workspace_entry)
    _grid_attach_labeled(Gtk, grid, 5, "Geometry", _geometry_box(Gtk, x_entry, y_entry, w_entry, h_entry))

    hint = Gtk.Label(
        label=(
            "Use Rule for EXCLUDE, PIN, WORKSPACE_ROUTES, WORKSPACE_PLACEMENT, and LEFT_EDGE_CORRECTION.\n"
            "Use Profile plus x/y/w/h for GEOM add. Use Profile only for GEOM remove."
        )
    )
    hint.set_xalign(0)
    hint.set_line_wrap(True)
    grid.attach(hint, 0, 6, 2, 1)

    apply_button = Gtk.Button(label="Apply managed-section edit")
    apply_button.set_sensitive(snapshot is not None and snapshot.ok)
    apply_button.connect(
        "clicked",
        lambda _button: _run_form_action(
            Gtk,
            snapshot,
            section_combo,
            operation_combo,
            rule_entry,
            profile_entry,
            workspace_entry,
            x_entry,
            y_entry,
            w_entry,
            h_entry,
            action_label,
            status_label,
            sections_box,
            refresh_sections,
        ),
    )
    grid.attach(apply_button, 0, 7, 2, 1)

    return frame


def _run_form_action(
    Gtk,
    snapshot: TestConfigSnapshot | None,
    section_combo,
    operation_combo,
    rule_entry,
    profile_entry,
    workspace_entry,
    x_entry,
    y_entry,
    w_entry,
    h_entry,
    action_label,
    status_label,
    sections_box,
    refresh_sections,
) -> None:
    if snapshot is None:
        action_label.set_text("Action: managed section edit\nStatus: error\nNo test config is loaded.")
        return

    try:
        request = ManagedSectionActionRequest(
            section=section_combo.get_active_text() or "",
            operation=operation_combo.get_active_text() or "",
            rule=rule_entry.get_text(),
            profile_name=profile_entry.get_text(),
            workspace=_optional_int(workspace_entry.get_text()),
            x=_optional_int(x_entry.get_text()),
            y=_optional_int(y_entry.get_text()),
            w=_optional_int(w_entry.get_text()),
            h=_optional_int(h_entry.get_text()),
        )
    except ValueError as exc:
        action_label.set_text(f"Action: managed section edit\nStatus: error\n{exc}")
        return

    result = apply_managed_section_action(snapshot.path, request)
    action_label.set_text(format_action_result(result))
    refreshed_snapshot = load_test_config_snapshot(snapshot.path)
    status_label.set_text(format_test_config_status(refreshed_snapshot))
    refresh_sections(Gtk, sections_box, refreshed_snapshot)


def _combo_box(Gtk, values: tuple[str, ...]):
    combo = Gtk.ComboBoxText()
    for value in values:
        combo.append_text(value)
    combo.set_active(0)
    return combo


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
