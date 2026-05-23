from pathlib import Path

from d2wc.core.backup import extract_backup_member_text, list_backup_members
from d2wc.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_PIN_RULE = "d:dom0 c:d2wc-test-pin"
TEST_PIN_RULE_UPDATED = "d:dom0 c:d2wc-test-pin-updated"
TEST_EXCLUDE_RULE = "c:d2wc-test-exclude"
TEST_EXCLUDE_RULE_UPDATED = "d:dom0 c:d2wc-test-exclude"


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
        TEST_PIN_RULE,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert f"Planned PIN add: {TEST_PIN_RULE}" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert "Run again with --write to save." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_add_pin_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        TEST_PIN_RULE,
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.bak.tgz"))

    assert exit_code == 0
    assert f"OK: PIN rule added: {TEST_PIN_RULE}" in captured.out
    assert "Backup archive:" in captured.out
    assert f'"{TEST_PIN_RULE}",' in saved
    assert backups
    members = list_backup_members(backups[0])
    assert extract_backup_member_text(backups[0], members[-1]) == original


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
    assert not list(tmp_path.glob("*.bak*"))


def test_cli_modify_pin_preview_reports_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        TEST_PIN_RULE,
        "--write",
    ])
    with_added = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "modify-pin",
        "--config",
        str(config_path),
        "--old-rule",
        TEST_PIN_RULE,
        "--new-rule",
        TEST_PIN_RULE_UPDATED,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Planned PIN modify: {TEST_PIN_RULE_UPDATED}" in captured.out
    assert f"Old rule: {TEST_PIN_RULE}" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == with_added
    assert with_added != original


def test_cli_delete_pin_write_removes_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    main([
        "add-pin",
        "--config",
        str(config_path),
        "--rule",
        TEST_PIN_RULE,
        "--write",
    ])

    exit_code = main([
        "delete-pin",
        "--config",
        str(config_path),
        "--rule",
        TEST_PIN_RULE,
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert f"OK: PIN rule deleted: {TEST_PIN_RULE}" in captured.out
    assert f'"{TEST_PIN_RULE}",' not in saved


def test_cli_add_exclude_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        TEST_EXCLUDE_RULE,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Planned EXCLUDE add: {TEST_EXCLUDE_RULE}" in captured.out
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
        TEST_EXCLUDE_RULE,
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.bak.tgz"))

    assert exit_code == 0
    assert f"OK: EXCLUDE rule added: {TEST_EXCLUDE_RULE}" in captured.out
    assert "Backup archive:" in captured.out
    assert f'"{TEST_EXCLUDE_RULE}",' in saved
    assert backups
    members = list_backup_members(backups[0])
    assert extract_backup_member_text(backups[0], members[-1]) == original


def test_cli_modify_exclude_preview_reports_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)

    main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        TEST_EXCLUDE_RULE,
        "--write",
    ])
    with_added = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "modify-exclude",
        "--config",
        str(config_path),
        "--old-rule",
        TEST_EXCLUDE_RULE,
        "--new-rule",
        TEST_EXCLUDE_RULE_UPDATED,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Planned EXCLUDE modify: {TEST_EXCLUDE_RULE_UPDATED}" in captured.out
    assert f"Old rule: {TEST_EXCLUDE_RULE}" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == with_added


def test_cli_delete_exclude_write_removes_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    main([
        "add-exclude",
        "--config",
        str(config_path),
        "--rule",
        TEST_EXCLUDE_RULE,
        "--write",
    ])

    exit_code = main([
        "delete-exclude",
        "--config",
        str(config_path),
        "--rule",
        TEST_EXCLUDE_RULE,
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")

    assert exit_code == 0
    assert f"OK: EXCLUDE rule deleted: {TEST_EXCLUDE_RULE}" in captured.out
    assert f'"{TEST_EXCLUDE_RULE}",' not in saved


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
    assert not list(tmp_path.glob("*.bak*"))
