"""GTK configurator proof for Devilspie2 event data and test config display."""

from __future__ import annotations

from d2wc.desktop.active_window import ActiveWindowInfo
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, WindowEventData, get_event_fixture
from d2wc.event_preview import (
    EventConfigAwareness,
    build_event_rule_preview,
    format_event_config_awareness,
    format_event_rule_preview,
    proposal_clipboard_text,
)
from d2wc.test_config import (
    TestConfigPrepareResult,
    TestConfigSnapshot,
    format_prepare_result,
    format_test_config_status,
)


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
        from gi.repository import Gtk, Gdk
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk, Gdk


def run_configurator(
    event_data: WindowEventData | None = None,
    config_awareness: EventConfigAwareness | None = None,
    test_config_snapshot: TestConfigSnapshot | None = None,
    prepare_result: TestConfigPrepareResult | None = None,
) -> int:
    """Open the GTK configurator proof window."""

    event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    preview = build_event_rule_preview(event)
    clipboard_text = proposal_clipboard_text(preview, config_awareness)
    Gtk, Gdk = _import_gtk()

    window = Gtk.Window(title="d2wc Configurator")
    window.set_default_size(900, 620)
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
            "Devilspie2 event-data and test-config UI proof.\n"
            "The event values and managed-section display are safe UI development surfaces."
        )
    )
    message.set_xalign(0)
    message.set_line_wrap(True)
    outer.pack_start(message, False, False, 0)

    scroller = Gtk.ScrolledWindow()
    scroller.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    scroller.set_hexpand(True)
    scroller.set_vexpand(True)
    outer.pack_start(scroller, True, True, 0)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    content.set_margin_end(8)
    scroller.add(content)

    content.pack_start(_build_section_frame(Gtk, "Identity", format_event_identity(event)), False, False, 0)
    content.pack_start(_build_section_frame(Gtk, "Geometry", format_event_geometry(event)), False, False, 0)
    content.pack_start(_build_section_frame(Gtk, "Read-only proposal", format_event_rule_preview(preview)), False, False, 0)
    content.pack_start(
        _build_section_frame(Gtk, "Existing config status", format_event_config_awareness(config_awareness)),
        False,
        False,
        0,
    )
    content.pack_start(
        _build_section_frame(Gtk, "Test config status", format_test_config_status(test_config_snapshot)),
        False,
        False,
        0,
    )
    content.pack_start(
        _build_section_frame(Gtk, "Test config prepare result", format_prepare_result(prepare_result)),
        False,
        False,
        0,
    )
    _pack_managed_sections(Gtk, content, test_config_snapshot)
    content.pack_start(
        _build_section_frame(
            Gtk,
            "Configuration options",
            "This UI branch may prepare or replace only ~/.config/devilspie2/d2wc-test.lua.\n"
            "The real user config remains out of scope for automatic writes.",
        ),
        False,
        False,
        0,
    )

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    outer.pack_end(button_box, False, False, 0)

    copy_button = Gtk.Button(label="Copy proposal")
    copy_button.connect("clicked", lambda _button: _copy_text_to_clipboard(Gtk, Gdk, clipboard_text))
    button_box.pack_start(copy_button, False, False, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    button_box.pack_end(close_button, False, False, 0)

    window.show_all()
    Gtk.main()
    return 0


def _pack_managed_sections(Gtk, content, snapshot: TestConfigSnapshot | None) -> None:
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


def _copy_text_to_clipboard(Gtk, Gdk, text: str) -> None:
    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(text, -1)
    clipboard.store()


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
