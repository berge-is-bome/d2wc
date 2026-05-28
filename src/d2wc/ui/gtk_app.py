"""GTK configurator proof for Devilspie2 managed config editing."""

from __future__ import annotations

from pathlib import Path

from d2wc.core.user_paths import default_managed_config_dir
from d2wc.desktop.active_window import ActiveWindowInfo
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, WindowEventData, get_event_fixture
from d2wc.managed_config_file import (
    activate_managed_config,
    load_managed_config_snapshot,
    managed_config_status_text,
    save_managed_config_as,
)
from d2wc.test_config import TestConfigPrepareResult, TestConfigSnapshot
from d2wc.ui.managed_actions import build_managed_section_editor
from d2wc.ui_settings import UiSettings, load_ui_settings, save_ui_settings

CONFIGURATOR_WINDOW_CLASS = "d2wc-configurator"
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
        from gi.repository import Gdk, Gio, GLib, Gtk, Pango
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk, Gdk, Gio, GLib, Pango


def run_configurator(
    event_data: WindowEventData | None = None,
    config_awareness=None,
    test_config_snapshot: TestConfigSnapshot | None = None,
    prepare_result: TestConfigPrepareResult | None = None,
) -> int:
    """Open the GTK configurator proof window."""

    _event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    ui_settings = load_ui_settings()
    Gtk, Gdk, Gio, GLib, Pango = _import_gtk()
    _set_configurator_window_class(Gdk, GLib)
    _apply_ui_css(Gtk, Gdk, Pango, UI_FONT_POINT_INCREASE)

    window = Gtk.Window(title="d2wc Configurator")
    window.set_wmclass(CONFIGURATOR_WINDOW_CLASS, CONFIGURATOR_WINDOW_CLASS)
    window.set_default_size(1280, 720)
    window.set_border_width(18)

    outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    window.add(outer)

    content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
    content.set_hexpand(True)
    content.set_vexpand(True)
    outer.pack_start(content, True, True, 0)

    state: dict[str, object] = {
        "snapshot": test_config_snapshot,
        "editor": None,
        "toast_timeout_seconds": ui_settings.toast_timeout_seconds,
        "toast_opacity": ui_settings.toast_opacity,
        "config_monitor": None,
        "config_monitor_path": None,
        "config_monitor_reload_source": None,
    }

    def current_snapshot() -> TestConfigSnapshot | None:
        snapshot = state.get("snapshot")
        return snapshot if isinstance(snapshot, TestConfigSnapshot) else None

    def current_toast_settings() -> tuple[int, float]:
        timeout = state.get("toast_timeout_seconds", ui_settings.toast_timeout_seconds)
        opacity = state.get("toast_opacity", ui_settings.toast_opacity)
        return int(timeout), float(opacity)

    def update_window_state() -> None:
        snapshot = current_snapshot()
        if snapshot is not None:
            window.set_title(f"d2wc Configurator - {snapshot.path.name}")
        else:
            window.set_title("d2wc Configurator")

    def stop_config_monitor() -> None:
        source_id = state.get("config_monitor_reload_source")
        if isinstance(source_id, int):
            GLib.source_remove(source_id)
        state["config_monitor_reload_source"] = None

        monitor = state.get("config_monitor")
        if monitor is not None and hasattr(monitor, "cancel"):
            monitor.cancel()
        state["config_monitor"] = None
        state["config_monitor_path"] = None

    def reload_changed_config(path: Path) -> bool:
        state["config_monitor_reload_source"] = None
        current = current_snapshot()
        if current is None or current.path != path:
            return False

        refreshed = load_managed_config_snapshot(path)
        rebuild_editor(refreshed)
        timeout_seconds, opacity = current_toast_settings()
        if refreshed.ok:
            _show_toast(
                Gtk,
                outer,
                "Reloaded managed config after file change.",
                timeout_seconds=timeout_seconds,
                opacity=opacity,
            )
        else:
            _show_message(
                Gtk,
                window,
                "The managed config changed on disk but could not be reloaded. "
                "No changes were written. Fix the file before applying more edits.\n\n"
                f"{managed_config_status_text(refreshed)}",
            )
        return False

    def schedule_config_reload(path: Path, event_type) -> None:
        if not _is_managed_config_reload_event(event_type):
            return
        if state.get("config_monitor_path") != path:
            return
        source_id = state.get("config_monitor_reload_source")
        if isinstance(source_id, int):
            GLib.source_remove(source_id)
        state["config_monitor_reload_source"] = GLib.timeout_add(250, reload_changed_config, path)

    def start_config_monitor(snapshot: TestConfigSnapshot | None) -> None:
        if snapshot is None or not snapshot.path:
            stop_config_monitor()
            return
        path = snapshot.path
        if state.get("config_monitor_path") == path and state.get("config_monitor") is not None:
            return

        stop_config_monitor()
        try:
            monitor = Gio.File.new_for_path(str(path)).monitor_file(Gio.FileMonitorFlags.NONE, None)
        except (GLib.Error, OSError) as exc:
            _show_message(Gtk, window, f"Could not monitor managed config for changes:\n{path}\n\n{exc}")
            return

        monitor.connect("changed", lambda _monitor, _file, _other_file, event_type: schedule_config_reload(path, event_type))
        state["config_monitor"] = monitor
        state["config_monitor_path"] = path

    def rebuild_editor(snapshot: TestConfigSnapshot | None) -> None:
        old_editor = state.get("editor")
        if old_editor is not None and hasattr(old_editor, "stop"):
            old_editor.stop()
        for child in content.get_children():
            content.remove(child)
        editor = build_managed_section_editor(Gtk, snapshot, _event, GLib=GLib, toast_settings=current_toast_settings)
        state["snapshot"] = snapshot
        state["editor"] = editor
        content.pack_start(editor.widget, True, True, 0)
        content.show_all()
        update_window_state()
        start_config_monitor(snapshot)

    def open_managed_file(_item=None) -> None:
        managed_dir = default_managed_config_dir()
        managed_dir.mkdir(parents=True, exist_ok=True)
        chooser = Gtk.FileChooserDialog(
            title="Open d2wc managed Lua file",
            parent=window,
            action=Gtk.FileChooserAction.OPEN,
        )
        chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        chooser.set_current_folder(str(managed_dir))
        _add_lua_filter(Gtk, chooser)
        try:
            response = chooser.run()
            if response != Gtk.ResponseType.OK:
                return
            selected = Path(chooser.get_filename())
        finally:
            chooser.destroy()

        if not _is_under_managed_dir(selected, managed_dir):
            _show_message(Gtk, window, f"Managed files must be opened from {managed_dir}")
            return
        snapshot = load_managed_config_snapshot(selected)
        if not snapshot.ok:
            _show_message(Gtk, window, managed_config_status_text(snapshot))
            return
        activation = activate_managed_config(selected)
        rebuild_editor(snapshot)
        if not activation.ok:
            _show_message(Gtk, window, activation.message)

    def save_managed_file_as(_item=None) -> None:
        snapshot = current_snapshot()
        if snapshot is None or not snapshot.exists:
            _show_message(Gtk, window, "No managed config is loaded.")
            return

        managed_dir = default_managed_config_dir()
        managed_dir.mkdir(parents=True, exist_ok=True)
        chooser = Gtk.FileChooserDialog(
            title="Save d2wc managed Lua file as",
            parent=window,
            action=Gtk.FileChooserAction.SAVE,
        )
        chooser.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK)
        chooser.set_do_overwrite_confirmation(True)
        chooser.set_current_folder(str(managed_dir))
        chooser.set_current_name(snapshot.path.name)
        _add_lua_filter(Gtk, chooser)
        try:
            response = chooser.run()
            if response != Gtk.ResponseType.OK:
                return
            target = Path(chooser.get_filename())
        finally:
            chooser.destroy()

        if not _is_under_managed_dir(target, managed_dir):
            _show_message(Gtk, window, f"Managed files must be saved under {managed_dir}")
            return
        result = save_managed_config_as(snapshot.path, target, replace=target.exists())
        if not result.ok or result.path is None:
            _show_message(Gtk, window, result.message)
            return
        refreshed = load_managed_config_snapshot(result.path)
        if not refreshed.ok:
            _show_message(Gtk, window, managed_config_status_text(refreshed))
            return
        activation = activate_managed_config(result.path)
        rebuild_editor(refreshed)
        timeout_seconds, opacity = current_toast_settings()
        if activation.ok:
            _show_toast(Gtk, outer, result.message, timeout_seconds=timeout_seconds, opacity=opacity)
        else:
            _show_message(Gtk, window, f"{result.message}\n\n{activation.message}")

    def configure_toasts(_item=None) -> None:
        timeout_seconds, opacity = current_toast_settings()
        dialog = Gtk.Dialog(title="Configure", transient_for=window, flags=0)
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK)
        dialog.set_default_response(Gtk.ResponseType.OK)

        box = dialog.get_content_area()
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_margin_top(12)
        grid.set_margin_bottom(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        box.add(grid)

        timeout_label = Gtk.Label(label="Toast timeout seconds")
        timeout_label.set_xalign(0)
        timeout_adjustment = Gtk.Adjustment(value=timeout_seconds, lower=1, upper=60, step_increment=1, page_increment=5)
        timeout_spin = Gtk.SpinButton(adjustment=timeout_adjustment, climb_rate=1, digits=0)
        timeout_spin.set_numeric(True)

        opacity_label = Gtk.Label(label="Toast opacity")
        opacity_label.set_xalign(0)
        opacity_adjustment = Gtk.Adjustment(value=opacity, lower=0.1, upper=1.0, step_increment=0.05, page_increment=0.1)
        opacity_spin = Gtk.SpinButton(adjustment=opacity_adjustment, climb_rate=0.05, digits=2)
        opacity_spin.set_numeric(True)

        grid.attach(timeout_label, 0, 0, 1, 1)
        grid.attach(timeout_spin, 1, 0, 1, 1)
        grid.attach(opacity_label, 0, 1, 1, 1)
        grid.attach(opacity_spin, 1, 1, 1, 1)
        dialog.show_all()

        try:
            response = dialog.run()
            if response != Gtk.ResponseType.OK:
                return
            state["toast_timeout_seconds"] = int(timeout_spin.get_value_as_int())
            state["toast_opacity"] = float(opacity_spin.get_value())
            save_ui_settings(
                UiSettings(
                    toast_timeout_seconds=int(timeout_spin.get_value_as_int()),
                    toast_opacity=float(opacity_spin.get_value()),
                )
            )
        finally:
            dialog.destroy()

        timeout_seconds, opacity = current_toast_settings()
        _show_toast(
            Gtk,
            outer,
            f"Toast settings updated: {timeout_seconds}s, opacity {opacity:.2f}",
            timeout_seconds=timeout_seconds,
            opacity=opacity,
        )

    def handle_destroy(_window) -> None:
        editor = state.get("editor")
        if editor is not None and hasattr(editor, "stop"):
            editor.stop()
        Gtk.main_quit()

    window.connect("destroy", handle_destroy)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
    outer.pack_end(button_box, False, False, 0)

    menu_button = Gtk.MenuButton(label="Menu")
    menu = Gtk.Menu()
    open_item = Gtk.MenuItem(label="File Open")
    open_item.connect("activate", open_managed_file)
    menu.append(open_item)
    save_as_item = Gtk.MenuItem(label="Save As")
    save_as_item.connect("activate", save_managed_file_as)
    menu.append(save_as_item)
    configure_item = Gtk.MenuItem(label="Configure")
    configure_item.connect("activate", configure_toasts)
    menu.append(configure_item)
    help_item = Gtk.MenuItem(label="Help")
    help_item.connect("activate", lambda _item: state["editor"].show_help() if state.get("editor") is not None else None)
    menu.append(help_item)
    menu.show_all()
    menu_button.set_popup(menu)
    button_box.pack_start(menu_button, False, False, 0)

    close_button = Gtk.Button(label="Close")
    close_button.connect("clicked", lambda _button: window.destroy())
    button_box.pack_end(close_button, False, False, 0)

    def handle_key_press(_window, event) -> bool:
        if event.keyval == Gdk.KEY_F1:
            editor = state.get("editor")
            if editor is not None and hasattr(editor, "show_help"):
                editor.show_help()
            return True
        return False

    def handle_destroy(_window) -> None:
        stop_config_monitor()
        Gtk.main_quit()

    window.connect("key-press-event", handle_key_press)
    window.connect("destroy", handle_destroy)
    rebuild_editor(test_config_snapshot)
    window.show_all()
    Gtk.main()
    return 0


_MANAGED_CONFIG_RELOAD_EVENT_NAMES = {
    "CHANGED",
    "CHANGES_DONE_HINT",
    "CREATED",
    "DELETED",
    "MOVED_IN",
    "MOVED_OUT",
    "RENAMED",
}


def _is_managed_config_reload_event(event_type) -> bool:
    """Return whether a Gio.FileMonitor event should trigger a config reload."""

    event_name = _file_monitor_event_name(event_type)
    return event_name in _MANAGED_CONFIG_RELOAD_EVENT_NAMES


def _file_monitor_event_name(event_type) -> str:
    name = getattr(event_type, "name", None)
    if name:
        return str(name).upper().replace("-", "_")

    value_nick = getattr(event_type, "value_nick", None)
    if value_nick:
        return str(value_nick).upper().replace("-", "_")

    text = str(event_type).upper().replace("-", "_")
    for event_name in sorted(_MANAGED_CONFIG_RELOAD_EVENT_NAMES, key=len, reverse=True):
        if event_name in text:
            return event_name
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return text


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
            "infobar { padding: 2px; }\n"
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


def _add_lua_filter(Gtk, chooser) -> None:
    lua_filter = Gtk.FileFilter()
    lua_filter.set_name("Lua files")
    lua_filter.add_pattern("*.lua")
    chooser.add_filter(lua_filter)


def _is_under_managed_dir(path: Path, managed_dir: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(managed_dir.resolve(strict=False))
    except (OSError, ValueError):
        return False
    return True


def _show_message(Gtk, parent, text: str) -> None:
    dialog = Gtk.MessageDialog(
        transient_for=parent,
        flags=0,
        message_type=Gtk.MessageType.INFO,
        buttons=Gtk.ButtonsType.OK,
        text=text,
    )
    dialog.run()
    dialog.destroy()


def _show_toast(Gtk, parent, text: str, *, timeout_seconds: int, opacity: float) -> None:
    toast = Gtk.InfoBar()
    toast.set_message_type(Gtk.MessageType.INFO)
    toast.set_show_close_button(True)
    toast.set_opacity(opacity)

    content = toast.get_content_area()
    label = Gtk.Label(label=text)
    label.set_xalign(0)
    label.set_selectable(False)
    label.set_line_wrap(True)
    content.add(label)

    def dismiss() -> bool:
        if toast.get_parent() is not None:
            parent.remove(toast)
        return False

    toast.connect("response", lambda _toast, _response: dismiss())
    parent.pack_end(toast, False, False, 0)
    toast.show_all()

    try:
        from gi.repository import GLib
    except (ImportError, ValueError):  # pragma: no cover
        return
    GLib.timeout_add_seconds(timeout_seconds, dismiss)


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
