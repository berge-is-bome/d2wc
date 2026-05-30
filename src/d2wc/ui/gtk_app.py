"""GTK configurator proof for Devilspie2 managed config editing."""

from __future__ import annotations

from pathlib import Path
import re

from d2wc.core.saving import SaveConfigError, SaveValidationError, save_source_config
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
D2WC_EVENT_HANDOFF_PATTERN = re.compile(
    r"(?m)^(?P<prefix>\s*local\s+D2WC_EVENT_HANDOFF_ENABLED\s*=\s*)"
    r"(?P<value>true|false)"
    r"(?P<suffix>\s*(?:--.*)?)$"
)
D2WC_EVENT_HANDOFF_ENTRY_POINT_PATTERN = re.compile(
    r"(?m)^(?P<prefix>\s*local\s+D2WC_EVENT_HANDOFF_ENTRY_POINT\s*=\s*)"
    r'"(?P<value>configurator|prompt)"'
    r"(?P<suffix>\s*(?:--.*)?)$"
)
D2WC_EVENT_HANDOFF_ENTRY_POINTS = {"configurator", "prompt"}


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
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as exc:  # pragma: no cover
        raise GtkConfiguratorImportError(
            "GTK 3 bindings are not available. Install the system GTK 3 PyGObject bindings, "
            "then run `python -m d2wc configure` again."
        ) from exc

    return Gtk, Gdk, GLib


def run_configurator(
    event_data: WindowEventData | None = None,
    config_awareness=None,
    test_config_snapshot: TestConfigSnapshot | None = None,
    prepare_result: TestConfigPrepareResult | None = None,
) -> int:
    """Open the GTK configurator proof window."""

    _event = event_data or get_event_fixture(DEFAULT_EVENT_FIXTURE)
    ui_settings = load_ui_settings()
    Gtk, Gdk, GLib = _import_gtk()
    _set_configurator_window_class(Gdk, GLib)
    _apply_ui_css(Gtk, Gdk)

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

    def stop_current_editor() -> None:
        editor = state.get("editor")
        if editor is not None and hasattr(editor, "stop"):
            editor.stop()
        state["editor"] = None

    def clear_content() -> None:
        for child in content.get_children():
            content.remove(child)

    def rebuild_editor(snapshot: TestConfigSnapshot | None) -> None:
        stop_current_editor()
        clear_content()
        editor = build_managed_section_editor(Gtk, snapshot, _event, GLib=GLib, toast_settings=current_toast_settings)
        state["snapshot"] = snapshot
        state["editor"] = editor
        content.pack_start(editor.widget, True, True, 0)
        content.show_all()
        update_window_state()

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
        activate_managed_config(selected)
        rebuild_editor(snapshot)

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

    def show_settings_page(active_page: str = "behavior") -> None:
        stop_current_editor()
        clear_content()
        content.pack_start(build_settings_view(active_page), True, True, 0)
        content.show_all()
        update_window_state()

    def configure_preferences(_item=None) -> None:
        show_settings_page("behavior")

    def build_settings_view(active_page: str):
        settings_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        settings_box.set_hexpand(True)
        settings_box.set_vexpand(True)
        settings_box.set_margin_top(8)
        settings_box.set_margin_bottom(8)
        settings_box.set_margin_start(8)
        settings_box.set_margin_end(8)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar.set_size_request(220, -1)
        settings_box.pack_start(sidebar, False, False, 0)

        nav_heading = Gtk.Label(label="Configure")
        nav_heading.set_xalign(0)
        if hasattr(nav_heading, "set_markup"):
            nav_heading.set_markup("<b>Configure</b>")
        sidebar.pack_start(nav_heading, False, False, 0)

        stack = Gtk.Stack()
        stack.set_hexpand(True)
        stack.set_vexpand(True)
        settings_box.pack_start(stack, True, True, 0)

        behavior_button = Gtk.ToggleButton(label="Behavior")
        notifications_button = Gtk.ToggleButton(label="Notifications")
        sidebar.pack_start(behavior_button, False, False, 0)
        sidebar.pack_start(notifications_button, False, False, 0)

        back_button = Gtk.Button(label="Back")
        back_button.set_halign(Gtk.Align.START)
        back_button.connect("clicked", lambda _button: rebuild_editor(current_snapshot()))
        sidebar.pack_end(back_button, False, False, 0)

        stack.add_named(build_behavior_settings_page(), "behavior")
        stack.add_named(build_notifications_settings_page(), "notifications")

        def activate_page(page_name: str) -> None:
            stack.set_visible_child_name(page_name)
            behavior_button.set_active(page_name == "behavior")
            notifications_button.set_active(page_name == "notifications")

        behavior_button.connect("toggled", lambda button: activate_page("behavior") if button.get_active() else None)
        notifications_button.connect("toggled", lambda button: activate_page("notifications") if button.get_active() else None)
        activate_page(active_page if active_page in {"behavior", "notifications"} else "behavior")

        return settings_box

    def build_behavior_settings_page():
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_hexpand(True)
        page.set_vexpand(True)
        page.set_margin_top(8)
        page.set_margin_bottom(8)
        page.set_margin_start(8)
        page.set_margin_end(8)

        heading = Gtk.Label(label="Behavior")
        heading.set_xalign(0)
        if hasattr(heading, "set_markup"):
            heading.set_markup("<b>Behavior</b>")
        page.pack_start(heading, False, False, 0)

        subheading = Gtk.Label(label="Automatic opening")
        subheading.set_xalign(0)
        page.pack_start(subheading, False, False, 0)

        snapshot = current_snapshot()
        current_handoff_enabled = None
        current_entry_point = None
        if snapshot is not None and snapshot.exists:
            current_handoff_enabled = _read_event_handoff_enabled(snapshot.path)
            current_entry_point = _read_event_handoff_entry_point(snapshot.path)

        behavior_settings_available = current_handoff_enabled is not None and current_entry_point is not None

        handoff_check = Gtk.CheckButton(label="Automatically open d2wc for unconfigured windows")
        handoff_check.set_active(bool(current_handoff_enabled))
        handoff_check.set_sensitive(current_handoff_enabled is not None)
        page.pack_start(handoff_check, False, False, 0)

        if current_handoff_enabled is None:
            hint_text = "No active managed config with D2WC_EVENT_HANDOFF_ENABLED is loaded."
        else:
            hint_text = (
                "Controls whether Devilspie2 opens d2wc automatically on new window events, "
                "for unconfigured windows."
            )
        hint = Gtk.Label(label=hint_text)
        hint.set_xalign(0)
        hint.set_line_wrap(True)
        page.pack_start(hint, False, False, 0)

        entry_heading = Gtk.Label(label="Entry point")
        entry_heading.set_xalign(0)
        page.pack_start(entry_heading, False, False, 0)

        configurator_radio = Gtk.RadioButton.new_with_label_from_widget(None, "Open configurator directly")
        prompt_radio = Gtk.RadioButton.new_with_label_from_widget(configurator_radio, "Show Cancel/Configure button first")
        configurator_radio.set_sensitive(current_entry_point is not None)
        prompt_radio.set_sensitive(current_entry_point is not None)
        if current_entry_point == "prompt":
            prompt_radio.set_active(True)
        else:
            configurator_radio.set_active(True)
        page.pack_start(configurator_radio, False, False, 0)
        page.pack_start(prompt_radio, False, False, 0)

        if current_entry_point is None:
            entry_hint_text = "No active managed config with D2WC_EVENT_HANDOFF_ENTRY_POINT is loaded."
        else:
            entry_hint_text = "Choose what appears when automatic opening handles an unconfigured window."
        entry_hint = Gtk.Label(label=entry_hint_text)
        entry_hint.set_xalign(0)
        entry_hint.set_line_wrap(True)
        page.pack_start(entry_hint, False, False, 0)

        spacer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.pack_start(spacer, True, True, 0)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        page.pack_start(action_box, False, False, 0)

        apply_button = Gtk.Button(label="Apply")
        apply_button.set_sensitive(behavior_settings_available)
        action_box.pack_end(apply_button, False, False, 0)

        def apply_behavior_settings(_button) -> None:
            nonlocal current_handoff_enabled, current_entry_point
            snapshot_value = current_snapshot()
            if snapshot_value is None or not snapshot_value.exists:
                _show_message(Gtk, window, "No managed config is loaded.")
                return

            current_handoff_enabled = _read_event_handoff_enabled(snapshot_value.path)
            current_entry_point = _read_event_handoff_entry_point(snapshot_value.path)
            if current_handoff_enabled is None or current_entry_point is None:
                _show_message(Gtk, window, "The active managed config does not contain the handoff behavior settings.")
                return

            new_handoff_enabled = bool(handoff_check.get_active())
            new_entry_point = "prompt" if prompt_radio.get_active() else "configurator"
            changed = False

            if new_handoff_enabled != current_handoff_enabled:
                try:
                    _set_event_handoff_enabled(snapshot_value.path, new_handoff_enabled)
                except ValueError as exc:
                    _show_message(Gtk, window, str(exc))
                    return
                except SaveValidationError as exc:
                    _show_message(Gtk, window, "Could not save handoff setting:\n" + "\n".join(exc.validation.errors))
                    return
                except (OSError, SaveConfigError) as exc:
                    _show_message(Gtk, window, f"Could not save handoff setting:\n{exc}")
                    return
                current_handoff_enabled = new_handoff_enabled
                changed = True

            if new_entry_point != current_entry_point:
                try:
                    _set_event_handoff_entry_point(snapshot_value.path, new_entry_point)
                except ValueError as exc:
                    _show_message(Gtk, window, str(exc))
                    return
                except SaveValidationError as exc:
                    _show_message(Gtk, window, "Could not save handoff entry point:\n" + "\n".join(exc.validation.errors))
                    return
                except (OSError, SaveConfigError) as exc:
                    _show_message(Gtk, window, f"Could not save handoff entry point:\n{exc}")
                    return
                current_entry_point = new_entry_point
                changed = True

            if changed:
                refreshed = load_managed_config_snapshot(snapshot_value.path)
                if refreshed.ok:
                    state["snapshot"] = refreshed

            timeout_seconds, opacity = current_toast_settings()
            handoff_text = "enabled" if current_handoff_enabled else "disabled"
            entry_point_text = "button" if current_entry_point == "prompt" else "configurator"
            _show_toast(
                Gtk,
                outer,
                f"Behavior settings updated: automatic handoff {handoff_text}, entry point {entry_point_text}",
                timeout_seconds=timeout_seconds,
                opacity=opacity,
            )

        apply_button.connect("clicked", apply_behavior_settings)
        return page

    def build_notifications_settings_page():
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        page.set_hexpand(True)
        page.set_vexpand(True)
        page.set_margin_top(8)
        page.set_margin_bottom(8)
        page.set_margin_start(8)
        page.set_margin_end(8)

        heading = Gtk.Label(label="Notifications")
        heading.set_xalign(0)
        if hasattr(heading, "set_markup"):
            heading.set_markup("<b>Notifications</b>")
        page.pack_start(heading, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        grid.set_hexpand(True)
        page.pack_start(grid, False, False, 0)

        timeout_seconds, opacity = current_toast_settings()

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

        spacer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        page.pack_start(spacer, True, True, 0)

        action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        page.pack_start(action_box, False, False, 0)

        apply_button = Gtk.Button(label="Apply")
        action_box.pack_end(apply_button, False, False, 0)

        def apply_notification_settings(_button) -> None:
            new_timeout = int(timeout_spin.get_value_as_int())
            new_opacity = float(opacity_spin.get_value())

            state["toast_timeout_seconds"] = new_timeout
            state["toast_opacity"] = new_opacity
            save_ui_settings(
                UiSettings(
                    toast_timeout_seconds=new_timeout,
                    toast_opacity=new_opacity,
                )
            )

            timeout_seconds_value, opacity_value = current_toast_settings()
            _show_toast(
                Gtk,
                outer,
                f"Notification settings updated: {timeout_seconds_value}s, opacity {opacity_value:.2f}",
                timeout_seconds=timeout_seconds_value,
                opacity=opacity_value,
            )

        apply_button.connect("clicked", apply_notification_settings)
        return page

    def handle_destroy(_window) -> None:
        stop_current_editor()
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
    configure_item.connect("activate", configure_preferences)
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

    window.connect("key-press-event", handle_key_press)
    rebuild_editor(test_config_snapshot)
    window.show_all()
    Gtk.main()
    return 0


def _set_configurator_window_class(Gdk, GLib) -> None:
    """Publish a stable X11/WM class for Devilspie2 matching."""

    GLib.set_prgname(CONFIGURATOR_WINDOW_CLASS)
    Gdk.set_program_class(CONFIGURATOR_WINDOW_CLASS)


def _apply_ui_css(Gtk, Gdk) -> None:
    """Apply application-scoped GTK CSS tweaks."""

    provider = Gtk.CssProvider()
    provider.load_from_data(
        (
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


def _read_event_handoff_enabled(config_path: Path) -> bool | None:
    try:
        source = Path(config_path).read_text(encoding="utf-8")
    except OSError:
        return None
    match = D2WC_EVENT_HANDOFF_PATTERN.search(source)
    if match is None:
        return None
    return match.group("value") == "true"


def _read_event_handoff_entry_point(config_path: Path) -> str | None:
    try:
        source = Path(config_path).read_text(encoding="utf-8")
    except OSError:
        return None
    match = D2WC_EVENT_HANDOFF_ENTRY_POINT_PATTERN.search(source)
    if match is None:
        return None
    value = match.group("value")
    if value not in D2WC_EVENT_HANDOFF_ENTRY_POINTS:
        return None
    return value


def _set_event_handoff_enabled(config_path: Path, enabled: bool) -> None:
    path = Path(config_path)
    source = path.read_text(encoding="utf-8")
    replacement_value = "true" if enabled else "false"

    def replace(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}{replacement_value}{match.group('suffix')}"

    updated, count = D2WC_EVENT_HANDOFF_PATTERN.subn(replace, source, count=1)
    if count != 1:
        raise ValueError("The active managed config does not contain D2WC_EVENT_HANDOFF_ENABLED.")

    save_source_config(path, updated)


def _set_event_handoff_entry_point(config_path: Path, entry_point: str) -> None:
    if entry_point not in D2WC_EVENT_HANDOFF_ENTRY_POINTS:
        raise ValueError(f"Unsupported handoff entry point: {entry_point}")

    path = Path(config_path)
    source = path.read_text(encoding="utf-8")

    def replace(match: re.Match[str]) -> str:
        return f"{match.group('prefix')}\"{entry_point}\"{match.group('suffix')}"

    updated, count = D2WC_EVENT_HANDOFF_ENTRY_POINT_PATTERN.subn(replace, source, count=1)
    if count != 1:
        raise ValueError("The active managed config does not contain D2WC_EVENT_HANDOFF_ENTRY_POINT.")

    save_source_config(path, updated)


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
