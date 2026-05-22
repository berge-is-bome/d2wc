import pytest

from d2wc.core.left_edge_operations import (
    LeftEdgeOperationError,
    LeftEdgeRuleExistsError,
    LeftEdgeRuleNotFoundError,
    add_left_edge_rule_to_source,
    delete_left_edge_rule_from_source,
    modify_left_edge_rule_in_source,
)
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.validation import validate_managed_blocks


def test_add_left_edge_rule_appends_rule_and_preserves_comments() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  -- left-edge note
  "d:dom0 c:qubes-qube-manager le:pos1", -- manager note
}
after
'''

    result = add_left_edge_rule_to_source(source, "LE:POS2 C:OKULAR D:PERSONAL")

    assert result.validation.ok
    assert result.operation == "add"
    assert result.rule == "d:personal c:okular le:pos2"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- left-edge note" in result.source
    assert "-- manager note" in result.source
    assert '"d:personal c:okular le:pos2",' in result.source
    _assert_valid(result.source)


def test_add_left_edge_rule_keeps_add_more_marker_last() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  "d:dom0 c:qubes-qube-manager le:pos1",
  -- add more here
}
'''

    result = add_left_edge_rule_to_source(source, "d:personal c:okular le:pos2")

    lines = _managed_block_lines(result.source, "LEFT_EDGE_CORRECTION")
    assert '  "d:personal c:okular le:pos2",' in lines
    assert lines[-2].strip() == "-- add more here"
    assert "d:personal c:okular le:pos2" in lines[-3]


def test_add_left_edge_rule_normalizes_prefix_order_and_case() -> None:
    result = add_left_edge_rule_to_source(_minimal_source(), "LE:POS2 C:OKULAR D:PERSONAL")

    assert result.rule == "d:personal c:okular le:pos2"
    assert '"d:personal c:okular le:pos2",' in result.source


def test_add_left_edge_rule_rejects_duplicate_target() -> None:
    with pytest.raises(LeftEdgeRuleExistsError, match="left-edge rule already exists for target: d:dom0 c:qubes-qube-manager"):
        add_left_edge_rule_to_source(_minimal_source(), "d:dom0 c:qubes-qube-manager le:pos2")


def test_add_left_edge_rule_rejects_missing_target() -> None:
    with pytest.raises(LeftEdgeOperationError, match="left-edge rule must include d: or c:"):
        add_left_edge_rule_to_source(_minimal_source(), "le:pos1")


def test_add_left_edge_rule_rejects_missing_mode() -> None:
    with pytest.raises(LeftEdgeOperationError, match="left-edge rule must include le:"):
        add_left_edge_rule_to_source(_minimal_source(), "c:okular")


def test_add_left_edge_rule_rejects_geometry_profile_token() -> None:
    with pytest.raises(LeftEdgeOperationError, match="left-edge rule must not include g:"):
        add_left_edge_rule_to_source(_minimal_source(), "c:okular g:half_left le:pos1")


def test_add_left_edge_rule_rejects_invalid_mode() -> None:
    with pytest.raises(LeftEdgeOperationError, match="invalid left-edge mode"):
        add_left_edge_rule_to_source(_minimal_source(), "c:okular le:pos3")


def test_modify_left_edge_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  "le:pos1 c:qubes-qube-manager d:dom0",
}
'''

    result = modify_left_edge_rule_in_source(
        source,
        "d:dom0 c:qubes-qube-manager le:pos1",
        "d:dom0 c:qubes-qube-manager le:pos2",
    )

    assert result.validation.ok
    assert result.old_rule == "d:dom0 c:qubes-qube-manager le:pos1"
    assert result.new_rule == "d:dom0 c:qubes-qube-manager le:pos2"
    assert "le:pos1" not in result.source
    assert '"d:dom0 c:qubes-qube-manager le:pos2",' in result.source


def test_modify_left_edge_rule_rejects_missing_old_rule() -> None:
    with pytest.raises(LeftEdgeRuleNotFoundError, match="left-edge rule not found: c:missing le:pos1"):
        modify_left_edge_rule_in_source(_minimal_source(), "c:missing le:pos1", "c:missing le:pos2")


def test_modify_left_edge_rule_rejects_duplicate_new_target() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  "d:dom0 c:qubes-qube-manager le:pos1",
  "d:personal c:okular le:pos2",
}
'''

    with pytest.raises(LeftEdgeRuleExistsError, match="left-edge rule already exists for target: d:personal c:okular"):
        modify_left_edge_rule_in_source(
            source,
            "d:dom0 c:qubes-qube-manager le:pos1",
            "d:personal c:okular le:pos1",
        )


def test_delete_left_edge_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  "le:pos1 c:qubes-qube-manager d:dom0",
}
'''

    result = delete_left_edge_rule_from_source(source, "d:dom0 c:qubes-qube-manager le:pos1")

    assert result.validation.ok
    assert result.operation == "delete"
    assert result.rule == "d:dom0 c:qubes-qube-manager le:pos1"
    assert "qubes-qube-manager" not in result.source


def test_delete_left_edge_rule_preserves_notes_for_remaining_rules() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  -- left-edge note
  "d:dom0 c:qubes-qube-manager le:pos1", -- remove me
  "d:personal c:okular le:pos2", -- keep me
}
after
'''

    result = delete_left_edge_rule_from_source(source, "d:dom0 c:qubes-qube-manager le:pos1")

    assert result.validation.ok
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- left-edge note" in result.source
    assert "qubes-qube-manager" not in result.source
    assert "remove me" not in result.source
    assert '"d:personal c:okular le:pos2",' in result.source
    assert "-- keep me" in result.source


def test_delete_left_edge_rule_rejects_missing_rule() -> None:
    with pytest.raises(LeftEdgeRuleNotFoundError, match="left-edge rule not found: c:missing le:pos1"):
        delete_left_edge_rule_from_source(_minimal_source(), "c:missing le:pos1")


def _minimal_source() -> str:
    return '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {
  "d:dom0 c:qubes-qube-manager le:pos1",
}
'''


def _managed_block_lines(source: str, name: str) -> list[str]:
    lines = source.splitlines()
    start = next(index for index, line in enumerate(lines) if line.strip() == f"local {name} = {{")
    for end in range(start + 1, len(lines)):
        if lines[end].strip() == "}":
            return lines[start : end + 1]
    raise AssertionError(f"block not found: {name}")


def _assert_valid(source: str) -> None:
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    assert validation.ok
