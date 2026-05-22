"""Minimal read-only GTK configurator proof for Devilspie2 event data."""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, WindowEventData, get_event_fixture


class GtkConfiguratorImportError(RuntimeError):
    """Raised when GTK/PyGObject cannot be imported."""


def _import_gtk():
    try:
        import gi
    except ImportError as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK/PyGObject is not available. Install the system PyGObject and GTK 3 packages, "
            "then run `python -m d2wc configure` again."
        ) from exc

    try:
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk


def run_configurator(event_data: WindowEventData | None = None) -> int:
    """Open the read-only GTK configurator proof window."""

    event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    Gtk = _import_gtk()

    window = Gtk.Window(title="d2wc Configurator")
    window.set_default_size(640, 460)
    window.set_border_width(18)
    window.connect("destroy", Gtk.main_quit)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    window.add(outer)

    title = Gtk.Label()
    title.set_markup("<b>d2wc Configurator</b>")
    title.set_xalign(0)
    outer.pack_start(title, False, False, 0)

    message = Gtk.Label(
        label=(
            "Devilspie2 event-data UI proof.\n"
            "The values below are read-only and no config files are read or written."
        )
    )
    message.set_xalign(0)
    message.set_line_wrap(True)
    outer.pack_start(message, False, False, 0)

    outer.pack_start(_build_section_frame(Gtk, "Identity", format_event_identity(event)), False, False, 0)
    outer.pack_start(_build_section_frame(Gtk, "Geometry", format_event_geometry(event)), False, False, 0)
    outer.pack_start(
        _build_section_frame(
            Gtk,
            "Configuration options",
            "Rule creation is intentionally disabled in this proof.\n"
            "Later stages can wire this event data into tested GEOM and WORKSPACE_PLACEMENT edits first.",
        ),
        False,
        False,
        0,
    )

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    outer.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


def _build_section_frame(Gtk, title: str, body: str):
    frame = Gtk.Frame(label=title)
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)

    label = Gtk.Label(label=body)
    label.set_xalign(0)
    label.set_yalign(0)
    label.set_selectable(True)
    label.set_line_wrap(True)
    label.set_margin_top(8)
    label.set_margin_bottom(8)
    label.set_margin_start(8)
    label.set_margin_end(8)
    frame.add(label)

    return frame


def format_event_identity(event: WindowEventData) -> str:
    """Format event-provided identity values for the GTK proof window."""

    return "\n".join(
        [
            f"Domain: {_value_or_unknown(event.display_domain)}",
            f"Application name: {_value_or_unknown(event.application_name)}",
            f"Window name: {_value_or_unknown(event.window_name)}",
            f"Window Type: {_value_or_unknown(event.window_type)}",
            f"Class instance name: {_value_or_unknown(event.class_instance_name)}",
            f"Window class: {_value_or_unknown(event.window_class)}",
        ]
    )


def format_event_geometry(event: WindowEventData) -> str:
    """Format event-provided geometry values for the GTK proof window."""

    screen = event.screen_geometry
    window = event.window_geometry

    return "\n".join(
        [
            f"Screen Geometry: x = {_value_or_unknown_float(screen.width)} y = {_value_or_unknown_float(screen.height)}",
            f"Window geometry:  x = {_value_or_unknown_float(window.x)} y = {_value_or_unknown_float(window.y)} w = {_value_or_unknown_float(window.w)} h = {_value_or_unknown_float(window.h)}",
            f"Geometry: x={_value_or_unknown_float(window.x)} y={_value_or_unknown_float(window.y)} w={_value_or_unknown_float(window.w)} h={_value_or_unknown_float(window.h)}",
            f"geometry {_value_or_unknown(window.size_text)}",
        ]
    )


def format_active_window_info(window_info: ActiveWindowInfo) -> str:
    """Format selected-window geometry kept for the completed PR #15 diagnostic proof."""

    if window_info.error:
        parts = [f"Window capture failed:\n{window_info.error}"]
        if window_info.raw_xwininfo_output:
            parts.append("Raw xwininfo -frame output kept for debugging.")
        return "\n\n".join(parts)

    geometry = window_info.geometry

    return "\n".join(
        [
            f"Absolute upper-left X:  {_value_or_unknown_int(geometry.x)}",
            f"Absolute upper-left Y:  {_value_or_unknown_int(geometry.y)}",
            f"Relative upper-left X:  {_value_or_unknown_int(geometry.relative_x)}",
            f"Relative upper-left Y:  {_value_or_unknown_int(geometry.relative_y)}",
            f"Width: {_value_or_unknown_int(geometry.width)}",
            f"Height: {_value_or_unknown_int(geometry.height)}",
            f"Geometry: x={_value_or_unknown_int(geometry.x)} y={_value_or_unknown_int(geometry.y)} w={_value_or_unknown_int(geometry.width)} h={_value_or_unknown_int(geometry.height)}",
            f"geometry {_value_or_unknown(geometry.size_text)}",
        ]
    )


def _value_or_unknown(value: str | None) -> str:
    if value is None:
        return "unknown"
    if value == "":
        return "empty"
    return value


def _value_or_unknown_float(value: float | None) -> str:
    if value is None:
        return "unknown"
    return str(value)


def _value_or_unknown_int(value: int | None) -> str:
    if value is None:
        return "unknown"
    return str(value)
