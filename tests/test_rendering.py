from pathlib import Path

import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_render_source_preserves_comments_and_formats_managed_blocks() -> None:
    source = '''before
local EXCLUDE = {
  -- user note
  "d:personal", -- personal note
}
between
local PIN = {
  "c:okular",
}
local WORKSPACE_ROUTES = {
  -- route note
  [1] = { "d:personal" },
}
local GEOM = {
  -- geometry note
  half_left = { x = 0, y = 0, w = 10, h = 10 }, -- left note
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {
  "c:okular le:pos1",
}
after
'''

    result = render_source(source)

    assert result.validation.ok
    assert "before\n" in result.source
    assert "\nbetween\n" in result.source
    assert "\nafter\n" in result.source
    assert 'local EXCLUDE = {\n  -- user note\n  "d:personal", -- personal note\n}' in result.source
    assert 'local PIN = {\n  "c:okular",\n}' in result.source
    assert 'local WORKSPACE_ROUTES = {\n  -- route note\n  [1] = { "d:personal" },\n}' in result.source
    assert 'local GEOM = {\n  -- geometry note\n  half_left              = { x = 0   , y = 0   , w = 10  , h = 10   },     -- left note\n}' in result.source
    assert 'local WORKSPACE_PLACEMENT = {\n  "c:okular g:half_left",\n}' in result.source
    assert 'local LEFT_EDGE_CORRECTION = {\n  "c:okular le:pos1",\n}' in result.source


def test_render_source_keeps_add_more_marker_last_in_rule_lists() -> None:
    source = '''
local EXCLUDE = {
  -- add more here
  "d:personal",
}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 10, h = 10 },
}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = render_source(source)

    assert result.validation.ok
    exclude_lines = _managed_block_lines(result.source, "EXCLUDE")
    assert '  "d:personal",' in exclude_lines
    assert exclude_lines[-2].strip() == "-- add more here"


def test_render_source_round_trips_current_lua_through_parser_and_validator() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    rendered = render_source(source).source
    parsed_again = ManagedBlockParser().parse(rendered)
    validation_again = validate_managed_blocks(parsed_again.blocks)

    assert validation_again.ok
    assert validation_again.errors == ()


def test_render_source_rejects_invalid_config() -> None:
    source = '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    with pytest.raises(RenderValidationError) as exc_info:
        render_source(source)

    assert "EXCLUDE: rule must include d: or c:: g:half_left" in exc_info.value.validation.errors


def _managed_block_lines(source: str, name: str) -> list[str]:
    lines = source.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == f"local {name} = {{")
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == "}":
            return lines[start : end + 1]
    raise AssertionError(f"block not found: {name}")
