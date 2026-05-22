from pathlib import Path

from d2wc.desktop.active_window import (
    ActiveWindowInfo,
    ScreenGeometry,
    WindowGeometry,
    format_probe_number,
    parse_devilspie2_probe_output,
    parse_screen_geometry,
    parse_window_geometry,
    run_devilspie2_probe,
)
from d2wc.ui.gtk_app import format_active_window_info


THUNDERBIRD_PROBE = """Domain: thunderbird-personal
Application name: thunderbird-personal:net.thunderbird.Thunderbird
Window name: Mozilla Thunderbird
Window Type: WINDOW_TYPE_NORMAL
Class instance name: thunderbird-personal:Mail
Window class: thunderbird-personal:net.thunderbird.Thunderbird
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
"""

TOR_BROWSER_PROBE = """Domain: disp3979
Application name: disp3979:Tor Browser
Window name: Tor Browser
Window Type: WINDOW_TYPE_NORMAL
Class instance name: disp3979:Navigator
Window class: disp3979:Tor Browser
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 0.0 y = 46.0 w = 2122.0 h = 1578.0
"""


def test_parse_devilspie2_probe_output() -> None:
    info = parse_devilspie2_probe_output(THUNDERBIRD_PROBE)

    assert info.domain == "thunderbird-personal"
    assert info.normalized_domain == "thunderbird-personal"
    assert info.application_name == "thunderbird-personal:net.thunderbird.Thunderbird"
    assert info.window_name == "Mozilla Thunderbird"
    assert info.window_type == "WINDOW_TYPE_NORMAL"
    assert info.class_instance_name == "thunderbird-personal:Mail"
    assert info.window_class == "thunderbird-personal:net.thunderbird.Thunderbird"
    assert info.screen_geometry == ScreenGeometry(x=3840.0, y=2160.0)
    assert info.geometry == WindowGeometry(x=474.0, y=359.0, width=3366.0, height=1801.0)
    assert info.raw_devilspie2_output == THUNDERBIRD_PROBE


def test_parse_devilspie2_probe_output_with_spaces_in_values() -> None:
    info = parse_devilspie2_probe_output(TOR_BROWSER_PROBE)

    assert info.domain == "disp3979"
    assert info.application_name == "disp3979:Tor Browser"
    assert info.window_name == "Tor Browser"
    assert info.class_instance_name == "disp3979:Navigator"
    assert info.window_class == "disp3979:Tor Browser"
    assert info.geometry == WindowGeometry(x=0.0, y=46.0, width=2122.0, height=1578.0)


def test_empty_domain_normalizes_to_dom0() -> None:
    info = ActiveWindowInfo(domain="")

    assert info.normalized_domain == "dom0"


def test_parse_screen_geometry() -> None:
    assert parse_screen_geometry("x = 3840.0 y = 2160.0") == ScreenGeometry(x=3840.0, y=2160.0)
    assert parse_screen_geometry(None) == ScreenGeometry()


def test_parse_window_geometry() -> None:
    assert parse_window_geometry("x = 474.0 y = 359.0 w = 3366.0 h = 1801.0") == WindowGeometry(
        x=474.0,
        y=359.0,
        width=3366.0,
        height=1801.0,
    )
    assert parse_window_geometry(None) == WindowGeometry()


def test_window_geometry_size_text() -> None:
    assert WindowGeometry(width=800.0, height=600.0).size_text == "800x600"
    assert WindowGeometry(width=800.5, height=600.25).size_text == "800.5x600.25"
    assert WindowGeometry(width=800.0).size_text is None


def test_format_probe_number() -> None:
    assert format_probe_number(800.0) == "800"
    assert format_probe_number(800.5) == "800.5"
    assert format_probe_number(None) == "unknown"


def test_format_active_window_info() -> None:
    info = parse_devilspie2_probe_output(THUNDERBIRD_PROBE)

    text = format_active_window_info(info)

    assert text == "\n".join(
        [
            "Domain: thunderbird-personal",
            "Application name: thunderbird-personal:net.thunderbird.Thunderbird",
            "Window name: Mozilla Thunderbird",
            "Window Type: WINDOW_TYPE_NORMAL",
            "Class instance name: thunderbird-personal:Mail",
            "Window class: thunderbird-personal:net.thunderbird.Thunderbird",
            "Screen Geometry: x = 3840 y = 2160",
            "Window geometry: x = 474 y = 359 w = 3366 h = 1801",
            "geometry 3366x1801",
        ]
    )


def test_format_active_window_info_reports_errors() -> None:
    info = ActiveWindowInfo(error="Timed out waiting for a Devilspie2 normal-window probe report.")

    assert format_active_window_info(info) == (
        "Window probe failed:\nTimed out waiting for a Devilspie2 normal-window probe report."
    )


def test_format_active_window_info_reports_errors_with_raw_output() -> None:
    info = ActiveWindowInfo(
        error="Timed out waiting for a Devilspie2 normal-window probe report.",
        raw_devilspie2_output="partial output",
    )

    text = format_active_window_info(info)

    assert "Window probe failed:" in text
    assert "Timed out waiting" in text
    assert "Raw Devilspie2 output:" in text
    assert "partial output" in text


def test_run_devilspie2_probe_reports_missing_binary(monkeypatch, tmp_path: Path) -> None:
    def fake_popen(*_args, **_kwargs):
        raise FileNotFoundError

    monkeypatch.setattr("d2wc.desktop.active_window.subprocess.Popen", fake_popen)

    info = run_devilspie2_probe(config_home=tmp_path, timeout_seconds=0.01)

    assert info.error == "Required command not found: devilspie2"
