"""GEOM profile editing operations."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import GeometryProfile, ManagedConfig, extract_managed_config, render_managed_config
from d2wc.core.rendering import RenderValidationError
from d2wc.core.rule_grammar import RuleParseError, parse_prefixed_rule
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class GeometryOperationError(ValueError):
    """Raised when a geometry edit cannot be applied."""


class GeometryProfileExistsError(GeometryOperationError):
    """Raised when adding a duplicate geometry profile."""


class GeometryProfileNotFoundError(GeometryOperationError):
    """Raised when modifying or deleting a missing geometry profile."""


class GeometryProfileInUseError(GeometryOperationError):
    """Raised when deleting a GEOM profile still used by placement rules."""


@dataclass(frozen=True)
class GeometryEditResult:
    """Result of applying a GEOM add or modify operation in memory."""

    source: str
    validation: ValidationResult
    profile: GeometryProfile
    operation: str


@dataclass(frozen=True)
class GeometryDeleteResult:
    """Result of applying a GEOM delete operation in memory."""

    source: str
    validation: ValidationResult
    profile_name: str


def add_geometry_profile_to_source(source: str, profile: GeometryProfile) -> GeometryEditResult:
    """Add one new GEOM profile to Lua source and return rendered source."""

    _validate_requested_profile(profile)
    parsed, config = _parse_valid_config(source)
    updated_profiles = _add_profile(config.geom, profile)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_profiles)

    return GeometryEditResult(
        source=rendered_source,
        validation=rendered_validation,
        profile=_normalize_profile(profile),
        operation="add",
    )


def modify_geometry_profile_in_source(source: str, profile: GeometryProfile) -> GeometryEditResult:
    """Modify one existing GEOM profile in Lua source and return rendered source."""

    _validate_requested_profile(profile)
    parsed, config = _parse_valid_config(source)
    updated_profiles = _modify_profile(config.geom, profile)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_profiles)

    return GeometryEditResult(
        source=rendered_source,
        validation=rendered_validation,
        profile=_normalize_profile(profile),
        operation="modify",
    )


def delete_geometry_profile_from_source(source: str, profile_name: str) -> GeometryDeleteResult:
    """Delete one unused GEOM profile from Lua source and return rendered source."""

    normalized_name = profile_name.lower()
    if not _is_lua_identifier(normalized_name):
        raise GeometryOperationError(f"invalid geometry profile name: {profile_name}")

    parsed, config = _parse_valid_config(source)
    _ensure_profile_not_used(config.workspace_placement, normalized_name)
    updated_profiles = _delete_profile(config.geom, normalized_name)
    rendered_source, rendered_validation = _render_updated_source(source, parsed.blocks, config, updated_profiles)

    return GeometryDeleteResult(
        source=rendered_source,
        validation=rendered_validation,
        profile_name=normalized_name,
    )


def _parse_valid_config(source: str):
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return parsed, extract_managed_config(parsed.blocks)


def _render_updated_source(
    source: str,
    blocks: dict[str, object],
    config: ManagedConfig,
    updated_profiles: tuple[GeometryProfile, ...],
) -> tuple[str, ValidationResult]:
    updated_config = ManagedConfig(
        exclude=config.exclude,
        pin=config.pin,
        workspace_routes=config.workspace_routes,
        geom=updated_profiles,
        workspace_placement=config.workspace_placement,
        left_edge_correction=config.left_edge_correction,
    )

    rendered_blocks = render_managed_config(updated_config, blocks)
    rendered_source = _replace_managed_blocks(source, blocks, rendered_blocks)

    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    rendered_validation = validate_managed_blocks(rendered_parsed.blocks)
    if not rendered_validation.ok:
        raise RenderValidationError(rendered_validation)

    return rendered_source, rendered_validation


def _add_profile(profiles: tuple[GeometryProfile, ...], profile: GeometryProfile) -> tuple[GeometryProfile, ...]:
    normalized_profile = _normalize_profile(profile)
    if any(existing.name == normalized_profile.name for existing in profiles):
        raise GeometryProfileExistsError(f"geometry profile already exists: {normalized_profile.name}")
    return (*profiles, normalized_profile)


def _modify_profile(profiles: tuple[GeometryProfile, ...], profile: GeometryProfile) -> tuple[GeometryProfile, ...]:
    normalized_profile = _normalize_profile(profile)
    updated: list[GeometryProfile] = []
    found = False

    for existing in profiles:
        if existing.name == normalized_profile.name:
            updated.append(normalized_profile)
            found = True
        else:
            updated.append(existing)

    if not found:
        raise GeometryProfileNotFoundError(f"geometry profile not found: {normalized_profile.name}")

    return tuple(updated)


def _delete_profile(profiles: tuple[GeometryProfile, ...], profile_name: str) -> tuple[GeometryProfile, ...]:
    updated = tuple(profile for profile in profiles if profile.name != profile_name)
    if len(updated) == len(profiles):
        raise GeometryProfileNotFoundError(f"geometry profile not found: {profile_name}")
    return updated


def _ensure_profile_not_used(placement_rules: tuple[str, ...], profile_name: str) -> None:
    for rule_text in placement_rules:
        try:
            rule = parse_prefixed_rule(rule_text)
        except RuleParseError:
            continue
        if rule.geometry_profile == profile_name:
            raise GeometryProfileInUseError(f"geometry profile is still used by WORKSPACE_PLACEMENT: {profile_name}")


def _normalize_profile(profile: GeometryProfile) -> GeometryProfile:
    return GeometryProfile(
        name=profile.name.lower(),
        x=profile.x,
        y=profile.y,
        w=profile.w,
        h=profile.h,
    )


def _validate_requested_profile(profile: GeometryProfile) -> None:
    if not _is_lua_identifier(profile.name):
        raise GeometryOperationError(f"invalid geometry profile name: {profile.name}")

    if profile.w < 10:
        raise GeometryOperationError("geometry profile width must be at least 10")
    if profile.h < 10:
        raise GeometryOperationError("geometry profile height must be at least 10")


def _replace_managed_blocks(source: str, blocks: dict[str, object], replacements: dict[str, str]) -> str:
    rendered = source
    for name in reversed(MANAGED_BLOCK_NAMES):
        block = blocks[name]
        replacement = replacements[name]
        rendered = rendered[: block.start_index] + replacement + rendered[block.end_index :]
    return rendered


def _is_lua_identifier(value: str) -> bool:
    return bool(value) and not value[0].isdigit() and value.replace("_", "").isalnum()
