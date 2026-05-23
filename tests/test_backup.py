from datetime import datetime
from pathlib import Path
import io
import tarfile

import pytest

from d2wc.core.backup import build_backup_paths, extract_backup_member_text
from d2wc.core.backup import list_backup_members


def test_build_backup_path_defaults_to_config_directory() -> None:
    archive, member = build_backup_paths(
        Path("/tmp/d2wc/d2wc.lua"),
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert archive == Path("/tmp/d2wc/d2wc.lua.bak.tgz")
    assert member == "d2wc.lua.2026-05-20-153000.bak"


def test_build_backup_path_uses_explicit_backup_directory() -> None:
    archive, member = build_backup_paths(
        Path("/tmp/d2wc/d2wc.lua"),
        backup_dir=Path("/tmp/d2wc/backups"),
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert archive == Path("/tmp/d2wc/backups/d2wc.lua.bak.tgz")
    assert member == "d2wc.lua.2026-05-20-153000.bak"


def test_extract_backup_member_rejects_unsafe_member_name(tmp_path: Path) -> None:
    archive = tmp_path / "d2wc.lua.bak.tgz"
    archive.write_bytes(b"")
    with pytest.raises(ValueError, match="unsafe backup member name"):
        extract_backup_member_text(archive, "../evil")


def test_list_backup_members_skips_unsafe_member_names(tmp_path: Path) -> None:
    archive = tmp_path / "d2wc.lua.bak.tgz"
    with tarfile.open(archive, mode="w:gz") as tar:
        safe = tarfile.TarInfo("d2wc.lua.2026-05-20-153000.bak")
        safe_data = b"safe"
        safe.size = len(safe_data)
        tar.addfile(safe, io.BytesIO(safe_data))

        unsafe = tarfile.TarInfo("../escape.bak")
        unsafe_data = b"unsafe"
        unsafe.size = len(unsafe_data)
        tar.addfile(unsafe, io.BytesIO(unsafe_data))

    assert list_backup_members(archive) == ["d2wc.lua.2026-05-20-153000.bak"]
