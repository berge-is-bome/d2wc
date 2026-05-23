from pathlib import Path

from d2wc.test_config import (
    BUNDLED_CONFIG_PATH,
    default_test_config_path,
    format_prepare_result,
    format_test_config_status,
    load_test_config_snapshot,
    prepare_test_config,
)


VALID_MINIMAL_CONFIG = '''
local EXCLUDE = {
  "d:personal-test",
}
local PIN = {
  "d:dom0 c:xfce4-terminal",
}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", },
}
local GEOM = {
  half_left = { x = 0, y = 0, w = 1920, h = 2115 },
}
local WORKSPACE_PLACEMENT = {
  "d:personal c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {
  "d:personal c:okular le:pos2",
}
'''


def test_default_test_config_path_uses_user_home(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    assert default_test_config_path() == tmp_path / ".config" / "devilspie2" / "d2wc-test.lua"


def test_prepare_test_config_creates_target(tmp_path) -> None:
    source_path = tmp_path / "source.lua"
    target_path = tmp_path / "nested" / "d2wc-test.lua"
    source_path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")

    result = prepare_test_config(target_path=target_path, source_path=source_path)

    assert result.created
    assert not result.replaced
    assert not result.skipped
    assert target_path.read_text(encoding="utf-8") == VALID_MINIMAL_CONFIG


def test_prepare_test_config_skips_existing_without_replace(tmp_path) -> None:
    source_path = tmp_path / "source.lua"
    target_path = tmp_path / "d2wc-test.lua"
    source_path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")
    target_path.write_text("existing", encoding="utf-8")

    result = prepare_test_config(target_path=target_path, source_path=source_path)

    assert result.skipped
    assert target_path.read_text(encoding="utf-8") == "existing"


def test_prepare_test_config_replaces_existing(tmp_path) -> None:
    source_path = tmp_path / "source.lua"
    target_path = tmp_path / "d2wc-test.lua"
    source_path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")
    target_path.write_text("existing", encoding="utf-8")

    result = prepare_test_config(target_path=target_path, source_path=source_path, replace=True)

    assert result.replaced
    assert target_path.read_text(encoding="utf-8") == VALID_MINIMAL_CONFIG


def test_load_test_config_snapshot_missing(tmp_path) -> None:
    path = tmp_path / "missing.lua"

    snapshot = load_test_config_snapshot(path)

    assert not snapshot.exists
    assert not snapshot.ok
    assert snapshot.error == "test config does not exist yet"


def test_load_test_config_snapshot_valid(tmp_path) -> None:
    path = tmp_path / "d2wc-test.lua"
    path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")

    snapshot = load_test_config_snapshot(path)

    assert snapshot.ok
    assert snapshot.config is not None
    assert [section.name for section in snapshot.sections] == [
        "EXCLUDE",
        "PIN",
        "WORKSPACE_ROUTES",
        "GEOM",
        "WORKSPACE_PLACEMENT",
        "LEFT_EDGE_CORRECTION",
    ]
    assert snapshot.sections[0].entries == ("d:personal-test",)
    assert "half_left: x=0 y=0 w=1920 h=2115" in snapshot.sections[3].entries


def test_format_test_config_status() -> None:
    path = BUNDLED_CONFIG_PATH
    snapshot = load_test_config_snapshot(path)

    text = format_test_config_status(snapshot)

    assert f"Test config: {path}" in text
    assert "Status: valid" in text


def test_format_prepare_result(tmp_path) -> None:
    source_path = tmp_path / "source.lua"
    target_path = tmp_path / "d2wc-test.lua"
    source_path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")
    result = prepare_test_config(target_path=target_path, source_path=source_path)

    text = format_prepare_result(result)

    assert "Prepare result: test config created" in text
    assert f"Target: {target_path}" in text
    assert f"Source: {source_path}" in text
