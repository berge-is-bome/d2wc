from d2wc.event_data import EventWindowGeometry, WindowEventData, get_event_fixture


def test_event_window_geometry_size_text() -> None:
    assert EventWindowGeometry(w=800.0, h=600.0).size_text == "800.0x600.0"
    assert EventWindowGeometry(w=800.0).size_text is None


def test_empty_domain_displays_as_dom0() -> None:
    assert WindowEventData(domain="").display_domain == "dom0"


def test_event_fixture_uses_standard_vm_sample() -> None:
    event = get_event_fixture("example")

    assert event.domain == "work"
    assert event.class_instance_name == "work:Example"
    assert event.window_class == "work:org.example.App"


def test_event_fixture_rejects_unknown_fixture() -> None:
    try:
        get_event_fixture("unknown")
    except ValueError as exc:
        assert "unknown event fixture" in str(exc)
        assert "example" in str(exc)
    else:
        raise AssertionError("expected unknown fixture to raise ValueError")


def test_event_data_with_overrides_keeps_unspecified_fixture_values() -> None:
    event = get_event_fixture("example").with_overrides(
        domain="personal",
        window_x=10.0,
        window_y=20.0,
        window_width=800.0,
        window_height=600.0,
    )

    assert event.domain == "personal"
    assert event.application_name == "work:org.example.App"
    assert event.window_geometry.x == 10.0
    assert event.window_geometry.y == 20.0
    assert event.window_geometry.w == 800.0
    assert event.window_geometry.h == 600.0
