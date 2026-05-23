from pathlib import Path

from d2wc.core.backup import extract_backup_member_text, list_backup_members
from d2wc.cli import main


ROUTE_SOURCE = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", "d:work", },
  [2] = { "d:personal c:navigator", },
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''


def write_route_config(tmp_path: Path) -> Path:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text(ROUTE_SOURCE, encoding="utf-8")
    return config_path


def test_cli_add_route_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-route",
            "--config",
            str(config_path),
            "--workspace",
            "3",
            "--rule",
            "d:test c:krusader",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "Planned WORKSPACE_ROUTES add: workspace=3 rule=d:test c:krusader" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_add_route_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-route",
            "--config",
            str(config_path),
            "--workspace",
            "3",
            "--rule",
            "d:test c:krusader",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.bak.tgz"))

    assert exit_code == 0
    assert "OK: WORKSPACE_ROUTES rule added: workspace=3 rule=d:test c:krusader" in captured.out
    assert '[3] = { "d:test c:krusader", },' in saved
    assert backups
    members = list_backup_members(backups[0])
    assert extract_backup_member_text(backups[0], members[-1]) == original


def test_cli_add_route_rejects_duplicate_target(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-route",
            "--config",
            str(config_path),
            "--workspace",
            "3",
            "--rule",
            "d:personal",
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "route rule already exists for target: d:personal" in captured.out
    assert "Use modify-route" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_route_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "modify-route",
            "--config",
            str(config_path),
            "--old-rule",
            "d:personal",
            "--new-workspace",
            "2",
            "--new-rule",
            "d:personal c:krusader",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned WORKSPACE_ROUTES modify: workspace=2 rule=d:personal c:krusader" in captured.out
    assert "Old workspace: 1" in captured.out
    assert "Old rule: d:personal" in captured.out
    assert config_path.read_text(encoding="utf-8") == original


def test_cli_modify_route_write_updates_config(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)

    exit_code = main(
        [
            "modify-route",
            "--config",
            str(config_path),
            "--old-rule",
            "d:personal",
            "--new-workspace",
            "2",
            "--new-rule",
            "d:personal c:krusader",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: WORKSPACE_ROUTES rule modified: workspace=2 rule=d:personal c:krusader" in captured.out
    assert '[1] = { "d:work", },' in saved
    assert '[2] = { "d:personal c:navigator", "d:personal c:krusader", },' in saved


def test_cli_delete_route_write_removes_route(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)

    exit_code = main(
        [
            "delete-route",
            "--config",
            str(config_path),
            "--rule",
            "d:personal",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: WORKSPACE_ROUTES rule deleted: workspace=1 rule=d:personal" in captured.out
    assert '[1] = { "d:work", },' in saved
    assert '"d:personal", "d:work"' not in saved


def test_cli_delete_route_rejects_missing_rule(tmp_path, capsys) -> None:
    config_path = write_route_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "delete-route",
            "--config",
            str(config_path),
            "--rule",
            "d:missing",
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "route rule not found: d:missing" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
