"""Helpers for user-managed d2wc Lua configuration files."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from d2wc.core.saving import SaveConfigError, SaveValidationError, save_source_config
from d2wc.core.user_paths import (
    default_managed_config_dir,
    default_managed_config_path,
    devilspie2_entry_path,
    is_safe_managed_filename,
    symlink_points_to_managed_dir,
)
from d2wc.test_config import (
    TestConfigActionResult,
    TestConfigSnapshot,
    format_action_result,
    load_test_config_snapshot,
)

ManagedConfigSnapshot = TestConfigSnapshot
ManagedConfigActionResult = TestConfigActionResult
format_managed_action_result = format_action_result


@dataclass(frozen=True)
class ManagedFileResult:
    """Result of a managed-config file operation."""

    ok: bool
    path: Path | None = None
    message: str = ""


@dataclass(frozen=True)
class ActivationResult:
    """Result of updating the Devilspie2-facing symlink."""

    ok: bool
    entry_path: Path
    target_path: Path
    message: str


def load_managed_config_snapshot(path: Path | None = None) -> ManagedConfigSnapshot:
    """Load and validate a d2wc managed Lua file."""

    return load_test_config_snapshot(path or default_managed_config_path())


def managed_config_status_text(snapshot: ManagedConfigSnapshot | None) -> str:
    """Format a concise status line for the active managed config."""

    if snapshot is None:
        return "Managed config: not loaded"

    status = f"Managed config: {snapshot.path}"
    if not snapshot.exists:
        return f"{status}\nStatus: missing"
    if snapshot.error:
        return f"{status}\nStatus: error\n{snapshot.error}"
    if snapshot.validation is not None and snapshot.validation.ok:
        return f"{status}\nStatus: valid"
    if snapshot.validation is not None:
        errors = "\n".join(f"- {error}" for error in snapshot.validation.errors)
        return f"{status}\nStatus: invalid\n{errors}"
    return f"{status}\nStatus: unknown"


def save_managed_config_as(source_path: Path, target_path: Path, *, replace: bool = False) -> ManagedFileResult:
    """Save one managed Lua file as another managed Lua file."""

    source = Path(source_path)
    target = Path(target_path)
    managed_dir = default_managed_config_dir()

    if not is_safe_managed_filename(target.name):
        return ManagedFileResult(
            ok=False,
            path=target,
            message="filename must be non-empty, end with .lua, and not contain / or ..",
        )

    if not _same_directory(target.parent, managed_dir):
        return ManagedFileResult(
            ok=False,
            path=target,
            message=f"managed configs must be saved under {managed_dir}",
        )

    snapshot = load_managed_config_snapshot(source)
    if not snapshot.ok or snapshot.validation is None:
        return ManagedFileResult(
            ok=False,
            path=source,
            message="source is not a valid d2wc-managed Lua file",
        )

    try:
        source_text = source.read_text(encoding="utf-8")
    except OSError as exc:
        return ManagedFileResult(ok=False, path=source, message=f"could not read source: {exc}")

    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not replace:
            return ManagedFileResult(ok=False, path=target, message=f"target already exists: {target}")
        try:
            save_source_config(target, source_text, validation=snapshot.validation)
        except (OSError, SaveConfigError, SaveValidationError) as exc:
            return ManagedFileResult(ok=False, path=target, message=str(exc))
    else:
        try:
            target.write_text(source_text, encoding="utf-8")
        except OSError as exc:
            return ManagedFileResult(ok=False, path=target, message=f"could not write target: {exc}")

    target_snapshot = load_managed_config_snapshot(target)
    if not target_snapshot.ok:
        return ManagedFileResult(ok=False, path=target, message="saved target is not a valid d2wc-managed Lua file")

    return ManagedFileResult(ok=True, path=target, message=f"Saved managed config as: {target}")


def copy_default_managed_config_if_missing() -> ManagedFileResult:
    """Create the default managed config from the bundled template if missing."""

    target = default_managed_config_path()
    if target.exists():
        return ManagedFileResult(ok=True, path=target, message=f"Managed config exists: {target}")

    source = Path(__file__).resolve().parents[1] / "d2wc.lua"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copyfile(source, target)
    except OSError as exc:
        return ManagedFileResult(ok=False, path=target, message=f"could not create managed config: {exc}")

    snapshot = load_managed_config_snapshot(target)
    if not snapshot.ok:
        return ManagedFileResult(ok=False, path=target, message="created managed config is not valid")

    return ManagedFileResult(ok=True, path=target, message=f"Created managed config: {target}")


def activate_managed_config(managed_path: Path) -> ActivationResult:
    """Point Devilspie2 at the selected managed config when the integration path is safe."""

    target = Path(managed_path)
    managed_dir = default_managed_config_dir()
    entry = devilspie2_entry_path()

    if not _is_within_directory(target, managed_dir):
        return ActivationResult(
            ok=False,
            entry_path=entry,
            target_path=target,
            message=f"not activating file outside managed config directory: {target}",
        )

    if not target.exists():
        return ActivationResult(
            ok=False,
            entry_path=entry,
            target_path=target,
            message=f"managed config does not exist: {target}",
        )

    entry.parent.mkdir(parents=True, exist_ok=True)
    if entry.is_symlink():
        if not symlink_points_to_managed_dir(entry, managed_dir):
            return ActivationResult(
                ok=False,
                entry_path=entry,
                target_path=target,
                message=f"leaving unrelated Devilspie2 symlink unchanged: {entry}",
            )
        entry.unlink()
    elif entry.exists():
        return ActivationResult(
            ok=False,
            entry_path=entry,
            target_path=target,
            message=f"leaving existing Devilspie2 file unchanged: {entry}",
        )

    entry.symlink_to(target)
    return ActivationResult(ok=True, entry_path=entry, target_path=target, message=f"Activated managed config: {entry} -> {target}")


def _same_directory(path: Path, directory: Path) -> bool:
    try:
        return path.resolve(strict=False) == directory.resolve(strict=False)
    except OSError:
        return False


def _is_within_directory(path: Path, directory: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(directory.resolve(strict=False))
    except (OSError, ValueError):
        return False
    return True
