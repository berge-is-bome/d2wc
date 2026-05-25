from d2wc import __main__


MANAGED_CONFIG_SOURCE = '''
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


def test_main_without_args_runs_gtk_launcher(monkeypatch, tmp_path) -> None:
    calls = []
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text(MANAGED_CONFIG_SOURCE, encoding="utf-8")

    monkeypatch.setattr(__main__, "default_managed_config_path", lambda: config_path)

    def fake_run_configurator(event_data, config_awareness, test_config_snapshot, prepare_result) -> int:
        calls.append((event_data, config_awareness, test_config_snapshot, prepare_result))
        return 0

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main([])

    assert exit_code == 0
    assert len(calls) == 1
    _event_data, config_awareness, test_config_snapshot, prepare_result = calls[0]
    assert config_awareness.status == "ok"
    assert test_config_snapshot.ok
    assert test_config_snapshot.path == config_path
    assert prepare_result is None


def test_main_configure_runs_gtk_launcher(monkeypatch, tmp_path) -> None:
    calls = []
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text(MANAGED_CONFIG_SOURCE, encoding="utf-8")

    monkeypatch.setattr(__main__, "default_managed_config_path", lambda: config_path)

    def fake_run_configurator(event_data, config_awareness, test_config_snapshot, prepare_result) -> int:
        calls.append((event_data, config_awareness, test_config_snapshot, prepare_result))
        return 0

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(["configure"])

    assert exit_code == 0
    assert len(calls) == 1
    _event_data, config_awareness, test_config_snapshot, prepare_result = calls[0]
    assert config_awareness.status == "ok"
    assert test_config_snapshot.ok
    assert test_config_snapshot.path == config_path
    assert prepare_result is None


def test_main_configure_reports_missing_gtk(monkeypatch, tmp_path, capsys) -> None:
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text(MANAGED_CONFIG_SOURCE, encoding="utf-8")

    monkeypatch.setattr(__main__, "default_managed_config_path", lambda: config_path)

    def fake_run_configurator(_event_data, _config_awareness, _test_config_snapshot, _prepare_result) -> int:
        raise __main__.GtkConfiguratorImportError("GTK is missing")

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(["configure"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "ERROR: GTK is missing" in captured.out


def test_main_configure_passes_event_data_and_config_awareness(monkeypatch, tmp_path) -> None:
    calls = []
    config_path = tmp_path / "d2wc.lua"
    config_path.write_text(MANAGED_CONFIG_SOURCE, encoding="utf-8")

    def fake_run_configurator(event_data, config_awareness, test_config_snapshot, prepare_result) -> int:
        calls.append((event_data, config_awareness, test_config_snapshot, prepare_result))
        return 0

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(
        [
            "configure",
            "--config",
            str(config_path),
            "--domain",
            "personal",
            "--class-instance-name",
            "personal:Example",
            "--window-x",
            "10",
            "--window-y",
            "20",
            "--window-width",
            "800",
            "--window-height",
            "600",
        ]
    )

    assert exit_code == 0
    assert len(calls) == 1
    event_data, config_awareness, test_config_snapshot, prepare_result = calls[0]
    assert event_data.domain == "personal"
    assert event_data.class_instance_name == "personal:Example"
    assert event_data.window_geometry.x == 10.0
    assert config_awareness.status == "ok"
    assert test_config_snapshot is None
    assert prepare_result is None


def test_main_configure_loads_test_config(monkeypatch, tmp_path) -> None:
    calls = []
    test_config_path = tmp_path / "d2wc-test.lua"
    test_config_path.write_text(MANAGED_CONFIG_SOURCE, encoding="utf-8")

    def fake_run_configurator(event_data, config_awareness, test_config_snapshot, prepare_result) -> int:
        calls.append((event_data, config_awareness, test_config_snapshot, prepare_result))
        return 0

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(["configure", "--test-config", "--test-config-path", str(test_config_path)])

    assert exit_code == 0
    assert len(calls) == 1
    _event_data, config_awareness, test_config_snapshot, prepare_result = calls[0]
    assert config_awareness.status == "ok"
    assert test_config_snapshot.ok
    assert test_config_snapshot.path == test_config_path
    assert prepare_result is None


def test_main_delegates_other_commands_to_cli(monkeypatch) -> None:
    calls = []

    def fake_cli_main(argv) -> int:
        calls.append(list(argv))
        return 17

    monkeypatch.setattr(__main__, "cli_main", fake_cli_main)

    exit_code = __main__.main(["validate", "--config", "src/d2wc.lua"])

    assert exit_code == 17
    assert calls == [["validate", "--config", "src/d2wc.lua"]]
