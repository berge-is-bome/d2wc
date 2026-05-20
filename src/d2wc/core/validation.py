"""Validation for managed d2wc configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlock
from d2wc.core.section_validation import (
    extract_geometry_profile_names,
    validate_geom_section,
    validate_left_edge_section,
    validate_placement_section,
    validate_target_section,
    validate_workspace_routes_section,
)


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for managed configuration data."""

    ok: bool
    messages: tuple[str, ...] = field(default_factory=tuple)


def validate_managed_blocks(blocks: dict[str, ManagedBlock]) -> ValidationResult:
    """Validate required managed blocks and first-layer rule grammar."""

    messages: list[str] = []

    for name in MANAGED_BLOCK_NAMES:
        if name not in blocks:
            messages.append(f"Missing managed block: {name}")

    if messages:
        return ValidationResult(ok=False, messages=tuple(messages))

    geometry_profiles = extract_geometry_profile_names(blocks["GEOM"].text)

    messages.extend(validate_target_section(blocks["EXCLUDE"]))
    messages.extend(validate_target_section(blocks["PIN"]))
    messages.extend(validate_workspace_routes_section(blocks["WORKSPACE_ROUTES"]))
    messages.extend(validate_geom_section(blocks["GEOM"]))
    messages.extend(validate_placement_section(blocks["WORKSPACE_PLACEMENT"], geometry_profiles))
    messages.extend(validate_left_edge_section(blocks["LEFT_EDGE_CORRECTION"]))

    return ValidationResult(ok=not messages, messages=tuple(messages))
