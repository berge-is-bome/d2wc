from pathlib import Path

from d2wc.core.managed_config import GeometryProfile, ManagedConfig, WorkspaceRoute
from d2wc.event_data import get_event_fixture
from d2wc.event_inventory import KnownWindowTarget
from d2wc.test_config import TestConfigSnapshot as ConfigSnapshot
from d2wc.ui.grid_rows import (
    build_available_known_window_grid_rows,
    build_configured_grid_rows,
    build_known_window_grid_rows,
    class_values,
)


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


def test_default_event_fixture_is_empty_for_normal_configurator_launch() -> None:
    event_data = get_event_fixture()

    assert event_data.domain is None
    assert event_data.class_instance_name is None
    assert event_data.window_class is None
    assert build_known_window_grid_rows(event_data) == ()
    assert class_values(None, event_data) == ()


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


def test_build_known_window_grid_rows_creates_inventory_target_rows() -> None:
    rows = build_known_window_grid_rows(
        inventory_targets=(
            KnownWindowTarget(machine="personal", application="navigator"),
            KnownWindowTarget(machine="work", application="terminal"),
        )
    )

    assert [row.section for row in rows] == [
        "EXCLUDE",
        "PIN",
        "WORKSPACE_ROUTES",
        "WORKSPACE_PLACEMENT",
        "LEFT_EDGE_CORRECTION",
        "EXCLUDE",
        "PIN",
        "WORKSPACE_ROUTES",
        "WORKSPACE_PLACEMENT",
        "LEFT_EDGE_CORRECTION",
    ]
    assert all(row.source == "not configured" for row in rows)
    assert all(row.action == "Add" for row in rows)
    assert rows[0].target_entry == "d:personal c:navigator"
    assert rows[3].target_entry == "d:personal c:navigator"
    assert rows[4].target_entry == "d:personal c:navigator le:pos1"
    assert rows[5].target_entry == "d:work c:terminal"
    assert rows[8].target_entry == "d:work c:terminal"
    assert rows[9].target_entry == "d:work c:terminal le:pos1"


def test_build_known_window_grid_rows_inventory_targets_do_not_create_geom_rows() -> None:
    rows = build_known_window_grid_rows(
        inventory_targets=(KnownWindowTarget(machine="personal", application="navigator"),)
    )

    assert "GEOM" not in {row.section for row in rows}


def test_build_available_known_window_grid_rows_suppresses_current_section_matches() -> None:
    snapshot = ConfigSnapshot(
        path=Path("d2wc-test.lua"),
        exists=True,
        config=ManagedConfig(
            exclude=(),
            pin=(),
            workspace_routes=(WorkspaceRoute(2, ("d:work c:navigator",)),),
            geom=(),
            workspace_placement=(),
            left_edge_correction=(),
        ),
    )

    rows = build_available_known_window_grid_rows(
        snapshot,
        "WORKSPACE_ROUTES",
        (
            KnownWindowTarget(machine="personal", application="navigator"),
            KnownWindowTarget(machine="work", application="navigator"),
            KnownWindowTarget(machine="work", application="terminal"),
        ),
    )

    assert [row.section for row in rows] == ["WORKSPACE_ROUTES", "WORKSPACE_ROUTES"]
    assert [row.target_entry for row in rows] == [
        "d:personal c:navigator",
        "d:work c:terminal",
    ]


def test_build_available_known_window_grid_rows_returns_empty_for_geom() -> None:
    snapshot = ConfigSnapshot(
        path=Path("d2wc-test.lua"),
        exists=True,
        config=ManagedConfig(
            exclude=(),
            pin=(),
            workspace_routes=(),
            geom=(),
            workspace_placement=(),
            left_edge_correction=(),
        ),
    )

    assert build_available_known_window_grid_rows(
        snapshot,
        "GEOM",
        (KnownWindowTarget(machine="personal", application="navigator"),),
    ) == ()
