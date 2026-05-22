"""Event-provided Devilspie2 window data for the configurator UI."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class EventScreenGeometry:
    """Screen geometry captured from the Devilspie2 event context."""

    width: float | None = None
    height: float | None = None


@dataclass(frozen=True)
class EventWindowGeometry:
    """Window geometry captured from the Devilspie2 event context."""

    x: float | None = None
    y: float | None = None
    w: float | None = None
    h: float | None = None

    @property
    def size_text(self) -> str | None:
        """Return WIDTHxHEIGHT text when both dimensions are known."""

        if self.w is None or self.h is None:
            return None
        return f"{self.w}x{self.h}"


@dataclass(frozen=True)
class WindowEventData:
    """Identity and geometry captured by Devilspie2/Lua for one window event."""

    domain: str | None = None
    application_name: str | None = None
    window_name: str | None = None
    window_type: str | None = None
    class_instance_name: str | None = None
    window_class: str | None = None
    screen_geometry: EventScreenGeometry = EventScreenGeometry()
    window_geometry: EventWindowGeometry = EventWindowGeometry()

    @property
    def display_domain(self) -> str | None:
        """Return a display-safe domain value, treating empty Qubes VM name as dom0."""

        if self.domain == "":
            return "dom0"
        return self.domain

    def with_overrides(
        self,
        *,
        domain: str | None = None,
        application_name: str | None = None,
        window_name: str | None = None,
        window_type: str | None = None,
        class_instance_name: str | None = None,
        window_class: str | None = None,
        screen_width: float | None = None,
        screen_height: float | None = None,
        window_x: float | None = None,
        window_y: float | None = None,
        window_width: float | None = None,
        window_height: float | None = None,
    ) -> WindowEventData:
        """Return a copy with command-line event-data overrides applied."""

        screen_geometry = replace(
            self.screen_geometry,
            width=self.screen_geometry.width if screen_width is None else screen_width,
            height=self.screen_geometry.height if screen_height is None else screen_height,
        )
        window_geometry = replace(
            self.window_geometry,
            x=self.window_geometry.x if window_x is None else window_x,
            y=self.window_geometry.y if window_y is None else window_y,
            w=self.window_geometry.w if window_width is None else window_width,
            h=self.window_geometry.h if window_height is None else window_height,
        )

        return replace(
            self,
            domain=self.domain if domain is None else domain,
            application_name=self.application_name if application_name is None else application_name,
            window_name=self.window_name if window_name is None else window_name,
            window_type=self.window_type if window_type is None else window_type,
            class_instance_name=(
                self.class_instance_name if class_instance_name is None else class_instance_name
            ),
            window_class=self.window_class if window_class is None else window_class,
            screen_geometry=screen_geometry,
            window_geometry=window_geometry,
        )


DEFAULT_EVENT_FIXTURE = "example"

_EVENT_FIXTURES: dict[str, WindowEventData] = {
    "example": WindowEventData(
        domain="work",
        application_name="work:org.example.App",
        window_name="Example",
        window_type="WINDOW_TYPE_NORMAL",
        class_instance_name="work:Example",
        window_class="work:org.example.App",
        screen_geometry=EventScreenGeometry(width=3840.0, height=2160.0),
        window_geometry=EventWindowGeometry(x=474.0, y=359.0, w=3366.0, h=1801.0),
    ),
}

EVENT_FIXTURE_NAMES = tuple(_EVENT_FIXTURES)


def get_event_fixture(name: str = DEFAULT_EVENT_FIXTURE) -> WindowEventData:
    """Return a representative event-data fixture by name."""

    try:
        return _EVENT_FIXTURES[name]
    except KeyError as exc:
        choices = ", ".join(EVENT_FIXTURE_NAMES)
        raise ValueError(f"unknown event fixture {name!r}; choose one of: {choices}") from exc
