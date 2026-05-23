"""Backup helpers for safe config writes and archive restores."""

from __future__ import annotations

import tarfile
from datetime import datetime
from pathlib import Path


def build_backup_paths(
    config_path: Path,
    backup_dir: Path | None = None,
    when: datetime | None = None,
) -> tuple[Path, str]:
    """Return archive path and timestamped member name for a config backup.

    Args:
        config_path: The configuration file that would be backed up.
        backup_dir: Optional directory for the backup archive. Defaults to the config file's directory.
        when: Optional timestamp for deterministic tests.

    Returns:
        A tuple like (`d2wc.lua.bak.tgz`, `d2wc.lua.2026-05-20-153000.bak`).
    """

    timestamp = (when or datetime.now()).strftime("%Y-%m-%d-%H%M%S")
    destination_dir = backup_dir if backup_dir is not None else config_path.parent
    return destination_dir / f"{config_path.name}.bak.tgz", f"{config_path.name}.{timestamp}.bak"


def list_backup_members(archive_path: Path) -> list[str]:
    """List archived backup member names in the archive order."""

    with tarfile.open(archive_path, mode="r:gz") as tar:
        return [member.name for member in tar.getmembers() if member.isfile()]


def extract_backup_member_bytes(archive_path: Path, member_name: str) -> bytes:
    """Extract a named backup member as bytes."""

    _validate_member_name(member_name)
    with tarfile.open(archive_path, mode="r:gz") as tar:
        member = tar.getmember(member_name)
        if not member.isfile():
            raise ValueError(f"backup member is not a regular file: {member_name}")
        file_obj = tar.extractfile(member)
        if file_obj is None:
            raise ValueError(f"backup member is not readable: {member_name}")
        return file_obj.read()


def extract_backup_member_text(archive_path: Path, member_name: str, encoding: str = "utf-8") -> str:
    """Extract a named backup member as decoded text."""

    return extract_backup_member_bytes(archive_path, member_name).decode(encoding)


def _validate_member_name(member_name: str) -> None:
    member_path = Path(member_name)
    if member_path.is_absolute() or ".." in member_path.parts or "/" in member_name or "\\" in member_name:
        raise ValueError(f"unsafe backup member name: {member_name}")
