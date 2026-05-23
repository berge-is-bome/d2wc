from pathlib import Path

from d2wc.core.backup import extract_backup_member_text, list_backup_members
from d2wc.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_current_config(tmp_path: Path) -> Path:
    source = REPO_ROOT / "src" / "d2wc.lua"
    target = tmp_path / "d2wc.lua"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_cli_add_placement_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-placement",
            "--config",
            str(config_path),
            "--rule",
            "d:personal c:testapp g:centered_mid",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "Planned WORKSPACE_PLACEMENT add: d:personal c:testapp g:centered_mid" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_cli_add_placement_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-placement",
            "--config",
            str(config_path),
            "--rule",
            "g:centered_mid c:testapp d:personal",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.bak.tgz"))

    assert exit_code == 0
    assert "OK: WORKSPACE_PLACEMENT rule added: d:personal c:testapp g:centered_mid" in captured.out
    assert "Backup archive:" in captured.out
    assert '"d:personal c:testapp g:centered_mid",' in saved
    assert backups
    members = list_backup_members(backups[0])
    assert extract_backup_member_text(backups[0], members[-1]) == original


def test_cli_add_placement_rejects_duplicate_target(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-placement",
            "--config",
            str(config_path),
            "--rule",
            "g:half_right C:Okular",
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "placement rule already exists for target: c:okular" in captured.out
    assert "Use modify-placement" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_add_placement_rejects_missing_geom(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-placement",
            "--config",
            str(config_path),
            "--rule",
            "c:testapp g:not_there",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "geometry profile not found: not_there" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_placement_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "modify-placement",
            "--config",
            str(config_path),
            "--old-rule",
            "c:okular g:half_right",
            "--new-rule",
            "c:okular g:centered_mid",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned WORKSPACE_PLACEMENT modify: c:okular g:centered_mid" in captured.out
    assert "Old rule: c:okular g:half_right" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_placement_write_updates_existing_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main(
        [
            "modify-placement",
            "--config",
            str(config_path),
            "--old-rule",
            "g:half_right c:okular",
            "--new-rule",
            "g:centered_mid c:okular",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: WORKSPACE_PLACEMENT rule modified: c:okular g:centered_mid" in captured.out
    assert '"c:okular g:half_right"' not in saved
    assert '"c:okular g:centered_mid",' in saved


def test_cli_modify_placement_rejects_missing_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "modify-placement",
            "--config",
            str(config_path),
            "--old-rule",
            "c:missing g:centered_mid",
            "--new-rule",
            "c:missing g:half_right",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "placement rule not found: c:missing g:centered_mid" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_delete_placement_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "delete-placement",
            "--config",
            str(config_path),
            "--rule",
            "c:okular g:half_right",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned WORKSPACE_PLACEMENT delete: c:okular g:half_right" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_delete_placement_write_removes_existing_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main(
        [
            "delete-placement",
            "--config",
            str(config_path),
            "--rule",
            "g:half_right c:okular",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: WORKSPACE_PLACEMENT rule deleted: c:okular g:half_right" in captured.out
    assert '"c:okular g:half_right"' not in saved


def test_cli_delete_placement_rejects_missing_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "delete-placement",
            "--config",
            str(config_path),
            "--rule",
            "c:missing g:centered_mid",
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "placement rule not found: c:missing g:centered_mid" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
