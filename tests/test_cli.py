from pathlib import Path

from d2wc.cli import main
from d2wc.core.rendering import render_source
from d2wc.core.backup import extract_backup_member_text, list_backup_members


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_current_config(tmp_path: Path) -> Path:
    source = REPO_ROOT / "src" / "d2wc.lua"
    target = tmp_path / "d2wc.lua"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_cli_render_requires_stdout(capsys) -> None:
    exit_code = main(["render", "--config", str(REPO_ROOT / "src" / "d2wc.lua")])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "render is dry-run only" in captured.out


def test_cli_render_stdout_prints_rendered_lua_source(capsys) -> None:
    config_path = REPO_ROOT / "src" / "d2wc.lua"
    source = config_path.read_text(encoding="utf-8")
    expected = render_source(source).source

    exit_code = main(["render", "--config", str(config_path), "--stdout"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out == expected
    assert captured.err == ""


def test_cli_render_rejects_invalid_config(tmp_path, capsys) -> None:
    config_path = tmp_path / "invalid.lua"
    config_path.write_text(
        '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
''',
        encoding="utf-8",
    )

    exit_code = main(["render", "--config", str(config_path), "--stdout"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot render invalid config" in captured.out
    assert "EXCLUDE: rule must include d: or c:: g:half_left" in captured.out


def test_cli_save_without_write_previews_and_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(["save", "--config", str(config_path)])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "Planned backup archive:" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert "Run again with --write to save." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_cli_save_preview_uses_explicit_backup_directory_without_creating_it(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    backup_dir = tmp_path / "backups"

    exit_code = main(
        [
            "save",
            "--config",
            str(config_path),
            "--backup-dir",
            str(backup_dir),
        ]
    )

    captured = capsys.readouterr()
    output_lines = captured.out.splitlines()
    planned_backup_lines = [line for line in output_lines if line.startswith("Planned backup archive: ")]

    assert exit_code == 0
    assert len(planned_backup_lines) == 1
    planned_backup = planned_backup_lines[0].removeprefix("Planned backup archive: ")
    assert planned_backup == str(backup_dir / "d2wc.lua.bak.tgz")
    assert not backup_dir.exists()


def test_cli_save_write_saves_config_and_prints_backup_path(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main(["save", "--config", str(config_path), "--write"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "OK: config saved." in captured.out
    assert "Backup archive:" in captured.out
    assert list(tmp_path.glob("d2wc.lua.bak.tgz"))


def test_cli_save_write_uses_explicit_backup_directory(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    backup_dir = tmp_path / "backups"

    exit_code = main(
        [
            "save",
            "--config",
            str(config_path),
            "--backup-dir",
            str(backup_dir),
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "OK: config saved." in captured.out
    assert list(backup_dir.glob("d2wc.lua.bak.tgz"))


def test_cli_save_write_rejects_invalid_config_and_leaves_file_unchanged(tmp_path, capsys) -> None:
    config_path = tmp_path / "invalid.lua"
    original = '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''
    config_path.write_text(original, encoding="utf-8")

    exit_code = main(["save", "--config", str(config_path), "--write"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot save invalid config" in captured.out
    assert "EXCLUDE: rule must include d: or c:: g:half_left" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_save_preview_rejects_invalid_config_and_leaves_file_unchanged(tmp_path, capsys) -> None:
    config_path = tmp_path / "invalid.lua"
    original = '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''
    config_path.write_text(original, encoding="utf-8")

    exit_code = main(["save", "--config", str(config_path)])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "cannot preview invalid config" in captured.out
    assert "EXCLUDE: rule must include d: or c:: g:half_left" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_save_write_reports_save_failure_and_leaves_file_unchanged(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")
    backup_dir = tmp_path / "not-a-directory"
    backup_dir.write_text("blocks backup directory creation", encoding="utf-8")

    exit_code = main(
        [
            "save",
            "--config",
            str(config_path),
            "--backup-dir",
            str(backup_dir),
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "could not save config" in captured.out
    assert config_path.read_text(encoding="utf-8") == original


def test_cli_add_geom_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "custom_left",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "Planned GEOM add: custom_left" in captured.out
    assert "Geometry: x=10 y=20 w=300 h=400" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_cli_add_geom_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "custom_left",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.bak.tgz"))

    assert exit_code == 0
    assert "OK: GEOM profile added: custom_left" in captured.out
    assert "Backup archive:" in captured.out
    assert "custom_left" in saved
    assert backups
    members = list_backup_members(backups[0])
    assert extract_backup_member_text(backups[0], members[-1]) == original


def test_cli_add_geom_rejects_duplicate(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "half_left",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
            "--write",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "geometry profile already exists: half_left" in captured.out
    assert "Use modify-geom" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_geom_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "modify-geom",
            "--config",
            str(config_path),
            "--name",
            "half_left",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned GEOM modify: half_left" in captured.out
    assert "Geometry: x=10 y=20 w=300 h=400" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_geom_write_updates_existing_profile(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main(
        [
            "modify-geom",
            "--config",
            str(config_path),
            "--name",
            "half_left",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
            "--write",
        ]
    )

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: GEOM profile modified: half_left" in captured.out
    assert "half_left" in saved
    assert "x = 10" in saved
    assert "y = 20" in saved
    assert "w = 300" in saved
    assert "h = 400" in saved


def test_cli_modify_geom_rejects_missing_profile(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "modify-geom",
            "--config",
            str(config_path),
            "--name",
            "not_there",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "geometry profile not found: not_there" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_delete_geom_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "throwaway",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
            "--write",
        ]
    )
    with_added = config_path.read_text(encoding="utf-8")

    exit_code = main(["delete-geom", "--config", str(config_path), "--name", "throwaway"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned GEOM delete: throwaway" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == with_added
    assert with_added != original


def test_cli_delete_geom_write_removes_unused_profile(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "throwaway",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "300",
            "--h",
            "400",
            "--write",
        ]
    )

    exit_code = main(["delete-geom", "--config", str(config_path), "--name", "throwaway", "--write"])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: GEOM profile deleted: throwaway" in captured.out
    assert "throwaway" not in saved


def test_cli_delete_geom_rejects_profile_used_by_placement_rule(tmp_path, capsys) -> None:
    config_path = tmp_path / "d2wc.lua"
    original = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {}
'''
    config_path.write_text(original, encoding="utf-8")

    exit_code = main(["delete-geom", "--config", str(config_path), "--name", "half_left", "--write"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "still used by WORKSPACE_PLACEMENT: half_left" in captured.out
    assert "Remove or change the WORKSPACE_PLACEMENT rule" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_add_geom_rejects_invalid_profile(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main(
        [
            "add-geom",
            "--config",
            str(config_path),
            "--name",
            "tiny",
            "--x",
            "10",
            "--y",
            "20",
            "--w",
            "9",
            "--h",
            "400",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "width must be at least 10" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
