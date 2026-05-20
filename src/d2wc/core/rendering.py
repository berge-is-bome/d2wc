"""Rendering helpers for managed Lua configuration.

The first renderer proof is deliberately conservative: it validates the managed
blocks and returns the original source unchanged. This establishes the safe
parse -> validate -> render -> parse -> validate path before canonical managed
block formatting or file writing is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from d2wc.core.lua_blocks import ManagedBlockParser
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
    """Validate and render a Lua source string without writing files.

    This first implementation returns the original source unchanged. Later
    renderer stages will replace managed blocks with deterministic canonical
    formatting after the formatter has its own tests.
    """

    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    if not validation.ok:
        raise RenderValidationError(validation)
    return RenderResult(source=source, validation=validation)
