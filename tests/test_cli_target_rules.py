from pathlib import Path

from d2wc.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]


def copy_current_config(tmp_path: Path) -> Path:
    source = REPO_ROOT / "src" / "d2wc.lua"
    target = tmp_path / "d2wc.lua"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_cli_add_pin_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        "d:dom0 c:qubes-qube-manager",
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert "Planned PIN add: d:dom0 c:qubes-qube-manager" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert "Run again with --write to save." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))


def test_cli_add_pin_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        "d:dom0 c:qubes-qube-manager",
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.*.bak"))

    assert exit_code == 0
    assert "OK: PIN rule added: d:dom0 c:qubes-qube-manager" in captured.out
    assert "Backup:" in captured.out
    assert '"d:dom0 c:qubes-qube-manager",' in saved
    assert backups
    assert backups[0].read_text(encoding="utf-8") == original


def test_cli_add_pin_rejects_duplicate(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        "d:dom0 c:xfce4-terminal",
        "--write",
    ])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "PIN rule already exists for target: d:dom0 c:xfce4-terminal" in captured.out
    assert "Use modify-pin" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))


def test_cli_modify_pin_preview_reports_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "modify-pin",
        "--config",
        str(config_path),
        "--old-rule",
        "d:dom0 c:xfce4-terminal",
        "--new-rule",
        "d:dom0 c:qubes-qube-manager",
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned PIN modify: d:dom0 c:qubes-qube-manager" in captured.out
    assert "Old rule: d:dom0 c:xfce4-terminal" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original


def test_cli_delete_pin_write_removes_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    exit_code = main([
        "delete-pin",
        "--config",
        str(config_path),
        "--rule",
        "d:dom0 c:xfce4-terminal",
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: PIN rule deleted: d:dom0 c:xfce4-terminal" in captured.out
    assert "xfce4-terminal" not in saved


def test_cli_add_exclude_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:qubes-app-menu",
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned EXCLUDE add: c:qubes-app-menu" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original


def test_cli_add_exclude_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:qubes-app-menu",
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.*.bak"))

    assert exit_code == 0
    assert "OK: EXCLUDE rule added: c:qubes-app-menu" in captured.out
    assert "Backup:" in captured.out
    assert '"c:qubes-app-menu",' in saved
    assert backups
    assert backups[0].read_text(encoding="utf-8") == original


def test_cli_modify_exclude_preview_reports_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:qubes-app-menu",
        "--write",
    ])
    with_added = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "modify-exclude",
        "--config",
        str(config_path),
        "--old-rule",
        "c:qubes-app-menu",
        "--new-rule",
        "d:dom0 c:qubes-app-menu",
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Planned EXCLUDE modify: d:dom0 c:qubes-app-menu" in captured.out
    assert "Old rule: c:qubes-app-menu" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == with_added


def test_cli_delete_exclude_write_removes_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:qubes-app-menu",
        "--write",
    ])

    exit_code = main([
        "delete-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:qubes-app-menu",
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert "OK: EXCLUDE rule deleted: c:qubes-app-menu" in captured.out
    assert "qubes-app-menu" not in saved


def test_cli_target_rule_rejects_invalid_rule_and_leaves_config_unchanged(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        "c:okular g:half_left",
        "--write",
    ])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "EXCLUDE rule must not include g:" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))
