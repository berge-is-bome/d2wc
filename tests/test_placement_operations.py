from pathlib import Path

import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.placement_operations import (
    PlacementOperationError,
    PlacementRuleExistsError,
    PlacementRuleNotFoundError,
    add_placement_rule_to_source,
    delete_placement_rule_from_source,
    modify_placement_rule_in_source,
)
from d2wc.core.validation import validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_add_placement_rule_appends_rule_and_preserves_comments() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  -- placement note
  "c:okular g:half_left", -- okular note
}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = add_placement_rule_to_source(source, "d:personal c:navigator g:half_left")

    assert result.validation.ok
    assert result.operation == "add"
    assert result.rule == "d:personal c:navigator g:half_left"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- placement note" in result.source
    assert "-- okular note" in result.source
    assert '"d:personal c:navigator g:half_left",' in result.source

    parsed = ManagedBlockParser().parse(result.source)
    validation = validate_managed_blocks(parsed.blocks)
    assert validation.ok


def test_add_placement_rule_normalizes_prefix_order_and_case() -> None:
    source = _minimal_source()

    result = add_placement_rule_to_source(source, "G:HALF_LEFT C:NAVIGATOR D:PERSONAL")

    assert result.rule == "d:personal c:navigator g:half_left"
    assert '"d:personal c:navigator g:half_left",' in result.source


def test_add_placement_rule_keeps_add_more_marker_last() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
  -- add more here
}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_placement_rule_to_source(source, "d:personal c:navigator g:half_left")

    placement_lines = _managed_block_lines(result.source, "WORKSPACE_PLACEMENT")
    assert '  "d:personal c:navigator g:half_left",' in placement_lines
    assert placement_lines[-2].strip() == "-- add more here"
    assert "d:personal c:navigator" in placement_lines[-3]


def test_add_placement_rule_rejects_duplicate_target() -> None:
    source = _minimal_source()

    with pytest.raises(PlacementRuleExistsError, match="placement rule already exists for target: c:okular"):
        add_placement_rule_to_source(source, "c:okular g:half_left")


def test_add_placement_rule_rejects_missing_geometry_profile() -> None:
    source = _minimal_source()

    with pytest.raises(PlacementOperationError, match="geometry profile not found: not_there"):
        add_placement_rule_to_source(source, "c:navigator g:not_there")


def test_add_placement_rule_rejects_missing_target() -> None:
    source = _minimal_source()

    with pytest.raises(PlacementOperationError, match="placement rule must include d: or c:"):
        add_placement_rule_to_source(source, "g:half_left")


def test_modify_placement_rule_updates_exact_rule() -> None:
    source = _minimal_source()

    result = modify_placement_rule_in_source(source, "c:okular g:half_left", "c:okular g:centered")

    assert result.validation.ok
    assert result.old_rule == "c:okular g:half_left"
    assert result.new_rule == "c:okular g:centered"
    assert '"c:okular g:half_left"' not in result.source
    assert '"c:okular g:centered",' in result.source


def test_modify_placement_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
  centered = { x = 10, y = 20, w = 300, h = 400 },
}
local WORKSPACE_PLACEMENT = {
  "g:half_left c:okular",
}
local LEFT_EDGE_CORRECTION = {}
'''

    result = modify_placement_rule_in_source(source, "c:okular g:half_left", "g:centered c:okular")

    assert result.validation.ok
    assert result.new_rule == "c:okular g:centered"
    assert '"g:half_left c:okular"' not in result.source
    assert '"c:okular g:centered",' in result.source


def test_modify_placement_rule_rejects_missing_old_rule() -> None:
    source = _minimal_source()

    with pytest.raises(PlacementRuleNotFoundError, match="placement rule not found: c:missing g:half_left"):
        modify_placement_rule_in_source(source, "c:missing g:half_left", "c:missing g:centered")


def test_modify_placement_rule_rejects_duplicate_new_target() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
  centered = { x = 10, y = 20, w = 300, h = 400 },
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
  "c:navigator g:centered",
}
local LEFT_EDGE_CORRECTION = {}
'''

    with pytest.raises(PlacementRuleExistsError, match="placement rule already exists for target: c:navigator"):
        modify_placement_rule_in_source(source, "c:okular g:half_left", "c:navigator g:half_left")


def test_delete_placement_rule_removes_exact_rule_and_preserves_notes() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  -- placement note
  "c:okular g:half_left", -- remove me
  "c:navigator g:half_left", -- keep me
}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = delete_placement_rule_from_source(source, "c:okular g:half_left")

    assert result.validation.ok
    assert result.operation == "delete"
    assert result.rule == "c:okular g:half_left"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- placement note" in result.source
    assert "c:okular" not in result.source
    assert "remove me" not in result.source
    assert '"c:navigator g:half_left",' in result.source
    assert "-- keep me" in result.source


def test_delete_placement_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  "g:half_left c:okular",
}
local LEFT_EDGE_CORRECTION = {}
'''

    result = delete_placement_rule_from_source(source, "c:okular g:half_left")

    assert result.validation.ok
    assert "g:half_left c:okular" not in result.source
    assert "c:okular" not in result.source


def test_delete_placement_rule_rejects_missing_rule() -> None:
    source = _minimal_source()

    with pytest.raises(PlacementRuleNotFoundError, match="placement rule not found: c:missing g:half_left"):
        delete_placement_rule_from_source(source, "c:missing g:half_left")


def _minimal_source() -> str:
    return '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
  centered = { x = 10, y = 20, w = 300, h = 400 },
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {}
'''


def _managed_block_lines(source: str, name: str) -> list[str]:
    lines = source.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == f"local {name} = {{")
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == "}":
            return lines[start : end + 1]
    raise AssertionError(f"block not found: {name}")
