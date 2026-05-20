from d2wc.core.managed_config import GeometryProfile, render_geom_block


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
  wide                   = { x = 100 , y = 456, w = 3624, h = 1389 },
  centered_mid           = { x = 960 , y = 540, w = 1200, h = 900  },
  half_left              = { x = 0   , y = 0  , w = 1920, h = 2115 },
  dom0_template_manager  = { x = 1129, y = 0  , w = 1220, h = 2115 },
}"""
