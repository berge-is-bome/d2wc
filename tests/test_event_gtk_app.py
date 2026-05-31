from d2wc.ui.managed_actions import EDITOR_ACTIONS


def test_managed_editor_actions() -> None:
    assert EDITOR_ACTIONS == ("Add", "Modify", "Delete")


def test_run_configurator_omits_event_fixture_when_event_data_is_not_provided(monkeypatch) -> None:
    from d2wc.ui import gtk_app

    def fail_fixture(_name=None):
        raise AssertionError("run_configurator should not load a development fixture by default")

    monkeypatch.setattr(gtk_app, "get_event_fixture", fail_fixture, raising=False)
    monkeypatch.setattr(
        gtk_app,
        "_import_gtk",
        lambda: (_ for _ in ()).throw(gtk_app.GtkConfiguratorImportError("GTK intentionally unavailable")),
    )

    try:
        gtk_app.run_configurator()
    except gtk_app.GtkConfiguratorImportError as exc:
        assert "GTK intentionally unavailable" in str(exc)
    else:
        raise AssertionError("expected GTK import to stop the launcher")
