"""GTK configurator proof for Devilspie2 test config editing."""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, WindowEventData, get_event_fixture
from d2wc.test_config import TestConfigPrepareResult, TestConfigSnapshot
from d2wc.ui.managed_actions import build_managed_section_editor

CONFIGURATOR_WINDOW_CLASS = "d2wc-configurator"
UI_FONT_POINT_INCREASE = 2
TOAST_OPACITY = 0.5


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
        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk, GLib, Gtk, Pango
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk, Gdk, GLib, Pango


def run_configurator(
    event_data: WindowEventData | None = None,
    config_awareness=None,
    test_config_snapshot: TestConfigSnapshot | None = None,
    prepare_result: TestConfigPrepareResult | None = None,
) -> int:
    """Open the GTK configurator proof window."""

    _event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    Gtk, Gdk, GLib, Pango = _import_gtk()
    _set_configurator_window_class(Gdk, GLib)
    _apply_ui_css(Gtk, Gdk, Pango, UI_FONT_POINT_INCREASE)

    window = Gtk.Window(title="d2wc Configurator")
    window.set_wmclass(CONFIGURATOR_WINDOW_CLASS, CONFIGURATOR_WINDOW_CLASS)
    window.set_default_size(1280, 720)
    window.set_border_width(18)
    def handle_destroy(_window) -> None:
        editor.stop()
        Gtk.main_quit()

    window.connect("destroy", handle_destroy)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    window.add(outer)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    content.set_hexpand(True)
    content.set_vexpand(True)
    outer.pack_start(content, True, True, 0)

    editor = build_managed_section_editor(Gtk, test_config_snapshot, _event, GLib=GLib)
    content.pack_start(editor.widget, True, True, 0)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    outer.pack_end(button_box, False, False, 0)

    menu_button = Gtk.MenuButton(label="Menu")
    menu = Gtk.Menu()
    help_item = Gtk.MenuItem(label="Help")
    help_item.connect("activate", lambda _item: editor.show_help())
    menu.append(help_item)
    menu.show_all()
    menu_button.set_popup(menu)
    button_box.pack_start(menu_button, False, False, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    button_box.pack_end(close_button, False, False, 0)

    def handle_key_press(_window, event) -> bool:
        if event.keyval == Gdk.KEY_F1:
            editor.show_help()
            return True
        return False

    window.connect("key-press-event", handle_key_press)
    window.show_all()
    Gtk.main()
    return 0


def _set_configurator_window_class(Gdk, GLib) -> None:
    """Publish a stable X11/WM class for Devilspie2 matching."""

    GLib.set_prgname(CONFIGURATOR_WINDOW_CLASS)
    Gdk.set_program_class(CONFIGURATOR_WINDOW_CLASS)


def _apply_ui_css(Gtk, Gdk, Pango, point_increase: int) -> None:
    """Apply application-scoped GTK CSS tweaks."""

    settings = Gtk.Settings.get_default()
    if settings is None:
        return

    font_name = settings.get_property("gtk-font-name") or ""
    font_description = Pango.FontDescription(font_name)
    theme_font_size = font_description.get_size()
    if theme_font_size <= 0:
        return

    font_size_pt = int(round(theme_font_size / Pango.SCALE))
    provider = Gtk.CssProvider()
    provider.load_from_data(
        (
            f"* {{ font-size: {font_size_pt + point_increase}pt; }}\n"
            f"infobar {{ opacity: {TOAST_OPACITY}; padding: 2px; }}\n"
            "infobar label { padding: 2px 6px; }\n"
        ).encode("utf-8")
    )
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
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


def _value_or_unknown_int(value: int | None) -> str:
    if value is None:
        return "unknown"
    return str(value)