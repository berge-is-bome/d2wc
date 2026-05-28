"""Persistent user settings for the d2wc configurator UI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from d2wc.core.user_paths import d2wc_config_dir

DEFAULT_TOAST_TIMEOUT_SECONDS = 5
DEFAULT_TOAST_OPACITY = 0.5
SETTINGS_FILENAME = "settings.json"


@dataclass(frozen=True)
class UiSettings:
    """User-configurable UI preferences."""

    toast_timeout_seconds: int = DEFAULT_TOAST_TIMEOUT_SECONDS
    toast_opacity: float = DEFAULT_TOAST_OPACITY


def ui_settings_path(home: Path | None = None) -> Path:
    """Return the persistent UI settings path."""

    return d2wc_config_dir(home) / SETTINGS_FILENAME


def load_ui_settings(path: Path | None = None) -> UiSettings:
    """Load UI settings, falling back safely to defaults."""

    settings_path = path or ui_settings_path()
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return UiSettings()

    if not isinstance(raw, dict):
        return UiSettings()

    return UiSettings(
        toast_timeout_seconds=_coerce_timeout(raw.get("toast_timeout_seconds")),
        toast_opacity=_coerce_opacity(raw.get("toast_opacity")),
    )


def save_ui_settings(settings: UiSettings, path: Path | None = None) -> None:
    """Persist UI settings."""

    settings_path = path or ui_settings_path()
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "toast_timeout_seconds": _coerce_timeout(settings.toast_timeout_seconds),
        "toast_opacity": _coerce_opacity(settings.toast_opacity),
    }
    tmp_path = settings_path.with_name(f".{settings_path.name}.tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp_path.replace(settings_path)


def _coerce_timeout(value: Any) -> int:
    try:
        timeout = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TOAST_TIMEOUT_SECONDS
    return min(max(timeout, 1), 60)


def _coerce_opacity(value: Any) -> float:
    try:
        opacity = float(value)
    except (TypeError, ValueError):
        return DEFAULT_TOAST_OPACITY
    return min(max(opacity, 0.1), 1.0)
