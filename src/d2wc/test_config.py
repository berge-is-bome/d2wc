"""Helpers for the dedicated d2wc UI test configuration file."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import ManagedConfig, extract_managed_config
from d2wc.core.validation import ValidationResult, validate_managed_blocks

TEST_CONFIG_RELATIVE_PATH = Path(".config/devilspie2/d2wc-test.lua")
BUNDLED_CONFIG_PATH = Path(__file__).resolve().parents[1] / "d2wc.lua"


@dataclass(frozen=True)
class TestConfigPrepareResult:
    """Result of preparing the dedicated test config file."""

    path: Path
    source_path: Path
    created: bool
    replaced: bool
    skipped: bool
    message: str


@dataclass(frozen=True)
class ManagedSectionSummary:
    """Display summary for one managed Lua configuration section."""

    name: str
    entries: tuple[str, ...]
    display_text: str


@dataclass(frozen=True)
class TestConfigSnapshot:
    """Read-only parsed view of the dedicated test config file."""

    path: Path
    exists: bool
    validation: ValidationResult | None = None
    config: ManagedConfig | None = None
    sections: tuple[ManagedSectionSummary, ...] = ()
    error: str | None = None

    @property
    def ok(self) -> bool:
        """Return whether the test config exists and validates."""

        return self.exists and self.validation is not None and self.validation.ok and self.config is not None


def default_test_config_path() -> Path:
    """Return the fixed user-local d2wc UI test config path."""

    return Path.home() / TEST_CONFIG_RELATIVE_PATH


def prepare_test_config(
    target_path: Path | None = None,
    *,
    source_path: Path = BUNDLED_CONFIG_PATH,
    replace: bool = False,
) -> TestConfigPrepareResult:
    """Copy the bundled Lua config to the dedicated test config path.

    This is intentionally scoped to the test file and does not modify the user's
    real Devilspie2 configuration.
    """

    target = target_path or default_test_config_path()
    if target.exists() and not replace:
        return TestConfigPrepareResult(
            path=target,
            source_path=source_path,
            created=False,
            replaced=False,
            skipped=True,
            message="test config already exists; pass replace=True to refresh it",
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, target)
    return TestConfigPrepareResult(
        path=target,
        source_path=source_path,
        created=not replace,
        replaced=replace,
        skipped=False,
        message="test config replaced" if replace else "test config created",
    )


def load_test_config_snapshot(path: Path | None = None) -> TestConfigSnapshot:
    """Load and validate the dedicated test config without changing it."""

    config_path = path or default_test_config_path()
    if not config_path.exists():
        return TestConfigSnapshot(
            path=config_path,
            exists=False,
            error="test config does not exist yet",
        )

    try:
        source = config_path.read_text(encoding="utf-8")
        parse_result = ManagedBlockParser().parse(source)
        validation = validate_managed_blocks(parse_result.blocks)
        config = extract_managed_config(parse_result.blocks) if validation.ok else None
    except (OSError, ValueError, TypeError) as exc:
        return TestConfigSnapshot(
            path=config_path,
            exists=True,
            error=f"could not load test config: {exc}",
        )

    return TestConfigSnapshot(
        path=config_path,
        exists=True,
        validation=validation,
        config=config,
        sections=_section_summaries(config) if config is not None else (),
    )


def format_test_config_status(snapshot: TestConfigSnapshot | None) -> str:
    """Format the test config status for the GTK UI."""

    if snapshot is None:
        return "Test config: not loaded"

    lines = [f"Test config: {snapshot.path}"]
    if not snapshot.exists:
        lines.append("Status: missing")
        lines.append("Use --init-test-config to create it from src/d2wc.lua.")
        return "\n".join(lines)

    if snapshot.error:
        lines.append("Status: error")
        lines.append(snapshot.error)
        return "\n".join(lines)

    if snapshot.validation is None:
        lines.append("Status: unknown")
        return "\n".join(lines)

    if snapshot.validation.ok:
        lines.append("Status: valid")
    else:
        lines.append("Status: invalid")
        lines.extend(f"- {error}" for error in snapshot.validation.errors)

    if snapshot.validation.warnings:
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in snapshot.validation.warnings)

    return "\n".join(lines)


def format_prepare_result(result: TestConfigPrepareResult | None) -> str:
    """Format the prepare/reset result for GTK display."""

    if result is None:
        return "Prepare result: none"
    return "\n".join(
        [
            f"Prepare result: {result.message}",
            f"Target: {result.path}",
            f"Source: {result.source_path}",
        ]
    )


def _section_summaries(config: ManagedConfig) -> tuple[ManagedSectionSummary, ...]:
    section_entries: dict[str, tuple[str, ...]] = {
        "EXCLUDE": config.exclude,
        "PIN": config.pin,
        "WORKSPACE_ROUTES": tuple(
            f"workspace {route.workspace}: {', '.join(route.rules) if route.rules else '(empty)'}"
            for route in config.workspace_routes
        ),
        "GEOM": tuple(
            f"{profile.name}: x={profile.x} y={profile.y} w={profile.w} h={profile.h}"
            for profile in config.geom
        ),
        "WORKSPACE_PLACEMENT": config.workspace_placement,
        "LEFT_EDGE_CORRECTION": config.left_edge_correction,
    }

    return tuple(
        ManagedSectionSummary(
            name=name,
            entries=section_entries.get(name, ()),
            display_text=_format_section_entries(section_entries.get(name, ())),
        )
        for name in MANAGED_BLOCK_NAMES
    )


def _format_section_entries(entries: tuple[str, ...]) -> str:
    if not entries:
        return "(empty)"
    return "\n".join(f"- {entry}" for entry in entries)
