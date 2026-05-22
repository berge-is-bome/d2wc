from pathlib import Path

from d2wc.desktop.active_window import (
    ActiveWindowInfo,
    parse_colon_field,
    parse_devilspie2_probe_output,
    run_devilspie2_probe,
)
from d2wc.ui.gtk_app import format_active_window_info


CLASS_INSTANCE_PROBE = "Class instance name: thunderbird-personal:Mail\n"
TOR_CLASS_INSTANCE_PROBE = "Class instance name: disp3979:Navigator\n"


def test_parse_devilspie2_probe_output() -> None:
    info = parse_devilspie2_probe_output(CLASS_INSTANCE_PROBE)

    assert info.class_instance_name == "thunderbird-personal:Mail"
    assert info.raw_devilspie2_output == CLASS_INSTANCE_PROBE


def test_parse_devilspie2_probe_output_with_tor_browser_value() -> None:
    info = parse_devilspie2_probe_output(TOR_CLASS_INSTANCE_PROBE)

    assert info.class_instance_name == "disp3979:Navigator"


def test_parse_colon_field() -> None:
    output = "Class instance name: thunderbird-personal:Mail\nOther: ignored\n"

    assert parse_colon_field(output, "Class instance name") == "thunderbird-personal:Mail"
    assert parse_colon_field(output, "Missing") is None


def test_format_active_window_info() -> None:
    info = ActiveWindowInfo(class_instance_name="thunderbird-personal:Mail")

    assert format_active_window_info(info) == "Class instance name: thunderbird-personal:Mail"


def test_format_active_window_info_preserves_empty_value() -> None:
    info = ActiveWindowInfo(class_instance_name="")

    assert format_active_window_info(info) == "Class instance name: empty"


def test_format_active_window_info_reports_errors() -> None:
    info = ActiveWindowInfo(error="Timed out waiting for a Devilspie2 class-instance probe report.")

    assert format_active_window_info(info) == (
        "Window probe failed:\nTimed out waiting for a Devilspie2 class-instance probe report."
    )


def test_format_active_window_info_reports_errors_with_raw_output() -> None:
    info = ActiveWindowInfo(
        error="Timed out waiting for a Devilspie2 class-instance probe report.",
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
