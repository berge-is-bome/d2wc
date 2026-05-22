"""Minimal GTK configurator proof.

The current UI proof is intentionally read-only. It runs a temporary Devilspie2
probe from dom0, then shows the captured snapshot so the Qubes/XFCE window data
path can be tested before any config-writing workflow is added.
"""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo, capture_selected_window, format_probe_number


class GtkConfiguratorImportError(RuntimeError):
    """Raised when GTK/PyGObject cannot be imported."""


def _import_gtk():
    try:
        import gi
    except ImportError as exc:  # pragma: no cover - depends on host packages
        raise GtkConfiguratorImportError(
            "GTK/PyGObject is not available. Install the system PyGObject and GTK 3 packages, "
            "then run `python -m d2wc configure` again."
        ) from exc

    try:
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gtk
    except (ImportError, ValueError) as exc:  # pragma: no cover - depends on host packages
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk


def run_configurator() -> int:
    """Open the read-only GTK configurator proof window."""

    window_info = capture_selected_window()
    Gtk = _import_gtk()

    window = Gtk.Window(title="d2wc Configurator")
    window.set_default_size(760, 420)
    window.set_border_width(18)
    window.connect("destroy", Gtk.main_quit)

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
    window.add(box)

    title = Gtk.Label()
    title.set_markup("<b>d2wc Configurator</b>")
    title.set_xalign(0)
    box.pack_start(title, False, False, 0)

    message = Gtk.Label(
        label=(
            "Devilspie2 window probe proof only.\n"
            "Open or focus a normal application window while this command is running.\n"
            "No config files are read or written from this window yet."
        )
    )
    message.set_xalign(0)
    message.set_line_wrap(True)
    box.pack_start(message, False, False, 0)

    details = Gtk.Label(label=format_active_window_info(window_info))
    details.set_xalign(0)
    details.set_yalign(0)
    details.set_selectable(True)
    details.set_line_wrap(False)
    box.pack_start(details, True, True, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    box.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


def format_active_window_info(window_info: ActiveWindowInfo) -> str:
    """Format captured Devilspie2 window information for the GTK proof window."""

    if window_info.error:
        parts = [f"Window probe failed:\n{window_info.error}"]
        if window_info.raw_devilspie2_output:
            parts.append("Raw Devilspie2 output:")
            parts.append(window_info.raw_devilspie2_output.rstrip())
        return "\n\n".join(parts)

    screen = window_info.screen_geometry
    geometry = window_info.geometry

    return "\n".join(
        [
            f"Domain: {_value_or_unknown(window_info.normalized_domain)}",
            f"Application name: {_value_or_unknown(window_info.application_name)}",
            f"Window name: {_value_or_unknown(window_info.window_name)}",
            f"Window Type: {_value_or_unknown(window_info.window_type)}",
            f"Class instance name: {_value_or_unknown(window_info.class_instance_name)}",
            f"Window class: {_value_or_unknown(window_info.window_class)}",
            f"Screen Geometry: x = {format_probe_number(screen.x)} y = {format_probe_number(screen.y)}",
            f"Window geometry: x = {format_probe_number(geometry.x)} y = {format_probe_number(geometry.y)} w = {format_probe_number(geometry.width)} h = {format_probe_number(geometry.height)}",
            f"geometry {_value_or_unknown(geometry.size_text)}",
        ]
    )


def _value_or_unknown(value: str | None) -> str:
    if value is None:
        return "unknown"
    if value == "":
        return "empty"
    return value
