"""Safe save helpers for rendered Lua configuration.

This module contains the first real write path for d2wc. Tests exercise it with
temporary directories, and the CLI exposes it only through an explicit --write
flag.
"""

from __future__ import annotations

import os
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, TextIO

from d2wc.core.backup import build_backup_paths
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class SaveConfigError(RuntimeError):
    """Raised when a config cannot be safely saved."""


class SaveValidationError(SaveConfigError):
    """Raised when rendered content fails validation."""

    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        super().__init__("rendered Lua config is not valid")


@dataclass(frozen=True)
class SavePreview:
    """Preview of a safe save without writing files."""

    config_path: Path
    backup_path: Path
    backup_member: str
    bytes_written: int
    validation: ValidationResult


@dataclass(frozen=True)
class SaveResult:
    """Result of a successful safe save."""

    config_path: Path
    backup_path: Path
    backup_member: str
    bytes_written: int
    validation: ValidationResult


def preview_save_config(
    config_path: Path,
    backup_dir: Path | None = None,
    when: datetime | None = None,
) -> SavePreview:
    """Render and validate a Lua config, but do not write anything."""

    config_path = Path(config_path)

    try:
        original_source = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SaveConfigError(f"config file not found: {config_path}") from exc
    except OSError as exc:
        raise SaveConfigError(f"could not read config file {config_path}: {exc}") from exc

    try:
        rendered = render_source(original_source)
    except RenderValidationError as exc:
        raise SaveValidationError(exc.validation) from exc

    return preview_source_save_config(
        config_path,
        rendered.source,
        backup_dir=backup_dir,
        when=when,
        validation=rendered.validation,
    )


def preview_source_save_config(
    config_path: Path,
    rendered_source: str,
    backup_dir: Path | None = None,
    when: datetime | None = None,
    validation: ValidationResult | None = None,
) -> SavePreview:
    """Preview saving already-rendered Lua source without writing files."""

    config_path = Path(config_path)
    backup_dir = Path(backup_dir) if backup_dir is not None else None

    if not config_path.exists():
        raise SaveConfigError(f"config file not found: {config_path}")

    source_validation = validation or _validate_source(rendered_source)
    if not source_validation.ok:
        raise SaveValidationError(source_validation)

    backup_path, backup_member = build_backup_paths(config_path, backup_dir=backup_dir, when=when)

    return SavePreview(
        config_path=config_path,
        backup_path=backup_path,
        backup_member=backup_member,
        bytes_written=len(rendered_source.encode("utf-8")),
        validation=source_validation,
    )


def save_rendered_config(
    config_path: Path,
    backup_dir: Path | None = None,
    when: datetime | None = None,
) -> SaveResult:
    """Render, validate, back up, and replace a Lua config file safely."""

    config_path = Path(config_path)

    try:
        original_source = config_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise SaveConfigError(f"config file not found: {config_path}") from exc
    except OSError as exc:
        raise SaveConfigError(f"could not read config file {config_path}: {exc}") from exc

    try:
        rendered = render_source(original_source)
    except RenderValidationError as exc:
        raise SaveValidationError(exc.validation) from exc

    return save_source_config(
        config_path,
        rendered.source,
        backup_dir=backup_dir,
        when=when,
        validation=rendered.validation,
    )


def save_source_config(
    config_path: Path,
    rendered_source: str,
    backup_dir: Path | None = None,
    when: datetime | None = None,
    validation: ValidationResult | None = None,
) -> SaveResult:
    """Validate, back up, and replace a config with supplied rendered source.

    The target file is replaced only after all of these steps succeed:

    1. Validate the supplied rendered source in memory.
    2. Write rendered content to a temporary file in the target directory.
    3. fsync the temporary file.
    4. Validate the staged temporary file.
    5. Create a timestamped backup of the original file.
    6. fsync the backup file and backup directory.
    7. Atomically replace the target with the staged file.
    8. fsync the target directory.

    Tests must use temporary directories. The CLI requires --write before this
    function is called from a user-facing command.
    """

    config_path = Path(config_path)
    backup_dir = Path(backup_dir) if backup_dir is not None else None
    staged_path: Path | None = None

    if not config_path.exists():
        raise SaveConfigError(f"config file not found: {config_path}")

    source_validation = validation or _validate_source(rendered_source)
    if not source_validation.ok:
        raise SaveValidationError(source_validation)

    try:
        staged_path = _write_staged_file(config_path, rendered_source)
        staged_validation = _validate_file(staged_path)
        if not staged_validation.ok:
            raise SaveValidationError(staged_validation)

        backup_path, backup_member = create_backup(config_path, backup_dir=backup_dir, when=when)
        os.replace(staged_path, config_path)
        staged_path = None
        _fsync_directory(config_path.parent)
    except Exception:
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)
        raise

    return SaveResult(
        config_path=config_path,
        backup_path=backup_path,
        backup_member=backup_member,
        bytes_written=len(rendered_source.encode("utf-8")),
        validation=staged_validation,
    )


def create_backup(config_path: Path, backup_dir: Path | None = None, when: datetime | None = None) -> tuple[Path, str]:
    """Create or update a backup archive and return archive path and member name."""

    config_path = Path(config_path)
    archive_path, backup_member = build_backup_paths(config_path, backup_dir=backup_dir, when=when)
    _ensure_directory(archive_path.parent)
    staged_archive_path: Path | None = None

    try:
        fd, staged_name = tempfile.mkstemp(prefix=f".{archive_path.name}.", suffix=".tmp", dir=archive_path.parent)
        os.close(fd)
        staged_archive_path = Path(staged_name)
        with tarfile.open(staged_archive_path, mode="w:gz") as new_tar:
            if archive_path.exists():
                with tarfile.open(archive_path, mode="r:gz") as old_tar:
                    for member in old_tar.getmembers():
                        if not member.isfile():
                            continue
                        member_stream = old_tar.extractfile(member)
                        if member_stream is None:
                            continue
                        new_tar.addfile(member, member_stream)
            tar_info = tarfile.TarInfo(name=backup_member)
            tar_info.size = config_path.stat().st_size
            with config_path.open("rb") as source_file:
                new_tar.addfile(tar_info, source_file)
        with staged_archive_path.open("rb") as staged_archive:
            _fsync_file(staged_archive)
        os.replace(staged_archive_path, archive_path)
        staged_archive_path = None
    except Exception:
        if staged_archive_path is not None:
            staged_archive_path.unlink(missing_ok=True)
        raise

    _fsync_directory(archive_path.parent)
    return archive_path, backup_member


def _write_staged_file(config_path: Path, rendered_source: str) -> Path:
    config_dir = config_path.parent
    _ensure_directory(config_dir)

    fd, staged_name = tempfile.mkstemp(
        prefix=f".{config_path.name}.",
        suffix=".tmp",
        dir=config_dir,
        text=True,
    )
    staged_path = Path(staged_name)

    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as staged_file:
            staged_file.write(rendered_source)
            _fsync_file(staged_file)
    except Exception:
        staged_path.unlink(missing_ok=True)
        raise

    return staged_path


def _validate_file(path: Path) -> ValidationResult:
    text = path.read_text(encoding="utf-8")
    return _validate_source(text)


def _validate_source(text: str) -> ValidationResult:
    parsed = ManagedBlockParser().parse(text)
    return validate_managed_blocks(parsed.blocks)


def _ensure_directory(directory: Path) -> None:
    existed = directory.exists()
    directory.mkdir(parents=True, exist_ok=True)
    if not existed:
        _fsync_directory(directory.parent)


def _fsync_file(file_obj: BinaryIO | TextIO) -> None:
    file_obj.flush()
    os.fsync(file_obj.fileno())


def _fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY

    fd = os.open(directory, flags)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)

