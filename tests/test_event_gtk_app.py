from d2wc.event_data import WindowEventData, EventScreenGeometry, EventWindowGeometry
from d2wc.ui.gtk_app import format_event_geometry, format_event_identity


def test_format_event_identity() -> None:
    event = WindowEventData(
        domain="work",
        application_name="work:org.example.App",
        window_name="Example",
        window_type="WINDOW_TYPE_NORMAL",
        class_instance_name="work:Example",
        window_class="work:org.example.App",
    )

    assert format_event_identity(event) == "\n".join(
        [
            "Domain: work",
            "Application name: work:org.example.App",
            "Window name: Example",
            "Window Type: WINDOW_TYPE_NORMAL",
            "Class instance name: work:Example",
            "Window class: work:org.example.App",
        ]
    )


def test_format_event_identity_treats_empty_domain_as_dom0() -> None:
    event = WindowEventData(domain="")

    assert "Domain: dom0" in format_event_identity(event)


def test_format_event_geometry() -> None:
    event = WindowEventData(
        screen_geometry=EventScreenGeometry(width=3840.0, height=2160.0),
        window_geometry=EventWindowGeometry(x=474.0, y=359.0, w=3366.0, h=1801.0),
    )

    assert format_event_geometry(event) == "\n".join(
        [
            "Screen Geometry: x = 3840.0 y = 2160.0",
            "Window geometry:  x = 474.0 y = 359.0 w = 3366.0 h = 1801.0",
            "Geometry: x=474.0 y=359.0 w=3366.0 h=1801.0",
            "geometry 3366.0x1801.0",
        ]
    )
