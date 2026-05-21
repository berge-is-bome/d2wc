from pathlib import Path

from d2wc.cli import main
from d2wc.core.rendering import render_source


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
    assert "Planned backup:" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert "Run again with --write to save." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))
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
    planned_backup_lines = [line for line in output_lines if line.startswith("Planned backup: ")]

    assert exit_code == 0
    assert len(planned_backup_lines) == 1
    planned_backup = planned_backup_lines[0].removeprefix("Planned backup: ")
    assert planned_backup.startswith(str(backup_dir / "d2wc.lua."))
    assert planned_backup.endswith(".bak")
    assert not backup_dir.exists()


def test_cli_save_write_saves_config_and_prints_backup_path(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main(["save", "--config", str(config_path), "--write"])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "OK: config saved." in captured.out
    assert "Backup:" in captured.out
    assert list(tmp_path.glob("d2wc.lua.*.bak"))


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
    assert list(backup_dir.glob("d2wc.lua.*.bak"))


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
    assert not list(tmp_path.glob("*.bak"))


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
    assert not list(tmp_path.glob("*.bak"))


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
