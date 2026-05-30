"""Managed Lua block parsing.

This module starts with conservative block detection only. It does not attempt to
execute Lua and it does not write files.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

LEGACY_MANAGED_MARKER = "d2wc managed"
MANAGED_ASSIGNMENT_PATTERN = re.compile(
    r"(?m)^\s*local\s+D2WC_MANAGED\s*=\s*true\s*(?:--.*)?$"
)

MANAGED_BLOCK_NAMES: tuple[str, ...] = (
    "EXCLUDE",
    "PIN",
    "WORKSPACE_ROUTES",
    "GEOM",
    "WORKSPACE_PLACEMENT",
    "LEFT_EDGE_CORRECTION",
)


@dataclass(frozen=True)
class ManagedBlock:
    """A detected managed Lua block."""

    name: str
    start_index: int
    end_index: int
    text: str


@dataclass(frozen=True)
class ParseResult:
    """Result of scanning a Lua file for managed blocks."""

    blocks: dict[str, ManagedBlock]
    source: str


def is_d2wc_managed_source(source: str) -> bool:
    """Return whether source is marked as a d2wc managed Lua file."""

    return bool(MANAGED_ASSIGNMENT_PATTERN.search(source)) or LEGACY_MANAGED_MARKER in source


class ManagedBlockParser:
    """Find managed `local NAME = { ... }` blocks in the Lua source.

    This first scaffold intentionally performs only balanced-brace block
    detection. Full rule parsing will be added after the block boundaries are
    covered by tests.
    """

    def parse(self, source: str) -> ParseResult:
        blocks: dict[str, ManagedBlock] = {}
        for name in MANAGED_BLOCK_NAMES:
            blocks[name] = self._find_block(source, name)
        return ParseResult(blocks=blocks, source=source)

    def _find_block(self, source: str, name: str) -> ManagedBlock:
        marker = f"local {name} ="
        marker_index = source.find(marker)
        if marker_index == -1:
            raise ValueError(f"managed block not found: {name}")

        open_brace_index = source.find("{", marker_index)
        if open_brace_index == -1:
            raise ValueError(f"managed block has no opening brace: {name}")

        close_brace_index = self._find_matching_brace(source, open_brace_index)
        block_end = close_brace_index + 1
        return ManagedBlock(
            name=name,
            start_index=marker_index,
            end_index=block_end,
            text=source[marker_index:block_end],
        )

    @staticmethod
    def _find_matching_brace(source: str, open_brace_index: int) -> int:
        depth = 0
        in_string: str | None = None
        escaped = False

        for index in range(open_brace_index, len(source)):
            char = source[index]

            if in_string is not None:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == in_string:
                    in_string = None
                continue

            if char in {'"', "'"}:
                in_string = char
                continue

            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    return index

        raise ValueError("managed block has no matching closing brace")
