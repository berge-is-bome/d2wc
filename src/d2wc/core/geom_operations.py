"""GEOM profile editing operations."""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import GeometryProfile, ManagedConfig, extract_managed_config, render_managed_config
from d2wc.core.rendering import RenderValidationError, RenderResult
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class GeometryOperationError(ValueError):
    """Raised when a geometry edit cannot be applied."""


class GeometryProfileExistsError(GeometryOperationError):
    """Raised when adding a duplicate geometry profile without replacement."""


@dataclass(frozen=True)
class GeometryEditResult:
    """Result of applying a GEOM edit in memory."""

    source: str
    validation: ValidationResult
    profile: GeometryProfile
    replaced: bool


def add_geometry_profile_to_source(
    source: str,
    profile: GeometryProfile,
    replace: bool = False,
) -> GeometryEditResult:
    """Add one GEOM profile to Lua source and return rendered source.

    The edit is in-memory only. Callers that want to save must use the safe-save
    path after previewing or validating the generated source.
    """

    _validate_requested_profile(profile)

    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)

    config = extract_managed_config(parsed.blocks)
    updated_profiles, replaced = _add_or_replace_profile(config.geom, profile, replace=replace)
    updated_config = ManagedConfig(
        exclude=config.exclude,
        pin=config.pin,
        workspace_routes=config.workspace_routes,
        geom=updated_profiles,
        workspace_placement=config.workspace_placement,
        left_edge_correction=config.left_edge_correction,
    )

    rendered_blocks = render_managed_config(updated_config, parsed.blocks)
    rendered_source = _replace_managed_blocks(source, parsed.blocks, rendered_blocks)

    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    rendered_validation = validate_managed_blocks(rendered_parsed.blocks)
    if not rendered_validation.ok:
        raise RenderValidationError(rendered_validation)

    return GeometryEditResult(
        source=rendered_source,
        validation=rendered_validation,
        profile=profile,
        replaced=replaced,
    )


def _add_or_replace_profile(
    profiles: tuple[GeometryProfile, ...],
    profile: GeometryProfile,
    replace: bool,
) -> tuple[tuple[GeometryProfile, ...], bool]:
    profile_name = profile.name.lower()
    normalized_profile = GeometryProfile(
        name=profile_name,
        x=profile.x,
        y=profile.y,
        w=profile.w,
        h=profile.h,
    )

    updated: list[GeometryProfile] = []
    replaced = False

    for existing in profiles:
        if existing.name == profile_name:
            if not replace:
                raise GeometryProfileExistsError(f"geometry profile already exists: {profile_name}")
            updated.append(normalized_profile)
            replaced = True
        else:
            updated.append(existing)

    if not replaced:
        updated.append(normalized_profile)

    return tuple(updated), replaced


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
