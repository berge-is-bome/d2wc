from d2wc.core.managed_config import ManagedConfig, WorkspaceRoute
from d2wc.event_inventory import (
    KnownWindowCandidate,
    KnownWindowTarget,
    build_available_known_window_targets,
    build_known_window_targets,
    merge_known_window_targets,
    parse_known_window_candidates,
)


def test_parse_known_window_candidates_keeps_only_normal_windows() -> None:
    raw = """
machine: work
application: work:org.example.App
class_instance_name: work:Example
window_type: WINDOW_TYPE_NORMAL

machine: work
application: work:org.example.Dialog
class_instance_name: work:Dialog
window_type: WINDOW_TYPE_DIALOG
"""

    result = parse_known_window_candidates(raw)

    assert result == (
        KnownWindowCandidate(
            machine="work",
            application="example",
            raw_class_instance_name="work:Example",
            window_type="WINDOW_TYPE_NORMAL",
            raw_source=(
                "machine: work\n"
                "application: work:org.example.App\n"
                "class_instance_name: work:Example\n"
                "window_type: WINDOW_TYPE_NORMAL"
            ),
        ),
    )


def test_parse_known_window_candidates_normalizes_dom0_and_alias_keys() -> None:
    raw = """
_QUBES_VMNAME=""
application_name="dom0:Qubes-app-menu"
wm_class_instance="dom0:Qubes-app-menu"
window_type=WINDOW_TYPE_NORMAL
"""

    result = parse_known_window_candidates(raw)

    assert len(result) == 1
    assert result[0].machine == "dom0"
    assert result[0].application == "qubes-app-menu"
    assert result[0].raw_class_instance_name == "dom0:Qubes-app-menu"


def test_parse_known_window_candidates_supports_documented_debug_labels() -> None:
    raw = """
Domain: work
Application name: work:org.example.App
Window name: Example
Window Type: WINDOW_TYPE_NORMAL
Class instance name: work:Example
Window class: work:org.example.App
Screen Geometry: x = 3840.0 y = 2160.0
Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0
"""

    result = parse_known_window_candidates(raw)

    assert result == (
        KnownWindowCandidate(
            machine="work",
            application="example",
            raw_class_instance_name="work:Example",
            window_type="WINDOW_TYPE_NORMAL",
            raw_source=(
                "Domain: work\n"
                "Application name: work:org.example.App\n"
                "Window name: Example\n"
                "Window Type: WINDOW_TYPE_NORMAL\n"
                "Class instance name: work:Example\n"
                "Window class: work:org.example.App\n"
                "Screen Geometry: x = 3840.0 y = 2160.0\n"
                "Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0"
            ),
        ),
    )


def test_parse_known_window_candidates_ignores_incomplete_records() -> None:
    raw = """
machine: work
window_type: WINDOW_TYPE_NORMAL
"""

    assert parse_known_window_candidates(raw) == ()


def test_build_known_window_targets_collapses_repeated_observations() -> None:
    candidates = (
        _candidate("personal", "navigator"),
        _candidate("personal", "navigator"),
        _candidate("work", "navigator"),
    )

    assert build_known_window_targets(candidates) == (
        KnownWindowTarget(machine="personal", application="navigator"),
        KnownWindowTarget(machine="work", application="navigator"),
    )


def test_build_known_window_targets_skips_whitespace_tokens() -> None:
    candidates = (
        _candidate("personal", "example app"),
        _candidate("work vm", "navigator"),
        _candidate("work", "navigator"),
    )

    assert build_known_window_targets(candidates) == (
        KnownWindowTarget(machine="work", application="navigator"),
    )


def test_merge_known_window_targets_preserves_first_seen_order() -> None:
    personal_navigator = KnownWindowTarget(machine="personal", application="navigator")
    work_terminal = KnownWindowTarget(machine="work", application="terminal")
    work_navigator = KnownWindowTarget(machine="work", application="navigator")

    assert merge_known_window_targets(
        (personal_navigator, work_terminal),
        (work_terminal, work_navigator, personal_navigator),
    ) == (personal_navigator, work_terminal, work_navigator)


def test_build_available_known_window_targets_suppresses_section_matches() -> None:
    candidates = (
        _candidate("personal", "navigator"),
        _candidate("work", "navigator"),
        _candidate("work", "terminal"),
    )
    config = _config(
        workspace_routes=(WorkspaceRoute(2, ("d:work c:navigator",)),),
    )

    assert build_available_known_window_targets(candidates, config, "WORKSPACE_ROUTES") == (
        KnownWindowTarget(machine="personal", application="navigator"),
        KnownWindowTarget(machine="work", application="terminal"),
    )


def test_build_available_known_window_targets_honors_broad_domain_and_class_rules() -> None:
    candidates = (
        _candidate("personal", "navigator"),
        _candidate("personal", "terminal"),
        _candidate("work", "navigator"),
        _candidate("work", "terminal"),
    )
    config = _config(
        exclude=("d:personal",),
        pin=("c:terminal",),
    )

    assert build_available_known_window_targets(candidates, config, "EXCLUDE") == (
        KnownWindowTarget(machine="work", application="navigator"),
        KnownWindowTarget(machine="work", application="terminal"),
    )
    assert build_available_known_window_targets(candidates, config, "PIN") == (
        KnownWindowTarget(machine="personal", application="navigator"),
        KnownWindowTarget(machine="work", application="navigator"),
    )


def test_build_available_known_window_targets_returns_empty_for_non_target_sections() -> None:
    assert build_available_known_window_targets(
        (_candidate("work", "navigator"),),
        _config(),
        "GEOM",
    ) == ()


def _candidate(machine: str, application: str) -> KnownWindowCandidate:
    return KnownWindowCandidate(
        machine=machine,
        application=application,
        raw_class_instance_name=f"{machine}:{application}",
        window_type="WINDOW_TYPE_NORMAL",
        raw_source="source",
    )


def _config(
    *,
    exclude: tuple[str, ...] = (),
    pin: tuple[str, ...] = (),
    workspace_routes: tuple[WorkspaceRoute, ...] = (),
    workspace_placement: tuple[str, ...] = (),
    left_edge_correction: tuple[str, ...] = (),
) -> ManagedConfig:
    return ManagedConfig(
        exclude=exclude,
        pin=pin,
        workspace_routes=workspace_routes,
        geom=(),
        workspace_placement=workspace_placement,
        left_edge_correction=left_edge_correction,
    )