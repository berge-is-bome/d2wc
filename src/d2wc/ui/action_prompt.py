"""Small action prompt for unconfigured window events."""

from __future__ import annotations

from typing import Literal

from d2wc.event_data import WindowEventData
from d2wc.ui.gtk_app import _import_gtk

ACTION_PROMPT_WINDOW_CLASS = "d2wc-action-prompt"
PROMPT_MARGIN = 12
PROMPT_BUTTON_WIDTH = 112
PROMPT_CSS = """
button.d2wc-prompt-button,
.d2wc-prompt-button {
  min-width: 0;
  min-height: 0;
  padding-left: 4px;
  padding-right: 4px;
}
button.d2wc-prompt-cancel,
.d2wc-prompt-cancel {
  background-image: none;
  background-color: #e0a323;
  color: #1d1d1d;
}
button.d2wc-prompt-configure,
.d2wc-prompt-configure {
  background-image: none;
  background-color: #6a35e8;
  color: #ffffff;
}
"""

ActionPromptDecision = Literal["cancel", "configure"]


def run_action_prompt(event_data: WindowEventData) -> ActionPromptDecision:
    """Show a small Cancel/Configure prompt near the event window."""

    Gtk, Gdk, GLib = _import_gtk()
    _set_prompt_window_class(Gdk, GLib)

    decision: dict[str, ActionPromptDecision] = {"value": "cancel"}

    window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    window.set_wmclass(ACTION_PROMPT_WINDOW_CLASS, ACTION_PROMPT_WINDOW_CLASS)
    window.set_title("d2wc")
    window.set_decorated(False)
    window.set_resizable(False)
    window.set_skip_taskbar_hint(True)
    window.set_skip_pager_hint(True)
    window.set_keep_above(True)
    window.set_border_width(0)
    if hasattr(Gdk, "WindowTypeHint"):
        window.set_type_hint(Gdk.WindowTypeHint.UTILITY)

    _install_prompt_css(Gtk, Gdk)

    button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    window.add(button_box)

    cancel_button = Gtk.Button(label="Cancel")
    cancel_button.set_size_request(PROMPT_BUTTON_WIDTH, -1)
    cancel_button.get_style_context().add_class("d2wc-prompt-button")
    cancel_button.get_style_context().add_class("d2wc-prompt-cancel")
    button_box.pack_start(cancel_button, False, False, 0)

    configure_button = Gtk.Button(label="Configure")
    configure_button.set_size_request(PROMPT_BUTTON_WIDTH, -1)
    configure_button.get_style_context().add_class("d2wc-prompt-button")
    configure_button.get_style_context().add_class("d2wc-prompt-configure")
    button_box.pack_start(configure_button, False, False, 0)

    def choose(value: ActionPromptDecision) -> None:
        decision["value"] = value
        window.destroy()

    cancel_button.connect("clicked", lambda _button: choose("cancel"))
    configure_button.connect("clicked", lambda _button: choose("configure"))
    window.connect("destroy", lambda _window: Gtk.main_quit())

    def handle_key_press(_window, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            choose("cancel")
            return True
        return False

    window.connect("key-press-event", handle_key_press)

    def after_show() -> bool:
        _position_prompt(Gtk, Gdk, GLib, window, cancel_button, event_data)
        return False

    window.show_all()
    GLib.idle_add(after_show)
    Gtk.main()
    return decision["value"]


def _set_prompt_window_class(Gdk, GLib) -> None:
    GLib.set_prgname(ACTION_PROMPT_WINDOW_CLASS)
    Gdk.set_program_class(ACTION_PROMPT_WINDOW_CLASS)


def _install_prompt_css(Gtk, Gdk) -> None:
    provider = Gtk.CssProvider()
    provider.load_from_data(PROMPT_CSS.encode("utf-8"))
    screen = Gdk.Screen.get_default()
    if screen is not None:
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )


def _position_prompt(Gtk, Gdk, GLib, window, cancel_button, event_data: WindowEventData) -> None:
    while Gtk.events_pending():
        Gtk.main_iteration_do(False)

    width, height = window.get_size()
    if width <= 1 or height <= 1:
        allocation = window.get_allocation()
        width = max(width, allocation.width)
        height = max(height, allocation.height)

    x, y = _prompt_origin(Gdk, event_data, width, height)
    window.move(x, y)
    GLib.timeout_add(60, lambda: _center_pointer_on_cancel(Gdk, window, cancel_button))


def _prompt_origin(Gdk, event_data: WindowEventData, prompt_width: int, prompt_height: int) -> tuple[int, int]:
    screen = Gdk.Screen.get_default()
    screen_width = screen.get_width() if screen is not None else 0
    screen_height = screen.get_height() if screen is not None else 0

    geometry = event_data.window_geometry
    if geometry.x is None or geometry.y is None or geometry.w is None or geometry.h is None:
        fallback_x = max(0, screen_width - prompt_width - PROMPT_MARGIN)
        fallback_y = max(0, screen_height - prompt_height - PROMPT_MARGIN)
        return fallback_x, fallback_y

    x = int(round(geometry.x + geometry.w - prompt_width - PROMPT_MARGIN))
    y = int(round(geometry.y + geometry.h - prompt_height - PROMPT_MARGIN))

    if screen_width > 0:
        x = min(max(0, x), max(0, screen_width - prompt_width))
    if screen_height > 0:
        y = min(max(0, y), max(0, screen_height - prompt_height))
    return x, y


def _center_pointer_on_cancel(Gdk, window, cancel_button) -> bool:
    gdk_window = window.get_window()
    if gdk_window is None:
        return False

    origin = gdk_window.get_origin()
    if isinstance(origin, tuple) and len(origin) == 3:
        ok, root_x, root_y = origin
        if not ok:
            return False
    elif isinstance(origin, tuple) and len(origin) == 2:
        root_x, root_y = origin
    else:
        return False

    allocation = cancel_button.get_allocation()
    target_x = int(root_x + allocation.x + allocation.width / 2)
    target_y = int(root_y + allocation.y + allocation.height / 2)
    screen = gdk_window.get_screen()
    display = Gdk.Display.get_default()
    if display is None:
        return False

    try:
        seat = display.get_default_seat()
        pointer = seat.get_pointer()
        pointer.warp(screen, target_x, target_y)
        return False
    except Exception:
        pass

    try:
        manager = display.get_device_manager()
        pointer = manager.get_client_pointer()
        pointer.warp(screen, target_x, target_y)
    except Exception:
        pass
    return False
