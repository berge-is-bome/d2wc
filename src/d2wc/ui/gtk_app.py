"""Minimal GTK configurator proof.

This first UI proof is intentionally read-only. It exists only to prove that the
source-checkout command path can open and close a GTK window on the target
Qubes/XFCE desktop before any active-window capture or rule editing workflow is
added.
"""

from __future__ import annotations


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
    """Open the first read-only GTK configurator proof window."""

    Gtk = _import_gtk()

    window = Gtk.Window(title="d2wc Configurator")
    window.set_default_size(420, 160)
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
            "GTK launch proof only.\n"
            "No config files are read or written from this window yet."
        )
    )
    message.set_xalign(0)
    message.set_line_wrap(True)
    box.pack_start(message, False, False, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    box.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0
