from pathlib import Path

from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.validation import ValidationResult, validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_validation_result_messages_aliases_errors() -> None:
    result = ValidationResult(ok=False, errors=("error one",), warnings=("warning one",))

    assert result.messages == ("error one",)


def test_current_lua_validates_without_errors() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")
    parsed = ManagedBlockParser().parse(source)

    result = validate_managed_blocks(parsed.blocks)

    assert result.ok
    assert result.errors == ()


def test_shadowed_rules_are_warnings_not_errors() -> None:
    source = '''
local EXCLUDE = { "d:personal", "d:personal c:okular" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''
    parsed = ManagedBlockParser().parse(source)

    result = validate_managed_blocks(parsed.blocks)

    assert result.ok
    assert result.errors == ()
    assert result.warnings == (
        "EXCLUDE: exact rule d:personal c:okular overrides broader d:personal",
    )


def test_route_and_placement_overrides_are_not_warnings() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = { [1] = { "d:personal" }, [2] = { "d:personal c:navigator" } }
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 }, half_right = { x = 20, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = { "c:okular g:half_right", "d:personal c:okular g:half_left" }
local LEFT_EDGE_CORRECTION = {}
'''
    parsed = ManagedBlockParser().parse(source)

    result = validate_managed_blocks(parsed.blocks)

    assert result.ok
    assert result.errors == ()
    assert result.warnings == ()


def test_validation_errors_still_fail_validation() -> None:
    source = '''
local EXCLUDE = { "g:half_left" }
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''
    parsed = ManagedBlockParser().parse(source)

    result = validate_managed_blocks(parsed.blocks)

    assert not result.ok
    assert "EXCLUDE: rule must include d: or c:: g:half_left" in result.errors
