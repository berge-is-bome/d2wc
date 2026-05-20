"""Validation for managed d2wc configuration.

The first scaffold validates only that all managed blocks were detected.
Detailed rule grammar validation will follow after the parser has tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlock


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for managed configuration data."""

    ok: bool
    messages: tuple[str, ...] = field(default_factory=tuple)


def validate_managed_blocks(blocks: dict[str, ManagedBlock]) -> ValidationResult:
    """Validate that required managed blocks were detected.

    This function is intentionally minimal for the first core proof. It gives
    the CLI a safe read-only validation path while more specific validators are
    added.
    """

    messages: list[str] = []

    for name in MANAGED_BLOCK_NAMES:
        if name not in blocks:
            messages.append(f"Missing managed block: {name}")

    return ValidationResult(ok=not messages, messages=tuple(messages))
