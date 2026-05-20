"""Safe save helpers for rendered Lua configuration.

This module contains the first real write path for d2wc. It is intentionally
core-only at this stage: tests exercise it with temporary directories, and no
user-facing CLI save command is exposed yet.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from d2wc.core.backup import build_backup_path
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class SaveConfigError(RuntimeError):
    """Raised when a config cannot be safely saved."""


class SaveValidationError(SaveConfigError):
    """Raised when staged rendered content fails validation."""

    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        super().__init__("rendered Lua config is not valid")


@dataclass(frozen=True)
class SaveResult:
    """Result of a successful safe save."""

    config_path: Path
    backup_path: Path
    bytes_written: int
    validation: ValidationResult


def save_rendered_config(
    config_path: Path,
    backup_dir: Path | None = None,
    when: datetime | None = None,
) -> SaveResult:
    """Render, validate, back up, and replace a Lua config file safely.

    The target file is replaced only after all of these steps succeed:

    1. Read the original config.
    2. Render and validate managed blocks in memory.
    3. Write rendered content to a temporary file in the target directory.
    4. Validate the staged temporary file.
    5. Create a timestamped backup of the original file.
    6. Atomically replace the target with the staged file.

    Tests must use temporary directories. The CLI does not expose this as a
    real user-config write path yet.
    """

    config_path = Path(config_path)
    backup_dir = Path(backup_dir) if backup_dir is not None else None
    staged_path: Path | None = None

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

    try:
        staged_path = _write_staged_file(config_path, rendered.source)
        staged_validation = _validate_file(staged_path)
        if not staged_validation.ok:
            raise SaveValidationError(staged_validation)

        backup_path = create_backup(config_path, backup_dir=backup_dir, when=when)
        os.replace(staged_path, config_path)
        staged_path = None
    except Exception:
        if staged_path is not None:
            staged_path.unlink(missing_ok=True)
        raise

    return SaveResult(
        config_path=config_path,
        backup_path=backup_path,
        bytes_written=len(rendered.source.encode("utf-8")),
        validation=staged_validation,
    )


def create_backup(config_path: Path, backup_dir: Path | None = None, when: datetime | None = None) -> Path:
    """Create a non-overwriting timestamped backup and return its path."""

    config_path = Path(config_path)
    base_backup_path = build_backup_path(config_path, backup_dir=backup_dir, when=when)
    backup_path = _next_available_path(base_backup_path)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, backup_path)
    return backup_path


def _write_staged_file(config_path: Path, rendered_source: str) -> Path:
    config_dir = config_path.parent
    config_dir.mkdir(parents=True, exist_ok=True)

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
            staged_file.flush()
            os.fsync(staged_file.fileno())
    except Exception:
        staged_path.unlink(missing_ok=True)
        raise

    return staged_path


def _validate_file(path: Path) -> ValidationResult:
    text = path.read_text(encoding="utf-8")
    parsed = ManagedBlockParser().parse(text)
    return validate_managed_blocks(parsed.blocks)


def _next_available_path(path: Path) -> Path:
    if not path.exists():
        return path

    for index in range(1, 1000):
        candidate = path.with_name(f"{path.name}.{index}")
        if not candidate.exists():
            return candidate

    raise SaveConfigError(f"could not find available backup path for {path}")
