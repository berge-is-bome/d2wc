from datetime import datetime
from pathlib import Path

from d2wc.core.backup import build_backup_path


def test_build_backup_path_defaults_to_config_directory() -> None:
    backup = build_backup_path(
        Path("/tmp/d2wc/d2wc.lua"),
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert backup == Path("/tmp/d2wc/d2wc.lua.2026-05-20-153000.bak")


def test_build_backup_path_uses_explicit_backup_directory() -> None:
    backup = build_backup_path(
        Path("/tmp/d2wc/d2wc.lua"),
        backup_dir=Path("/tmp/d2wc/backups"),
        when=datetime(2026, 5, 20, 15, 30, 0),
    )

    assert backup == Path("/tmp/d2wc/backups/d2wc.lua.2026-05-20-153000.bak")
