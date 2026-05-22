import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.route_operations import (
    RouteOperationError,
    RouteRuleExistsError,
    RouteRuleNotFoundError,
    add_route_rule_to_source,
    delete_route_rule_from_source,
    modify_route_rule_in_source,
)
from d2wc.core.validation import validate_managed_blocks


def test_add_route_rule_appends_to_existing_workspace_and_preserves_notes() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  -- route note
  [1] = { "d:personal", }, -- workspace one
  -- add more here
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = add_route_rule_to_source(source, 1, "C:NAVIGATOR D:WORK")

    assert result.validation.ok
    assert result.workspace == 1
    assert result.rule == "d:work c:navigator"
    assert "-- route note" in result.source
    assert "-- workspace one" in result.source
    assert '[1] = { "d:personal", "d:work c:navigator", },' in result.source
    assert _managed_block_lines(result.source, "WORKSPACE_ROUTES")[-2].strip() == "-- add more here"

    parsed = ManagedBlockParser().parse(result.source)
    assert validate_managed_blocks(parsed.blocks).ok


def test_add_route_rule_adds_new_workspace_before_add_more_marker() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", },
  -- add more here
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_route_rule_to_source(source, 3, "d:work c:krusader")
    route_lines = _managed_block_lines(result.source, "WORKSPACE_ROUTES")

    assert route_lines[-3] == '  [3] = { "d:work c:krusader", },'
    assert route_lines[-2].strip() == "-- add more here"


def test_add_route_rule_orders_workspace_rows_and_inserts_blank_lines() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [3] = { "d:work", },

  [4] = { "d:test", },
  -- add more here
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_route_rule_to_source(source, 1, "d:personal")

    assert _managed_block_lines(result.source, "WORKSPACE_ROUTES") == [
        "local WORKSPACE_ROUTES = {",
        '  [1] = { "d:personal", },',
        "",
        '  [3] = { "d:work", },',
        "",
        '  [4] = { "d:test", },',
        "  -- add more here",
        "}",
    ]


def test_add_route_rule_preserves_multiline_route_closing_comment() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = {
    "d:personal",
  }, -- workspace one

  [3] = { "d:work", },
  -- add more here
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_route_rule_to_source(source, 2, "d:test")

    assert _managed_block_lines(result.source, "WORKSPACE_ROUTES") == [
        "local WORKSPACE_ROUTES = {",
        '  [1] = { "d:personal", }, -- workspace one',
        "",
        '  [2] = { "d:test", },',
        "",
        '  [3] = { "d:work", },',
        "  -- add more here",
        "}",
    ]


def test_add_route_rule_preserves_standalone_comment_after_existing_route() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", },
  -- workspace one note

  [3] = { "d:work", },
  -- add more here
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_route_rule_to_source(source, 2, "d:test")

    assert _managed_block_lines(result.source, "WORKSPACE_ROUTES") == [
        "local WORKSPACE_ROUTES = {",
        '  [1] = { "d:personal", },',
        "  -- workspace one note",
        "",
        '  [2] = { "d:test", },',
        "",
        '  [3] = { "d:work", },',
        "  -- add more here",
        "}",
    ]


def test_add_route_rule_allows_shadowed_domain_class_target() -> None:
    result = add_route_rule_to_source(_minimal_source(), 3, "d:personal c:krusader")

    assert result.validation.ok
    assert '[1] = { "d:personal", "d:work", },' in result.source
    assert '[3] = { "d:personal c:krusader", },' in result.source


def test_add_route_rule_rejects_duplicate_target_across_workspaces() -> None:
    with pytest.raises(RouteRuleExistsError, match="route rule already exists for target: d:personal"):
        add_route_rule_to_source(_minimal_source(), 2, "d:personal")


def test_add_route_rule_rejects_invalid_route_rule() -> None:
    with pytest.raises(RouteOperationError, match="route rule must include d: or c:"):
        add_route_rule_to_source(_minimal_source(), 2, "g:half_left")

    with pytest.raises(RouteOperationError, match="route rule must not include g:"):
        add_route_rule_to_source(_minimal_source(), 2, "d:work g:half_left")


def test_modify_route_rule_moves_rule_to_existing_workspace() -> None:
    result = modify_route_rule_in_source(_minimal_source(), "d:personal", 2, "d:personal c:krusader")

    assert result.validation.ok
    assert result.old_workspace == 1
    assert result.new_workspace == 2
    assert '[1] = { "d:work", },' in result.source
    assert '[2] = { "d:personal c:navigator", "d:personal c:krusader", },' in result.source


def test_modify_route_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "c:navigator d:work", },
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = modify_route_rule_in_source(source, "d:work c:navigator", 1, "d:work c:krusader")

    assert result.validation.ok
    assert '"c:navigator d:work"' not in result.source
    assert '"d:work c:krusader",' in result.source


def test_modify_route_rule_rejects_missing_and_duplicate_rules() -> None:
    with pytest.raises(RouteRuleNotFoundError, match="route rule not found: d:missing"):
        modify_route_rule_in_source(_minimal_source(), "d:missing", 2, "d:missing c:navigator")

    with pytest.raises(RouteRuleExistsError, match="route rule already exists for target: d:work"):
        modify_route_rule_in_source(_minimal_source(), "d:personal", 1, "d:work")

    with pytest.raises(RouteRuleExistsError, match="route rule already exists for target: d:personal c:navigator"):
        modify_route_rule_in_source(_minimal_source(), "d:personal", 2, "d:personal c:navigator")


def test_delete_route_rule_removes_rule_and_preserves_notes() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  -- route note
  [1] = { "d:personal", "d:work", }, -- workspace one
  [2] = { "d:test", }, -- keep workspace two
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = delete_route_rule_from_source(source, "d:personal")

    assert result.validation.ok
    assert "-- route note" in result.source
    assert '[1] = { "d:work", }, -- workspace one' in result.source
    assert '[2] = { "d:test", }, -- keep workspace two' in result.source
    assert '"d:personal"' not in result.source


def test_delete_route_rule_removes_empty_workspace_bucket() -> None:
    result = delete_route_rule_from_source(_minimal_source(), "d:personal")
    assert '[1] = { "d:work", },' in result.source

    result = delete_route_rule_from_source(result.source, "d:work")
    assert result.validation.ok
    assert "[1]" not in result.source
    assert '[2] = { "d:personal c:navigator", },' in result.source


def test_delete_route_rule_rejects_missing_rule() -> None:
    with pytest.raises(RouteRuleNotFoundError, match="route rule not found: d:missing"):
        delete_route_rule_from_source(_minimal_source(), "d:missing")


def _minimal_source() -> str:
    return '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", "d:work", },
  [2] = { "d:personal c:navigator", },
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''


def _managed_block_lines(source: str, name: str) -> list[str]:
    lines = source.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == f"local {name} = {{")
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == "}":
            return lines[start : end + 1]
    raise AssertionError(f"block not found: {name}")
