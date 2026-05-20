"""Runtime settings model for d2wc."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RuntimeSettings:
    """Runtime settings that are not Lua rule strings."""

    lua_config_path: Path = Path("src/d2wc.lua")
    window_border_width: int = 0

    def validate(self) -> tuple[str, ...]:
        messages: list[str] = []

        if self.window_border_width < 0:
            messages.append("window_border_width must be zero or greater")

        return tuple(messages)
