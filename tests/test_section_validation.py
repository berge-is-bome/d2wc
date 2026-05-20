from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.section_validation import (
    MIN_GEOMETRY_SIZE,
    extract_active_rule_strings,
    extract_geometry_profile_names,
    extract_geometry_profiles,
    validate_geom_section,
    validate_left_edge_section,
    validate_placement_section,
    validate_target_section,
    validate_workspace_routes_section,
)


def block(name: str, text: str) -> ManagedBlock:
    return ManagedBlock(name=name, start_index=0, end_index=len(text), text=text)


def test_extract_active_rule_strings_ignores_comments() -> None:
    text = '''local EXCLUDE = {
      "d:personal",
      -- "d:work",
      "c:okular", -- "c:commented-tail"
    }'''

    assert extract_active_rule_strings(text) == ["d:personal", "c:okular"]


def test_extract_geometry_profile_names() -> None:
    text = '''local GEOM = {
      half_left = { x = 0, y = 0, w = 1920, h = 1080 },
      -- ignored = { x = 0, y = 0, w = 1, h = 1 },
      dom0_qubes_app_menu = { x = 0, y = 0, w = 1000, h = 1200 },
    }'''

    assert extract_geometry_profile_names(text) == {"half_left", "dom0_qubes_app_menu"}


def test_extract_geometry_profiles() -> None:
    text = '''local GEOM = {
      half_left = { x = 0, y = 0, w = 1920, h = 1080 },
    }'''

    assert extract_geometry_profiles(text) == {
        "half_left": {"x": 0, "y": 0, "w": 1920, "h": 1080}
    }


def test_validate_target_section_accepts_domain_or_class_rules() -> None:
    messages = validate_target_section(
        block("PIN", 'local PIN = { "d:dom0 c:xfce4-terminal", "c:okular" }')
    )

    assert messages == []


def test_validate_target_section_rejects_geometry_and_left_edge_tokens() -> None:
    messages = validate_target_section(
        block("EXCLUDE", 'local EXCLUDE = { "d:personal g:half_left", "c:okular le:pos1" }')
    )

    assert "EXCLUDE: rule must not include g:: d:personal g:half_left" in messages
    assert "EXCLUDE: rule must not include le:: c:okular le:pos1" in messages


def test_validate_workspace_routes_section_accepts_valid_routes() -> None:
    messages = validate_workspace_routes_section(
        block("WORKSPACE_ROUTES", 'local WORKSPACE_ROUTES = { [1] = { "d:personal", "d:work c:navigator" } }')
    )

    assert messages == []


def test_validate_workspace_routes_section_rejects_invalid_route_tokens() -> None:
    messages = validate_workspace_routes_section(
        block("WORKSPACE_ROUTES", 'local WORKSPACE_ROUTES = { [1] = { "g:half_left", "c:okular le:pos1" } }')
    )

    assert "WORKSPACE_ROUTES: rule must include d: or c:: g:half_left" in messages
    assert "WORKSPACE_ROUTES: rule must not include g:: g:half_left" in messages
    assert "WORKSPACE_ROUTES: rule must not include le:: c:okular le:pos1" in messages


def test_validate_geom_section_accepts_minimum_sizes() -> None:
    messages = validate_geom_section(
        block(
            "GEOM",
            f"local GEOM = {{ custom = {{ x = 0, y = 0, w = {MIN_GEOMETRY_SIZE}, h = {MIN_GEOMETRY_SIZE} }} }}",
        )
    )

    assert messages == []


def test_validate_geom_section_rejects_sizes_below_minimum() -> None:
    messages = validate_geom_section(
        block("GEOM", 'local GEOM = { custom = { x = 0, y = 0, w = 9, h = 0 } }')
    )

    assert "GEOM: profile custom field w must be at least 10" in messages
    assert "GEOM: profile custom field h must be at least 10" in messages


def test_validate_geom_section_rejects_missing_and_invalid_fields() -> None:
    messages = validate_geom_section(
        block("GEOM", 'local GEOM = { broken = { x = 0, y = nope, w = -1 } }')
    )

    assert "GEOM: profile broken field y must be an integer" in messages
    assert "GEOM: profile broken missing h" in messages
    assert "GEOM: profile broken field w must be at least 10" in messages


def test_validate_placement_section_requires_existing_geometry_profile() -> None:
    messages = validate_placement_section(
        block("WORKSPACE_PLACEMENT", 'local WORKSPACE_PLACEMENT = { "c:okular g:missing" }'),
        {"half_left"},
    )

    assert messages == ["WORKSPACE_PLACEMENT: geometry profile not found: missing"]


def test_validate_left_edge_section_accepts_pos1_and_pos2() -> None:
    messages = validate_left_edge_section(
        block("LEFT_EDGE_CORRECTION", 'local LEFT_EDGE_CORRECTION = { "c:okular le:pos1", "d:dom0 le:pos2" }')
    )

    assert messages == []


def test_validate_left_edge_section_rejects_invalid_mode() -> None:
    messages = validate_left_edge_section(
        block("LEFT_EDGE_CORRECTION", 'local LEFT_EDGE_CORRECTION = { "c:okular le:wrong" }')
    )

    assert messages == ["LEFT_EDGE_CORRECTION: invalid left-edge mode: wrong"]
