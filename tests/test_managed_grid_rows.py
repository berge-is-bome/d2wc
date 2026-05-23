from pathlib import Path

from d2wc.core.managed_config import GeometryProfile, ManagedConfig, WorkspaceRoute
from d2wc.event_data import get_event_fixture
from d2wc.test_config import TestConfigSnapshot as ConfigSnapshot
from d2wc.ui.managed_actions import build_configured_grid_rows, build_known_window_grid_rows


def test_build_configured_grid_rows_flattens_all_sections() -> None:
    snapshot = ConfigSnapshot(
        path=Path("d2wc-test.lua"),
        exists=True,
        config=ManagedConfig(
            exclude=("d:personal",),
            pin=("d:work c:terminal",),
            workspace_routes=(WorkspaceRoute(2, ("d:work c:navigator",)),),
            geom=(GeometryProfile("nav_wide", 10, 20, 300, 400),),
            workspace_placement=("d:work c:navigator g:nav_wide",),
            left_edge_correction=("d:work c:navigator le:pos1",),
        ),
    )

    rows = build_configured_grid_rows(snapshot)

    assert [row.section for row in rows] == [
        "EXCLUDE",
        "PIN",
        "WORKSPACE_ROUTES",
        "GEOM",
        "WORKSPACE_PLACEMENT",
        "LEFT_EDGE_CORRECTION",
    ]
    assert rows[2].workspace == "2"
    assert rows[3].existing_profile == "nav_wide"
    assert rows[3].geometry == "x=10 y=20 w=300 h=400"
    assert rows[4].existing_profile == "nav_wide"


def test_build_known_window_grid_rows_creates_event_proposals() -> None:
    rows = build_known_window_grid_rows(get_event_fixture("example"))

    assert [row.section for row in rows] == [
        "EXCLUDE",
        "PIN",
        "WORKSPACE_ROUTES",
        "GEOM",
        "WORKSPACE_PLACEMENT",
        "LEFT_EDGE_CORRECTION",
    ]
    assert all(row.action == "Add" for row in rows)
    assert rows[0].target_entry == "d:work c:example"
    assert rows[2].target_entry == "d:work c:example"
    assert rows[3].new_profile == "event_example"
    assert rows[3].geometry == "x=474 y=359 w=3366 h=1801"
    assert rows[4].target_entry == "d:work c:example g:event_example"
    assert rows[5].target_entry == "d:work c:example le:pos1"
