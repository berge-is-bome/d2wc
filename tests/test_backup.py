from datetime import datetime
from pathlib import Path

import pytest

from d2wc.core.backup import build_backup_paths, extract_backup_member_text


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
