"""User path helpers for managed config and installer integration."""

from __future__ import annotations

from pathlib import Path

MANAGED_CONFIG_FILENAME = "d2wc.lua"
MANAGED_CONFIG_RELATIVE_DIR = Path(".config/d2wc/lua")
DEVILSPIE2_RELATIVE_DIR = Path(".config/devilspie2")
DEVILSPIE2_ENTRY_FILENAME = "d2wc.lua"
MANAGED_FILE_HEADER_MARKER = "-- d2wc managed"


def default_managed_config_dir(home: Path | None = None) -> Path:
    root = Path.home() if home is None else home
    return root / MANAGED_CONFIG_RELATIVE_DIR


def default_managed_config_path(home: Path | None = None) -> Path:
    return default_managed_config_dir(home) / MANAGED_CONFIG_FILENAME


def devilspie2_entry_path(home: Path | None = None) -> Path:
    root = Path.home() if home is None else home
    return root / DEVILSPIE2_RELATIVE_DIR / DEVILSPIE2_ENTRY_FILENAME


def is_safe_managed_filename(name: str) -> bool:
    if not name or not name.endswith(".lua"):
        return False
    if "/" in name or ".." in name:
        return False
    return True


def is_d2wc_managed_lua_file(path: Path) -> bool:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return MANAGED_FILE_HEADER_MARKER in source


def is_safe_devilspie2_integration_target(path: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return True
    if path.is_symlink():
        return True
    if path.is_file() and is_d2wc_managed_lua_file(path):
        return True
    return False
