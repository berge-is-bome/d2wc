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
    window.set_default_size(760, 560)
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
            "Qubes/dom0 selected-window capture proof only.\n"
            "No config files are read or written from this window yet."
        )
    )
    message.set_xalign(0)
    message.set_line_wrap(True)
    box.pack_start(message, False, False, 0)

    scrolled = Gtk.ScrolledWindow()
    scrolled.set_hexpand(True)
    scrolled.set_vexpand(True)
    box.pack_start(scrolled, True, True, 0)

    details = Gtk.Label(label=format_active_window_info(window_info))
    details.set_xalign(0)
    details.set_yalign(0)
    details.set_selectable(True)
    details.set_line_wrap(False)
    scrolled.add(details)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    box.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


def format_active_window_info(window_info: ActiveWindowInfo) -> str:
    """Format captured window information for the GTK proof window."""

    if window_info.error:
        parts = [f"Window capture failed:\n{window_info.error}"]
        if window_info.raw_xwininfo_output:
            parts.append("Raw xwininfo -frame output:")
            parts.append(window_info.raw_xwininfo_output.rstrip())
        return "\n\n".join(parts)

    geometry = window_info.geometry
    geometry_text = "unknown"
    if None not in (geometry.x, geometry.y, geometry.width, geometry.height):
        geometry_text = f"x={geometry.x} y={geometry.y} w={geometry.width} h={geometry.height}"

    parts = [
        "Parsed summary:",
        f"Window ID: {_value_or_unknown(window_info.window_id)}",
        f"Title: {_value_or_unknown(window_info.title)}",
        f"Class instance: {_value_or_unknown(window_info.wm_class_instance)}",
        f"Class: {_value_or_unknown(window_info.wm_class)}",
        f"Qubes domain: {_value_or_unknown(window_info.domain)}",
        f"Geometry: {geometry_text}",
    ]

    if window_info.raw_xwininfo_output:
        parts.extend(
            [
                "",
                "Raw xwininfo -frame output:",
                window_info.raw_xwininfo_output.rstrip(),
            ]
        )

    if window_info.raw_xprop_output:
        parts.extend(
            [
                "",
                "Raw xprop output for selected window id:",
                window_info.raw_xprop_output.rstrip(),
            ]
        )

    return "\n".join(parts)


def _value_or_unknown(value: str | None) -> str:
    if value is None:
        return "unknown"
    if value == "":
        return "empty"
    return value
