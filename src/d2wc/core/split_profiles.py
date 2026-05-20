"""Generated split-profile helpers.

The formula is intentionally simple for the first scaffold and will be refined
with tests against real desktop geometry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Geometry:
    """Integer window geometry."""

    x: int
    y: int
    w: int
    h: int


@dataclass(frozen=True)
class SplitProfiles:
    """Generated half-left and half-right profiles."""

    half_left: Geometry
    half_right: Geometry


def generate_split_profiles(screen: Geometry, window_border_width: int = 0) -> SplitProfiles:
    """Generate basic half-left and half-right profiles.

    `window_border_width` accounts for visible border overlap/gap correction.
    The exact formula is a first-pass placeholder and must be validated against
    Qubes/XFCE behavior before becoming final.
    """

    if window_border_width < 0:
        raise ValueError("window_border_width must be zero or greater")
    if screen.w <= 0 or screen.h <= 0:
        raise ValueError("screen width and height must be positive")

    half_width = screen.w // 2
    adjusted_width = max(1, half_width + window_border_width)

    left = Geometry(
        x=screen.x,
        y=screen.y,
        w=adjusted_width,
        h=screen.h,
    )
    right = Geometry(
        x=screen.x + half_width - window_border_width,
        y=screen.y,
        w=adjusted_width,
        h=screen.h,
    )
    return SplitProfiles(half_left=left, half_right=right)
