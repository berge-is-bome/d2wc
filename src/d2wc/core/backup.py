"""Backup helpers for safe config writes.

This module currently calculates backup paths only. It does not copy or write
files yet, which keeps the core proof read-only.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


def build_backup_path(config_path: Path, backup_dir: Path | None = None, when: datetime | None = None) -> Path:
    """Return a timestamped backup path for a config file.

    Args:
        config_path: The configuration file that would be backed up.
        backup_dir: Optional directory for the backup. Defaults to the config file's directory.
        when: Optional timestamp for deterministic tests.

    Returns:
        A path such as `d2wc.lua.2026-05-20-153000.bak` in the selected backup directory.
    """

    timestamp = (when or datetime.now()).strftime("%Y-%m-%d-%H%M%S")
    destination_dir = backup_dir if backup_dir is not None else config_path.parent
    return destination_dir / f"{config_path.name}.{timestamp}.bak"
