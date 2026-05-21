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
from d2wc.core.shadow_validation import warn_shadowed_target_rules


@dataclass(frozen=True)
class ValidationResult:
    """Validation outcome for managed configuration data."""

    ok: bool
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)

    @property
    def messages(self) -> tuple[str, ...]:
        """Compatibility alias for blocking validation errors."""

        return self.errors


def validate_managed_blocks(blocks: dict[str, ManagedBlock]) -> ValidationResult:
    """Validate required managed blocks and first-layer rule grammar."""

    errors: list[str] = []
    warnings: list[str] = []

    for name in MANAGED_BLOCK_NAMES:
        if name not in blocks:
            errors.append(f"Missing managed block: {name}")

    if errors:
        return ValidationResult(ok=False, errors=tuple(errors), warnings=tuple(warnings))

    geometry_profiles = extract_geometry_profile_names(blocks["GEOM"].text)

    errors.extend(validate_target_section(blocks["EXCLUDE"]))
    errors.extend(validate_target_section(blocks["PIN"]))
    errors.extend(validate_workspace_routes_section(blocks["WORKSPACE_ROUTES"]))
    errors.extend(validate_geom_section(blocks["GEOM"]))
    errors.extend(validate_placement_section(blocks["WORKSPACE_PLACEMENT"], geometry_profiles))
    errors.extend(validate_left_edge_section(blocks["LEFT_EDGE_CORRECTION"]))

    warnings.extend(warn_shadowed_target_rules(blocks["EXCLUDE"]))
    warnings.extend(warn_shadowed_target_rules(blocks["PIN"]))
    warnings.extend(warn_shadowed_target_rules(blocks["WORKSPACE_ROUTES"]))
    warnings.extend(warn_shadowed_target_rules(blocks["LEFT_EDGE_CORRECTION"]))

    return ValidationResult(ok=not errors, errors=tuple(errors), warnings=tuple(warnings))
