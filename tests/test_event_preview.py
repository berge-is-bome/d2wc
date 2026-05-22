from d2wc.event_data import EventScreenGeometry, EventWindowGeometry, WindowEventData
from d2wc.event_preview import (
    build_event_config_awareness,
    build_event_rule_preview,
    format_event_config_awareness,
    format_event_rule_preview,
    proposal_clipboard_text,
)


def event() -> WindowEventData:
    return WindowEventData(
        domain="work",
        application_name="work:org.example.App",
        window_name="Example",
        window_type="WINDOW_TYPE_NORMAL",
        class_instance_name="work:Example",
        window_class="work:org.example.App",
        screen_geometry=EventScreenGeometry(width=3840.0, height=2160.0),
        window_geometry=EventWindowGeometry(x=474.0, y=359.0, w=3366.0, h=1801.0),
    )


def test_build_event_rule_preview() -> None:
    preview = build_event_rule_preview(event())

    assert preview.ok
    assert preview.geometry_profile_name == "event_example"
    assert preview.geometry_profile_line == "event_example = { x = 474, y = 359, w = 3366, h = 1801 }"
    assert preview.placement_rule == "d:work c:example g:event_example"


def test_build_event_rule_preview_without_domain() -> None:
    preview = build_event_rule_preview(event().with_overrides(domain=""))

    assert preview.placement_rule == "c:example g:event_example"


def test_build_event_rule_preview_rejects_spaced_class_token() -> None:
    preview = build_event_rule_preview(event().with_overrides(class_instance_name="work:Example App"))

    assert not preview.ok
    assert preview.warning is not None
    assert "whitespace" in preview.warning


def test_build_event_rule_preview_rejects_incomplete_geometry() -> None:
    incomplete_event = WindowEventData(
        domain="work",
        class_instance_name="work:Example",
        window_geometry=EventWindowGeometry(x=10.0, y=20.0, w=800.0),
    )

    preview = build_event_rule_preview(incomplete_event)

    assert not preview.ok
    assert preview.warning == "Window geometry is incomplete, so a GEOM preview cannot be built."


def test_format_event_rule_preview() -> None:
    preview = build_event_rule_preview(event())

    text = format_event_rule_preview(preview)

    assert "Proposal status: ready for later edit wiring" in text
    assert "event_example = { x = 474, y = 359, w = 3366, h = 1801 }" in text
    assert "d:work c:example g:event_example" in text
    assert "No config files are read or written" in text


def test_format_event_rule_preview_unavailable() -> None:
    preview = build_event_rule_preview(WindowEventData())

    text = format_event_rule_preview(preview)

    assert "Proposal status: unavailable" in text
    assert "No safe class token" in text


def test_build_event_config_awareness_detects_existing_profile_and_matching_rules() -> None:
    source = '''
local EXCLUDE = {
}
local PIN = {
}
local WORKSPACE_ROUTES = {
  [1] = { "d:work", },
}
local GEOM = {
  event_example = { x = 474, y = 359, w = 3366, h = 1801 },
}
local WORKSPACE_PLACEMENT = {
  "d:work c:example g:event_example",
}
local LEFT_EDGE_CORRECTION = {
}
'''
    preview = build_event_rule_preview(event())

    awareness = build_event_config_awareness(source, preview)

    assert awareness.status == "ok"
    assert awareness.profile_exists
    assert "WORKSPACE_ROUTES[1]: d:work" in awareness.matching_rules
    assert "WORKSPACE_PLACEMENT: d:work c:example g:event_example" in awareness.matching_rules
    assert awareness.has_existing_handling


def test_build_event_config_awareness_reports_no_matches() -> None:
    source = '''
local EXCLUDE = {
}
local PIN = {
}
local WORKSPACE_ROUTES = {
}
local GEOM = {
}
local WORKSPACE_PLACEMENT = {
}
local LEFT_EDGE_CORRECTION = {
}
'''
    preview = build_event_rule_preview(event())

    awareness = build_event_config_awareness(source, preview)

    assert awareness.status == "ok"
    assert not awareness.profile_exists
    assert awareness.matching_rules == ()
    assert not awareness.has_existing_handling


def test_format_event_config_awareness_none() -> None:
    text = format_event_config_awareness(None)

    assert "Config status: not inspected" in text
    assert "Pass --config" in text


def test_format_event_config_awareness_with_matches() -> None:
    source = '''
local EXCLUDE = {
}
local PIN = {
}
local WORKSPACE_ROUTES = {
}
local GEOM = {
}
local WORKSPACE_PLACEMENT = {
  "d:work c:example g:event_example",
}
local LEFT_EDGE_CORRECTION = {
}
'''
    preview = build_event_rule_preview(event())
    awareness = build_event_config_awareness(source, preview)

    text = format_event_config_awareness(awareness)

    assert "Config status: ok" in text
    assert "Existing target matches:" in text
    assert "WORKSPACE_PLACEMENT: d:work c:example g:event_example" in text
    assert "No config files were changed." in text


def test_proposal_clipboard_text_combines_preview_and_config_awareness() -> None:
    preview = build_event_rule_preview(event())
    text = proposal_clipboard_text(preview)

    assert "Candidate GEOM profile:" in text
    assert "Candidate WORKSPACE_PLACEMENT rule:" in text
