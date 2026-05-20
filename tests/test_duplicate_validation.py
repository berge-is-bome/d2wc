from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.section_validation import (
    validate_geom_section,
    validate_left_edge_section,
    validate_placement_section,
    validate_target_section,
    validate_workspace_routes_section,
)


def block(name: str, text: str) -> ManagedBlock:
    return ManagedBlock(name=name, start_index=0, end_index=len(text), text=text)


def test_target_sections_reject_duplicate_targets() -> None:
    messages = validate_target_section(
        block("PIN", 'local PIN = { "d:dom0 c:terminal", "c:okular", "d:dom0 c:terminal" }')
    )

    assert "PIN: duplicate rule target: d:dom0 c:terminal" in messages


def test_workspace_routes_reject_duplicate_route_targets() -> None:
    messages = validate_workspace_routes_section(
        block("WORKSPACE_ROUTES", 'local WORKSPACE_ROUTES = { [1] = { "d:personal" }, [2] = { "d:personal" } }')
    )

    assert "WORKSPACE_ROUTES: duplicate route target: d:personal" in messages


def test_workspace_routes_reject_duplicate_workspace_keys() -> None:
    messages = validate_workspace_routes_section(
        block("WORKSPACE_ROUTES", 'local WORKSPACE_ROUTES = { [1] = { "d:personal" }, [1] = { "d:work" } }')
    )

    assert "WORKSPACE_ROUTES: duplicate workspace key: 1" in messages


def test_geom_rejects_duplicate_profile_names() -> None:
    messages = validate_geom_section(
        block(
            "GEOM",
            """local GEOM = {
              custom = { x = 0, y = 0, w = 10, h = 10 },
              custom = { x = 1, y = 1, w = 20, h = 20 },
            }""",
        )
    )

    assert "GEOM: duplicate geometry profile: custom" in messages


def test_placement_rejects_duplicate_targets() -> None:
    messages = validate_placement_section(
        block("WORKSPACE_PLACEMENT", 'local WORKSPACE_PLACEMENT = { "c:okular g:half_left", "c:okular g:half_right" }'),
        {"half_left", "half_right"},
    )

    assert "WORKSPACE_PLACEMENT: duplicate placement target: c:okular" in messages


def test_left_edge_rejects_duplicate_targets() -> None:
    messages = validate_left_edge_section(
        block("LEFT_EDGE_CORRECTION", 'local LEFT_EDGE_CORRECTION = { "c:okular le:pos1", "c:okular le:pos2" }')
    )

    assert "LEFT_EDGE_CORRECTION: duplicate left-edge target: c:okular" in messages
