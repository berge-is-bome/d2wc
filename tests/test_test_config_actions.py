from d2wc.test_config import load_test_config_snapshot
from d2wc.test_config_actions import ManagedSectionActionRequest, apply_managed_section_action


VALID_MINIMAL_CONFIG = '''
local EXCLUDE = {
}
local PIN = {
}
local WORKSPACE_ROUTES = {
}
local GEOM = {
  half_left = { x = 0, y = 0, w = 1920, h = 2115 },
}
local WORKSPACE_PLACEMENT = {
  "d:personal c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {
}
'''


def write_config(tmp_path):
    path = tmp_path / "d2wc-test.lua"
    path.write_text(VALID_MINIMAL_CONFIG, encoding="utf-8")
    return path


def test_add_and_delete_exclude(tmp_path) -> None:
    path = write_config(tmp_path)

    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="EXCLUDE", operation="add", rule="d:work c:example"),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="EXCLUDE", operation="delete", rule="d:work c:example"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert "d:work c:example" not in snapshot.config.exclude


def test_add_and_delete_pin(tmp_path) -> None:
    path = write_config(tmp_path)

    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:example"),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="PIN", operation="delete", rule="d:work c:example"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert "d:work c:example" not in snapshot.config.pin


def test_add_and_delete_workspace_route(tmp_path) -> None:
    path = write_config(tmp_path)

    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="WORKSPACE_ROUTES", operation="add", rule="d:work c:example", workspace=2),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="WORKSPACE_ROUTES", operation="delete", rule="d:work c:example"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert all("d:work c:example" not in route.rules for route in snapshot.config.workspace_routes)


def test_add_and_delete_geom(tmp_path) -> None:
    path = write_config(tmp_path)

    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(
            section="GEOM",
            operation="add",
            profile_name="event_example",
            x=10,
            y=20,
            w=800,
            h=600,
        ),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="GEOM", operation="delete", profile_name="event_example"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert all(profile.name != "event_example" for profile in snapshot.config.geom)


def test_add_and_delete_workspace_placement(tmp_path) -> None:
    path = write_config(tmp_path)

    apply_managed_section_action(
        path,
        ManagedSectionActionRequest(
            section="GEOM",
            operation="add",
            profile_name="event_example",
            x=10,
            y=20,
            w=800,
            h=600,
        ),
    )
    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="WORKSPACE_PLACEMENT", operation="add", rule="d:work c:example g:event_example"),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="WORKSPACE_PLACEMENT", operation="delete", rule="d:work c:example g:event_example"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert "d:work c:example g:event_example" not in snapshot.config.workspace_placement


def test_add_and_delete_left_edge(tmp_path) -> None:
    path = write_config(tmp_path)

    add_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="LEFT_EDGE_CORRECTION", operation="add", rule="d:work c:example le:pos1"),
    )
    delete_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="LEFT_EDGE_CORRECTION", operation="delete", rule="d:work c:example le:pos1"),
    )

    assert add_result.ok
    assert delete_result.ok
    snapshot = load_test_config_snapshot(path)
    assert snapshot.config is not None
    assert "d:work c:example le:pos1" not in snapshot.config.left_edge_correction


def test_invalid_geom_request_reports_error(tmp_path) -> None:
    path = write_config(tmp_path)

    result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="GEOM", operation="add", profile_name="event_example", x=10, y=20, w=800),
    )

    assert not result.ok
    assert "GEOM add requires numeric values" in result.message
