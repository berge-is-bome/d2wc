import pytest

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.target_rule_operations import (
    TargetRuleExistsError,
    TargetRuleNotFoundError,
    TargetRuleOperationError,
    add_exclude_rule_to_source,
    add_pin_rule_to_source,
    delete_exclude_rule_from_source,
    delete_pin_rule_from_source,
    modify_exclude_rule_in_source,
    modify_pin_rule_in_source,
)
from d2wc.core.validation import validate_managed_blocks


def test_add_pin_rule_appends_rule_and_preserves_comments() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {
  -- pin note
  "d:dom0 c:xfce4-terminal", -- terminal note
}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = add_pin_rule_to_source(source, "C:QUBES-QUBE-MANAGER D:DOM0")

    assert result.validation.ok
    assert result.section == "PIN"
    assert result.operation == "add"
    assert result.rule == "d:dom0 c:qubes-qube-manager"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- pin note" in result.source
    assert "-- terminal note" in result.source
    assert '"d:dom0 c:qubes-qube-manager",' in result.source
    _assert_valid(result.source)


def test_add_exclude_rule_appends_rule_and_preserves_comments() -> None:
    source = '''before
local EXCLUDE = {
  -- exclude note
  "d:personal-test", -- domain note
}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = add_exclude_rule_to_source(source, "c:qubes-app-menu")

    assert result.validation.ok
    assert result.section == "EXCLUDE"
    assert result.operation == "add"
    assert result.rule == "c:qubes-app-menu"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- exclude note" in result.source
    assert "-- domain note" in result.source
    assert '"c:qubes-app-menu",' in result.source
    _assert_valid(result.source)


def test_add_target_rule_keeps_add_more_marker_last() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {
  "d:dom0 c:xfce4-terminal",
  -- add more here
}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = add_pin_rule_to_source(source, "d:dom0 c:qubes-qube-manager")

    pin_lines = _managed_block_lines(result.source, "PIN")
    assert '  "d:dom0 c:qubes-qube-manager",' in pin_lines
    assert pin_lines[-2].strip() == "-- add more here"
    assert "qubes-qube-manager" in pin_lines[-3]


def test_add_target_rule_normalizes_prefix_order_and_case() -> None:
    result = add_pin_rule_to_source(_minimal_source(), "C:QUBES-QUBE-MANAGER D:DOM0")

    assert result.rule == "d:dom0 c:qubes-qube-manager"
    assert '"d:dom0 c:qubes-qube-manager",' in result.source


def test_add_target_rule_rejects_duplicate_target() -> None:
    with pytest.raises(TargetRuleExistsError, match="PIN rule already exists for target: d:dom0 c:xfce4-terminal"):
        add_pin_rule_to_source(_minimal_source(), "c:xfce4-terminal d:dom0")


def test_add_target_rule_rejects_missing_target() -> None:
    with pytest.raises(TargetRuleOperationError, match="PIN rule must include d: or c:"):
        add_pin_rule_to_source(_minimal_source(), "")


def test_add_target_rule_rejects_geometry_profile_token() -> None:
    with pytest.raises(TargetRuleOperationError, match="EXCLUDE rule must not include g:"):
        add_exclude_rule_to_source(_minimal_source(), "c:okular g:half_left")


def test_add_target_rule_rejects_left_edge_token() -> None:
    with pytest.raises(TargetRuleOperationError, match="PIN rule must not include le:"):
        add_pin_rule_to_source(_minimal_source(), "c:okular le:pos1")


def test_modify_pin_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {
  "c:xfce4-terminal d:dom0",
}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = modify_pin_rule_in_source(source, "d:dom0 c:xfce4-terminal", "c:qubes-qube-manager d:dom0")

    assert result.validation.ok
    assert result.old_rule == "d:dom0 c:xfce4-terminal"
    assert result.new_rule == "d:dom0 c:qubes-qube-manager"
    assert "xfce4-terminal" not in result.source
    assert '"d:dom0 c:qubes-qube-manager",' in result.source


def test_modify_exclude_rule_rejects_missing_old_rule() -> None:
    with pytest.raises(TargetRuleNotFoundError, match="EXCLUDE rule not found: c:missing"):
        modify_exclude_rule_in_source(_minimal_source(), "c:missing", "c:qubes-app-menu")


def test_modify_target_rule_rejects_duplicate_new_target() -> None:
    source = '''
local EXCLUDE = {
  "d:personal-test",
  "c:qubes-app-menu",
}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    with pytest.raises(TargetRuleExistsError, match="EXCLUDE rule already exists for target: c:qubes-app-menu"):
        modify_exclude_rule_in_source(source, "d:personal-test", "c:qubes-app-menu")


def test_delete_pin_rule_matches_noncanonical_stored_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {
  "c:xfce4-terminal d:dom0",
}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = delete_pin_rule_from_source(source, "d:dom0 c:xfce4-terminal")

    assert result.validation.ok
    assert result.operation == "delete"
    assert result.rule == "d:dom0 c:xfce4-terminal"
    assert "xfce4-terminal" not in result.source


def test_delete_exclude_rule_preserves_notes_for_remaining_rules() -> None:
    source = '''before
local EXCLUDE = {
  -- exclude note
  "d:personal-test", -- remove me
  "c:qubes-app-menu", -- keep me
}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = delete_exclude_rule_from_source(source, "d:personal-test")

    assert result.validation.ok
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "-- exclude note" in result.source
    assert "personal-test" not in result.source
    assert "remove me" not in result.source
    assert '"c:qubes-app-menu",' in result.source
    assert "-- keep me" in result.source


def test_delete_target_rule_rejects_missing_rule() -> None:
    with pytest.raises(TargetRuleNotFoundError, match="PIN rule not found: c:missing"):
        delete_pin_rule_from_source(_minimal_source(), "c:missing")


def _minimal_source() -> str:
    return '''
local EXCLUDE = {
  "d:personal-test",
}
local PIN = {
  "d:dom0 c:xfce4-terminal",
}
local WORKSPACE_ROUTES = {}
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


def _assert_valid(source: str) -> None:
    parsed = ManagedBlockParser().parse(source)
    validation = validate_managed_blocks(parsed.blocks)
    assert validation.ok
