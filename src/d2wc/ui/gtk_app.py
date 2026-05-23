"""GTK configurator proof for Devilspie2 test config editing."""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, WindowEventData, get_event_fixture
from d2wc.test_config import TestConfigPrepareResult, TestConfigSnapshot
from d2wc.ui.managed_actions import build_managed_section_editor

UI_FONT_POINT_INCREASE = 2


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
        from gi.repository import Gdk, Gtk, Pango
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk, Gdk, Pango


def run_configurator(
    event_data: WindowEventData | None = None,
    config_awareness=None,
    test_config_snapshot: TestConfigSnapshot | None = None,
    prepare_result: TestConfigPrepareResult | None = None,
) -> int:
    """Open the GTK configurator proof window."""

    _event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    Gtk, Gdk, Pango = _import_gtk()
    _apply_ui_font_point_increase(Gtk, Gdk, Pango, UI_FONT_POINT_INCREASE)

    window = Gtk.Window(title="d2wc Configurator")
    window.set_default_size(1280, 720)
    window.set_border_width(18)
    window.connect("destroy", Gtk.main_quit)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    window.add(outer)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    outer.pack_start(scroller, True, True, 0)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    content.set_margin_end(8)
    scroller.add(content)

    managed_sections_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    editor = build_managed_section_editor(
        Gtk,
        test_config_snapshot,
        managed_sections_box,
        _replace_managed_sections,
        _event,
    )

    content.pack_start(editor.widget, True, True, 0)
    content.pack_start(managed_sections_box, False, False, 0)
    _populate_managed_sections(Gtk, managed_sections_box, test_config_snapshot)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    outer.pack_end(button_box, False, False, 0)

    apply_button = Gtk.Button(label="Apply")
    apply_button.set_sensitive(test_config_snapshot is not None and test_config_snapshot.ok)
    apply_button.connect("clicked", lambda _button: editor.apply())
    button_box.pack_start(apply_button, False, False, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    button_box.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


def _apply_ui_font_point_increase(Gtk, Gdk, Pango, point_increase: int) -> None:
    """Increase the GTK theme font size for this application window."""

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
    provider.load_from_data(f"* {{ font-size: {font_size_pt + point_increase}pt; }}".encode("utf-8"))
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def _replace_managed_sections(Gtk, managed_sections_box, snapshot: TestConfigSnapshot | None) -> None:
    for child in managed_sections_box.get_children():
        managed_sections_box.remove(child)
    _populate_managed_sections(Gtk, managed_sections_box, snapshot)
    managed_sections_box.show_all()


def _populate_managed_sections(Gtk, content, snapshot: TestConfigSnapshot | None) -> None:
    if snapshot is None:
        content.pack_start(
            _build_section_frame(Gtk, "Managed sections", "No test config loaded. Use --test-config or --init-test-config."),
            False,
            False,
            0,
        )
        return

    if not snapshot.ok:
        content.pack_start(
            _build_section_frame(Gtk, "Managed sections", "Managed sections are unavailable until the test config is valid."),
            False,
            False,
            0,
        )
        return

    for section in snapshot.sections:
        content.pack_start(
            _build_section_frame(Gtk, section.name, section.display_text),
            False,
            False,
            0,
        )


def _build_section_frame(Gtk, title: str, body: str):
    return _wrap_label_in_frame(Gtk, title, _build_text_label(Gtk, body))


def _wrap_label_in_frame(Gtk, title: str, label):
    frame = Gtk.Frame(label=title)
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
    frame.add(label)
    return frame


def _build_text_label(Gtk, body: str):
    label = Gtk.Label(label=body)
    label.set_xalign(0)
    label.set_yalign(0)
    label.set_selectable(True)
    label.set_line_wrap(True)
    label.set_margin_top(8)
    label.set_margin_bottom(8)
    label.set_margin_start(8)
    label.set_margin_end(8)
    return label


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