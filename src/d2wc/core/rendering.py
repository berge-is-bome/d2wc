"""Rendering helpers for managed Lua configuration.

The renderer is still dry-run only. It validates the managed blocks and returns
new source text without writing files.
"""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser
from d2wc.core.managed_config import extract_managed_config, render_managed_config
from d2wc.core.validation import ValidationResult, validate_managed_blocks


class RenderValidationError(ValueError):
    """Raised when rendering is requested for invalid managed Lua config."""

    def __init__(self, validation: ValidationResult) -> None:
        self.validation = validation
        super().__init__("managed Lua config is not valid")


@dataclass(frozen=True)
class RenderResult:
    """Result of a dry-run render."""

    source: str
    validation: ValidationResult


def render_source(source: str) -> RenderResult:
    """Validate and render a Lua source string without writing files."""

    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)

    config = extract_managed_config(parsed.blocks)
    rendered_blocks = render_managed_config(config)
    rendered_source = _replace_managed_blocks(source, parsed.blocks, rendered_blocks)

    rendered_parsed = ManagedBlockParser().parse(rendered_source)
    rendered_validation = validate_managed_blocks(rendered_parsed.blocks)
    if not rendered_validation.ok:
        raise RenderValidationError(rendered_validation)

    return RenderResult(source=rendered_source, validation=rendered_validation)


def _replace_managed_blocks(source: str, blocks: dict[str, object], replacements: dict[str, str]) -> str:
    rendered = source
    for name in reversed(MANAGED_BLOCK_NAMES):
        block = blocks[name]
        replacement = replacements[name]
        rendered = rendered[: block.start_index] + replacement + rendered[block.end_index :]
    return rendered
