from d2wc.core.lua_blocks import ManagedBlock, ManagedBlockParser
from d2wc.core.shadow_validation import warn_shadowed_target_rules
from d2wc.core.validation import validate_managed_blocks


def block(name: str, text: str) -> ManagedBlock:
    return ManagedBlock(name=name, start_index=0, end_index=len(text), text=text)


def test_warns_when_exact_rule_overrides_domain_wide_rule() -> None:
    warnings = warn_shadowed_target_rules(
        block("PIN", 'local PIN = { "d:personal", "d:personal c:okular" }')
    )

    assert warnings == [
        "PIN: exact rule d:personal c:okular overrides broader d:personal"
    ]


def test_warns_when_exact_rule_overrides_class_wide_rule() -> None:
    warnings = warn_shadowed_target_rules(
        block("WORKSPACE_PLACEMENT", 'local WORKSPACE_PLACEMENT = { "c:okular g:half_right", "d:personal c:okular g:half_left" }')
    )

    assert warnings == [
        "WORKSPACE_PLACEMENT: exact rule d:personal c:okular overrides broader c:okular"
    ]


def test_warns_when_exact_rule_overrides_domain_and_class_wide_rules() -> None:
    warnings = warn_shadowed_target_rules(
        block("EXCLUDE", 'local EXCLUDE = { "d:personal", "c:okular", "d:personal c:okular" }')
    )

    assert warnings == [
        "EXCLUDE: exact rule d:personal c:okular overrides broader d:personal",
        "EXCLUDE: exact rule d:personal c:okular overrides broader c:okular",
    ]


def test_exact_duplicate_workspace_route_target_is_error_not_warning() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {
  [1] = { "d:personal", },
  [2] = { "d:personal", },
}
local GEOM = {}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    parsed = ManagedBlockParser().parse(source)
    result = validate_managed_blocks(parsed.blocks)

    assert not result.ok
    assert result.errors == ("WORKSPACE_ROUTES: duplicate route target: d:personal",)
    assert result.warnings == ()


def test_no_warning_for_unrelated_rules() -> None:
    warnings = warn_shadowed_target_rules(
        block("PIN", 'local PIN = { "d:personal", "c:okular", "d:work c:terminal" }')
    )

    assert warnings == []
