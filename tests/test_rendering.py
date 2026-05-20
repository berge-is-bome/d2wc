from pathlib import Path

import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_render_source_canonicalizes_managed_blocks() -> None:
    source = '''before
local EXCLUDE = { "d:personal" }
between
local PIN = { "c:okular" }
local WORKSPACE_ROUTES = { [1] = { "d:personal" } }
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = { "c:okular g:half_left" }
local LEFT_EDGE_CORRECTION = { "c:okular le:pos1" }
after
'''

    result = render_source(source)

    assert result.validation.ok
    assert "before\n" in result.source
    assert "\nbetween\n" in result.source
    assert "\nafter\n" in result.source
    assert 'local EXCLUDE = {\n  "d:personal",\n}' in result.source
    assert 'local PIN = {\n  "c:okular",\n}' in result.source
    assert 'local WORKSPACE_ROUTES = {\n  [1] = { "d:personal", },\n}' in result.source
    assert 'local WORKSPACE_PLACEMENT = {\n  "c:okular g:half_left",\n}' in result.source
    assert 'local LEFT_EDGE_CORRECTION = {\n  "c:okular le:pos1",\n}' in result.source


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
