"""Minimal GTK configurator proof.

The current UI proof is intentionally read-only. It prompts for a selected X11
window from dom0, then shows the captured snapshot so the Qubes/XFCE launch and
window identity path can be tested before any config-writing workflow is added.
"""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo, capture_selected_window


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
    window.set_default_size(520, 260)
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
            "Qubes/dom0 selected-window geometry proof only.\n"
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
    """Format captured window geometry for the GTK proof window."""

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
            f"Width: { _value_or_unknown_int(geometry.width)}",
            f"Height: { _value_or_unknown_int(geometry.height)}",
            f"geometry {_value_or_unknown(geometry.size_text)}",
        ]
    )


def _value_or_unknown(value: str | None) -> str:
    if value is None:
        return "unknown"
    if value == "":
        return "empty"
    return value


def _value_or_unknown_int(value: int | None) -> str:
    if value is None:
        return "unknown"
    return str(value)
