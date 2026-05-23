from datetime import datetime
from pathlib import Path

import pytest

from d2wc.core.saving import (
    SaveConfigError,
    SaveValidationError,
    create_backup,
    preview_save_config,
    preview_source_save_config,
    save_rendered_config,
    save_source_config,
)
from d2wc.core.backup import extract_backup_member_text, list_backup_members


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_current_config(tmp_path: Path) -> Path:
    source = REPO_ROOT / "src" / "d2wc.lua"
    target = tmp_path / "d2wc.lua"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_preview_save_config_reports_paths_without_writing(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    preview = preview_save_config(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert preview.config_path == config_path
    assert preview.backup_path == tmp_path / "d2wc.lua.bak.tgz"
    assert preview.bytes_written > 0
    assert preview.validation.ok
    assert config_path.read_text(encoding="utf-8") == original
    assert not preview.backup_path.exists()
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_preview_source_save_config_reports_paths_without_writing(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")
    edited_source = original.replace("local GEOM = {", "local GEOM = {\n  smoke_test             = { x = 1   , y = 2   , w = 300 , h = 400  },", 1)

    preview = preview_source_save_config(
        config_path,
        edited_source,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert preview.config_path == config_path
    assert preview.backup_path == tmp_path / "d2wc.lua.bak.tgz"
    assert preview.bytes_written == len(edited_source.encode("utf-8"))
    assert preview.validation.ok
    assert config_path.read_text(encoding="utf-8") == original
    assert not preview.backup_path.exists()
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_preview_save_config_uses_explicit_backup_directory_without_creating_it(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    backup_dir = tmp_path / "backups"

    preview = preview_save_config(
        config_path,
        backup_dir=backup_dir,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert preview.backup_path == backup_dir / "d2wc.lua.bak.tgz"
    assert not backup_dir.exists()


def test_preview_save_config_rejects_invalid_config_without_backup_or_write(tmp_path: Path) -> None:
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

    with pytest.raises(SaveValidationError):
        preview_save_config(
            config_path,
            when=datetime(2026, 5, 20, 15, 30, 0),
        )

    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
    assert not list(tmp_path.glob("*.tmp"))


def test_create_backup_copies_config_without_modifying_original(tmp_path: Path) -> None:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text("original", encoding="utf-8")

    backup_path, backup_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert backup_path == tmp_path / "d2wc.lua.bak.tgz"
    assert backup_member == "d2wc.lua.2026-05-20-153000.bak"
    assert extract_backup_member_text(backup_path, backup_member) == "original"
    assert config_path.read_text(encoding="utf-8") == "original"


def test_create_backup_does_not_overwrite_existing_backup(tmp_path: Path) -> None:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text("current", encoding="utf-8")
    first_path, first_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )
    config_path.write_text("current-2", encoding="utf-8")
    backup_path, backup_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 1),
    )
    assert first_path == backup_path
    assert first_member == "d2wc.lua.2026-05-20-153000.bak"
    assert backup_member == "d2wc.lua.2026-05-20-153001.bak"
    assert list_backup_members(backup_path) == [first_member, backup_member]


def test_create_backup_uses_suffix_for_duplicate_member_name(tmp_path: Path) -> None:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text("current", encoding="utf-8")

    first_path, first_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )
    second_path, second_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert first_path == second_path
    assert first_member == "d2wc.lua.2026-05-20-153000.bak"
    assert second_member == "d2wc.lua.2026-05-20-153000.bak.1"
    assert list_backup_members(first_path) == [first_member, second_member]


def test_create_backup_fsyncs_backup_file_and_directory(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text("original", encoding="utf-8")
    fsync_calls: list[int] = []

    def record_fsync(fd: int) -> None:
        fsync_calls.append(fd)

    monkeypatch.setattr("d2wc.core.saving.os.fsync", record_fsync)

    backup_path, backup_member = create_backup(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert backup_path.exists()
    assert len(fsync_calls) >= 2


def test_save_rendered_config_writes_rendered_output_and_creates_backup(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    result = save_rendered_config(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    saved = config_path.read_text(encoding="utf-8")

    assert result.config_path == config_path
    assert result.backup_path == tmp_path / "d2wc.lua.bak.tgz"
    assert extract_backup_member_text(result.backup_path, result.backup_member) == original
    assert result.validation.ok
    assert result.bytes_written == len(saved.encode("utf-8"))
    assert 'local EXCLUDE = {' in saved
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_save_source_config_writes_supplied_source_and_creates_backup(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")
    edited_source = original.replace("local GEOM = {", "local GEOM = {\n  smoke_test             = { x = 1   , y = 2   , w = 300 , h = 400  },", 1)

    result = save_source_config(
        config_path,
        edited_source,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    saved = config_path.read_text(encoding="utf-8")

    assert result.config_path == config_path
    assert result.backup_path == tmp_path / "d2wc.lua.bak.tgz"
    assert extract_backup_member_text(result.backup_path, result.backup_member) == original
    assert result.validation.ok
    assert result.bytes_written == len(saved.encode("utf-8"))
    assert "smoke_test" in saved
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))


def test_save_rendered_config_fsyncs_staged_backup_and_target_directory(tmp_path: Path, monkeypatch) -> None:
    config_path = copy_current_config(tmp_path)
    fsync_calls: list[int] = []

    def record_fsync(fd: int) -> None:
        fsync_calls.append(fd)

    monkeypatch.setattr("d2wc.core.saving.os.fsync", record_fsync)

    result = save_rendered_config(
        config_path,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert result.validation.ok
    assert len(fsync_calls) >= 4


def test_save_rendered_config_can_write_backup_to_explicit_directory(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    backup_dir = tmp_path / "backups"

    result = save_rendered_config(
        config_path,
        backup_dir=backup_dir,
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert result.backup_path == backup_dir / "d2wc.lua.bak.tgz"
    assert result.backup_path.exists()
    assert config_path.exists()


def test_save_rendered_config_rejects_invalid_original_without_backup_or_write(tmp_path: Path) -> None:
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

    with pytest.raises(SaveValidationError):
        save_rendered_config(
            config_path,
            when=datetime(2026, 5, 20, 15, 30, 0),
        )

    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))
    assert not list(tmp_path.glob("*.tmp"))


def test_save_rendered_config_reports_missing_config(tmp_path: Path) -> None:
    config_path = tmp_path / "missing.lua"

    with pytest.raises(SaveConfigError, match="config file not found"):
        save_rendered_config(config_path)


def test_save_rendered_config_leaves_original_if_backup_fails(tmp_path: Path) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")
    backup_dir = tmp_path / "not-a-directory"
    backup_dir.write_text("blocks backup directory creation", encoding="utf-8")

    with pytest.raises(FileExistsError):
        save_rendered_config(
            config_path,
            backup_dir=backup_dir,
            when=datetime(2026, 5, 20, 15, 30, 0),
        )

    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob(".d2wc.lua.*.tmp"))
