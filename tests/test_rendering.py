from pathlib import Path

import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.rendering import RenderValidationError, render_source
from d2wc.core.validation import validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_render_source_returns_current_lua_unchanged_for_first_renderer_proof() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    result = render_source(source)

    assert result.validation.ok
    assert result.source == source


def test_render_source_round_trips_through_parser_and_validator() -> None:
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
