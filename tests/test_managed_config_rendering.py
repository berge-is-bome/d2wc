from d2wc.core.lua_blocks import ManagedBlock
from d2wc.core.managed_config import (
    GeometryProfile,
    extract_managed_config,
    render_geom_block,
    render_managed_config,
)


def block(name: str, text: str) -> ManagedBlock:
    return ManagedBlock(name=name, start_index=0, end_index=len(text), text=text)


def test_render_geom_block_aligns_profile_names_and_numeric_columns() -> None:
    rendered = render_geom_block(
        (
            GeometryProfile(name="wide", x=100, y=456, w=3624, h=1389),
            GeometryProfile(name="centered_mid", x=960, y=540, w=1200, h=900),
            GeometryProfile(name="half_left", x=0, y=0, w=1920, h=2115),
            GeometryProfile(name="dom0_template_manager", x=1129, y=0, w=1220, h=2115),
        )
    )

    assert rendered == """local GEOM = {
  wide                   = { x = 100 , y = 456 , w = 3624, h = 1389 },
  centered_mid           = { x = 960 , y = 540 , w = 1200, h = 900  },
  half_left              = { x = 0   , y = 0   , w = 1920, h = 2115 },
  dom0_template_manager  = { x = 1129, y = 0   , w = 1220, h = 2115 },
}"""


def test_render_rule_list_preserves_comments_and_blank_lines() -> None:
    blocks = {
        "EXCLUDE": block(
            "EXCLUDE",
            '''local EXCLUDE = {
  -- keep this note
  "d:personal", -- personal note

  "c:okular",
}''',
        ),
        "PIN": block("PIN", "local PIN = {}"),
        "WORKSPACE_ROUTES": block("WORKSPACE_ROUTES", "local WORKSPACE_ROUTES = {}"),
        "GEOM": block("GEOM", "local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }"),
        "WORKSPACE_PLACEMENT": block("WORKSPACE_PLACEMENT", "local WORKSPACE_PLACEMENT = {}"),
        "LEFT_EDGE_CORRECTION": block("LEFT_EDGE_CORRECTION", "local LEFT_EDGE_CORRECTION = {}"),
    }
    config = extract_managed_config(blocks)

    rendered = render_managed_config(config, blocks)["EXCLUDE"]

    assert rendered == '''local EXCLUDE = {
  -- keep this note
  "d:personal", -- personal note

  "c:okular",
}'''


def test_render_geom_preserves_comments_and_blank_lines() -> None:
    blocks = {
        "EXCLUDE": block("EXCLUDE", "local EXCLUDE = {}"),
        "PIN": block("PIN", "local PIN = {}"),
        "WORKSPACE_ROUTES": block("WORKSPACE_ROUTES", "local WORKSPACE_ROUTES = {}"),
        "GEOM": block(
            "GEOM",
            '''local GEOM = {
  -- main split profiles
  half_left = { x = 0, y = 0, w = 10, h = 10 }, -- left note

  half_right = { x = 20, y = 0, w = 10, h = 10 },
}''',
        ),
        "WORKSPACE_PLACEMENT": block("WORKSPACE_PLACEMENT", "local WORKSPACE_PLACEMENT = {}"),
        "LEFT_EDGE_CORRECTION": block("LEFT_EDGE_CORRECTION", "local LEFT_EDGE_CORRECTION = {}"),
    }
    config = extract_managed_config(blocks)

    rendered = render_managed_config(config, blocks)["GEOM"]

    assert rendered == '''local GEOM = {
  -- main split profiles
  half_left              = { x = 0   , y = 0   , w = 10  , h = 10   },     -- left note

  half_right             = { x = 20  , y = 0   , w = 10  , h = 10   },
}'''


def test_workspace_routes_preserves_original_comments_and_blank_lines_for_now() -> None:
    blocks = {
        "EXCLUDE": block("EXCLUDE", "local EXCLUDE = {}"),
        "PIN": block("PIN", "local PIN = {}"),
        "WORKSPACE_ROUTES": block(
            "WORKSPACE_ROUTES",
            '''local WORKSPACE_ROUTES = {
  -- routing note
  [1] = { "d:personal" }, -- workspace one

  [2] = { "d:work" },
}''',
        ),
        "GEOM": block("GEOM", "local GEOM = { half_left = { x = 0, y = 0, w = 10, h = 10 } }"),
        "WORKSPACE_PLACEMENT": block("WORKSPACE_PLACEMENT", "local WORKSPACE_PLACEMENT = {}"),
        "LEFT_EDGE_CORRECTION": block("LEFT_EDGE_CORRECTION", "local LEFT_EDGE_CORRECTION = {}"),
    }
    config = extract_managed_config(blocks)

    rendered = render_managed_config(config, blocks)["WORKSPACE_ROUTES"]

    assert rendered == blocks["WORKSPACE_ROUTES"].text
