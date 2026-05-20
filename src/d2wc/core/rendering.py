"""Rendering helpers for managed Lua configuration.

Rendering is intentionally not implemented yet. This module exists so the first
package skeleton matches the documented architecture.
"""

from __future__ import annotations


class RenderingNotImplementedError(NotImplementedError):
    """Raised when rendering is requested before the renderer is implemented."""


def render_managed_blocks() -> str:
    """Render managed Lua blocks.

    Full rendering will be added after parser and validation tests exist.
    """

    raise RenderingNotImplementedError("managed block rendering is not implemented yet")
