from d2wc import __main__


def test_main_configure_runs_gtk_launcher(monkeypatch) -> None:
    calls = []

    def fake_run_configurator() -> int:
        calls.append("run")
        return 0

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(["configure"])

    assert exit_code == 0
    assert calls == ["run"]


def test_main_configure_reports_missing_gtk(monkeypatch, capsys) -> None:
    def fake_run_configurator() -> int:
        raise __main__.GtkConfiguratorImportError("GTK is missing")

    monkeypatch.setattr(__main__, "run_configurator", fake_run_configurator)

    exit_code = __main__.main(["configure"])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "ERROR: GTK is missing" in captured.out


def test_main_delegates_other_commands_to_cli(monkeypatch) -> None:
    calls = []

    def fake_cli_main(argv) -> int:
        calls.append(list(argv))
        return 17

    monkeypatch.setattr(__main__, "cli_main", fake_cli_main)

    exit_code = __main__.main(["validate", "--config", "src/d2wc.lua"])

    assert exit_code == 17
    assert calls == [["validate", "--config", "src/d2wc.lua"]]
