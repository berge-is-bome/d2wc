from d2wc.desktop.active_window import (
    ActiveWindowInfo,
    CaptureCommandError,
    WindowGeometry,
    capture_active_window,
    capture_selected_window,
    parse_active_window_id,
    parse_wm_class,
    parse_xprop_string,
    parse_xwininfo_geometry,
    parse_xwininfo_title,
    parse_xwininfo_window_id,
)
from d2wc.ui.gtk_app import format_active_window_info


def test_parse_active_window_id() -> None:
    output = '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x3e00007\n'

    assert parse_active_window_id(output) == "0x3e00007"


def test_parse_active_window_id_supports_compact_xprop_output() -> None:
    output = '_NET_ACTIVE_WINDOW(WINDOW): 0x3e00007\n'

    assert parse_active_window_id(output) == "0x3e00007"


def test_parse_active_window_id_returns_none_for_zero() -> None:
    output = '_NET_ACTIVE_WINDOW(WINDOW): window id # 0x0\n'

    assert parse_active_window_id(output) is None


def test_parse_xwininfo_window_id() -> None:
    output = 'xwininfo: Window id: 0x3e00007 "Terminal"\n'

    assert parse_xwininfo_window_id(output) == "0x3e00007"


def test_parse_xwininfo_title() -> None:
    output = 'xwininfo: Window id: 0x3e00007 "Terminal"\n'

    assert parse_xwininfo_title(output) == "Terminal"


def test_parse_xwininfo_title_for_no_name() -> None:
    output = 'xwininfo: Window id: 0x3e00007 (has no name)\n'

    assert parse_xwininfo_title(output) == "has no name"


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
  Relative upper-left X:  1
  Relative upper-left Y:  2
  Width: 800
  Height: 600
"""

    assert parse_xwininfo_geometry(output) == WindowGeometry(
        x=10,
        y=20,
        relative_x=1,
        relative_y=2,
        width=800,
        height=600,
    )


def test_window_geometry_size_text() -> None:
    assert WindowGeometry(width=800, height=600).size_text == "800x600"
    assert WindowGeometry(width=800).size_text is None


def test_capture_selected_window_with_mocked_command() -> None:
    xwininfo_output = """
xwininfo: Window id: 0x3e00007 "Terminal"

  Absolute upper-left X:  10
  Absolute upper-left Y:  20
  Relative upper-left X:  1
  Relative upper-left Y:  2
  Width: 800
  Height: 600
"""
    outputs = {
        ("xwininfo", "-frame"): xwininfo_output,
    }

    def runner(command):
        return outputs[tuple(command)]

    info = capture_selected_window(runner=runner)

    assert info.window_id == "0x3e00007"
    assert info.title == "Terminal"
    assert info.wm_class_instance is None
    assert info.wm_class is None
    assert info.qubes_vmname is None
    assert info.domain is None
    assert info.geometry == WindowGeometry(
        x=10,
        y=20,
        relative_x=1,
        relative_y=2,
        width=800,
        height=600,
    )
    assert info.raw_xwininfo_output == xwininfo_output
    assert info.error is None


def test_capture_selected_window_reports_command_error() -> None:
    def runner(_command):
        raise CaptureCommandError("xwininfo failed")

    info = capture_selected_window(runner=runner)

    assert info.error == "xwininfo failed"


def test_capture_selected_window_keeps_raw_xwininfo_when_id_parse_fails() -> None:
    def runner(_command):
        return "unexpected xwininfo output"

    info = capture_selected_window(runner=runner)

    assert info.error == "Could not determine selected window id from xwininfo output."
    assert info.raw_xwininfo_output == "unexpected xwininfo output"


def test_capture_active_window_uses_selected_window_capture_path() -> None:
    outputs = {
        ("xwininfo", "-frame"): 'xwininfo: Window id: 0x3e00007 "Terminal"\n',
    }

    def runner(command):
        return outputs[tuple(command)]

    info = capture_active_window(runner=runner)

    assert info.window_id == "0x3e00007"
    assert info.title == "Terminal"


def test_format_active_window_info() -> None:
    info = ActiveWindowInfo(
        window_id="0x3e00007",
        title="Terminal",
        geometry=WindowGeometry(
            x=10,
            y=20,
            relative_x=1,
            relative_y=2,
            width=800,
            height=600,
        ),
        raw_xwininfo_output="xwininfo raw output",
    )

    text = format_active_window_info(info)

    assert text == "\n".join(
        [
            "Absolute upper-left X:  10",
            "Absolute upper-left Y:  20",
            "Relative upper-left X:  1",
            "Relative upper-left Y:  2",
            "Width: 800",
            "Height: 600",
            "Geometry: x=10 y=20 w=800 h=600",
            "geometry 800x600",
        ]
    )


def test_format_active_window_info_reports_errors() -> None:
    info = ActiveWindowInfo(error="Could not determine selected window")

    assert format_active_window_info(info) == "Window capture failed:\nCould not determine selected window"


def test_format_active_window_info_reports_errors_with_raw_xwininfo() -> None:
    info = ActiveWindowInfo(
        error="Could not determine selected window",
        raw_xwininfo_output="unexpected xwininfo output",
    )

    text = format_active_window_info(info)

    assert "Window capture failed:" in text
    assert "Could not determine selected window" in text
    assert "Raw xwininfo -frame output kept for debugging." in text
