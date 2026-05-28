from d2wc.ui.gtk_app import _file_monitor_event_name, _is_managed_config_reload_event


class EventWithName:
    name = "CHANGES_DONE_HINT"


class EventWithNick:
    value_nick = "attribute-changed"


class StringEvent:
    def __str__(self) -> str:
        return "<enum G_FILE_MONITOR_EVENT_CHANGED of type Gio.FileMonitorEvent>"


def test_file_monitor_reload_events_include_common_write_notifications() -> None:
    assert _is_managed_config_reload_event(EventWithName())
    assert _is_managed_config_reload_event(StringEvent())


def test_file_monitor_reload_events_ignore_metadata_only_notifications() -> None:
    assert not _is_managed_config_reload_event(EventWithNick())


def test_file_monitor_event_name_normalizes_gio_enum_strings() -> None:
    assert _file_monitor_event_name(StringEvent()) == "CHANGED"
