from d2wc.desktop.active_window import (
    ActiveWindowInfo,
    CaptureCommandError,
    WindowGeometry,
    capture_active_window,
    parse_active_window_id,
    parse_wm_class,
    parse_xprop_string,
    parse_xwininfo_geometry,
)
from d2wc.ui.gtk_app import format_active_window_info


def test_parse_active_window_id() -> None:
    output = '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3e00007\n'

    assert parse_active_window_id(output) == "0x3e00007"


def test_parse_active_window_id_returns_none_for_zero() -> None:
    output = '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x0\n'

    assert parse_active_window_id(output) is None


def test_parse_xprop_string() -> None:
    output = 'WM_NAME(STRING) = "Terminal"\n_QUBES_VMNAME(STRING) = "work"\n'

    assert parse_xprop_string(output, "WM_NAME") == "Terminal"
    assert parse_xprop_string(output, "_QUBES_VMNAME") == "work"


def test_parse_xprop_string_preserves_empty_qubes_vmname() -> None:
    output = '_QUBES_VMNAME(STRING) = ""\n'

    assert parse_xprop_string(output, "_QUBES_VMNAME") == ""


def test_parse_wm_class() -> None:
    output = 'WM_CLASS(STRING) = "Navigator", "firefox"\n'

    assert parse_wm_class(output) == ("Navigator", "firefox")


def test_parse_xwininfo_geometry() -> None:
    output = """
xwininfo: Window id: 0x3e00007 "Terminal"

  Absolute upper-left X:  10
  Absolute upper-left Y:  20
  Width: 800
  Height: 600
"""

    assert parse_xwininfo_geometry(output) == WindowGeometry(x=10, y=20, width=800, height=600)


def test_capture_active_window_with_mocked_commands() -> None:
    outputs = {
        ("xprop", "-root", "_NET_ACTIVE_WINDOW"): '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3e00007\n',
        (
            "xprop",
            "-id",
            "0x3e00007",
            "WM_NAME",
            "WM_CLASS",
            "_QUBES_VMNAME",
        ): 'WM_NAME(STRING) = "Terminal"\nWM_CLASS(STRING) = "xfce4-terminal", "Xfce4-terminal"\n_QUBES_VMNAME(STRING) = "work"\n',
        ("xwininfo", "-id", "0x3e00007"): """
  Absolute upper-left X:  10
  Absolute upper-left Y:  20
  Width: 800
  Height: 600
""",
    }

    def runner(command):
        return outputs[tuple(command)]

    info = capture_active_window(runner=runner)

    assert info.window_id == "0x3e00007"
    assert info.title == "Terminal"
    assert info.wm_class_instance == "xfce4-terminal"
    assert info.wm_class == "Xfce4-terminal"
    assert info.qubes_vmname == "work"
    assert info.domain == "work"
    assert info.geometry == WindowGeometry(x=10, y=20, width=800, height=600)
    assert info.error is None


def test_capture_active_window_treats_empty_qubes_vmname_as_dom0() -> None:
    outputs = {
        ("xprop", "-root", "_NET_ACTIVE_WINDOW"): '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3e00007\n',
        (
            "xprop",
            "-id",
            "0x3e00007",
            "WM_NAME",
            "WM_CLASS",
            "_QUBES_VMNAME",
        ): 'WM_NAME(STRING) = "Qubes Manager"\nWM_CLASS(STRING) = "qubes-qube-manager", "Qubes-qube-manager"\n_QUBES_VMNAME(STRING) = ""\n',
        ("xwininfo", "-id", "0x3e00007"): "",
    }

    def runner(command):
        return outputs[tuple(command)]

    info = capture_active_window(runner=runner)

    assert info.qubes_vmname == ""
    assert info.domain == "dom0"


def test_capture_active_window_reports_command_error() -> None:
    def runner(_command):
        raise CaptureCommandError("xprop failed")

    info = capture_active_window(runner=runner)

    assert info.error == "xprop failed"


def test_format_active_window_info() -> None:
    info = ActiveWindowInfo(
        window_id="0x3e00007",
        title="Terminal",
        wm_class_instance="xfce4-terminal",
        wm_class="Xfce4-terminal",
        qubes_vmname="work",
        geometry=WindowGeometry(x=10, y=20, width=800, height=600),
    )

    text = format_active_window_info(info)

    assert "Window ID: 0x3e00007" in text
    assert "Title: Terminal" in text
    assert "Class instance: xfce4-terminal" in text
    assert "Class: Xfce4-terminal" in text
    assert "Qubes domain: work" in text
    assert "Geometry: x=10 y=20 w=800 h=600" in text


def test_format_active_window_info_reports_errors() -> None:
    info = ActiveWindowInfo(error="Could not determine active window")

    assert format_active_window_info(info) == "Active window capture failed:\nCould not determine active window"
