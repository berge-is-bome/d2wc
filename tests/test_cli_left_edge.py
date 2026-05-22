from pathlib import Path

from d2wc.cli import main


REPO_ROOT = Path(__file__).resolve().parents[1]
TEST_LEFT_EDGE_RULE = "d:dom0 c:d2wc-test-left-edge le:pos1"
TEST_LEFT_EDGE_RULE_UPDATED = "d:dom0 c:d2wc-test-left-edge le:pos2"


def copy_current_config(tmp_path: Path) -> Path:
    source = REPO_ROOT / "src" / "d2wc.lua"
    target = tmp_path / "d2wc.lua"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_cli_add_left_edge_preview_does_not_modify_config(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-left-edge",
        "--config",
        str(config_path),
        "--rule",
        TEST_LEFT_EDGE_RULE,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Config: {config_path}" in captured.out
    assert f"Planned LEFT_EDGE_CORRECTION add: {TEST_LEFT_EDGE_RULE}" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))


def test_cli_add_left_edge_write_updates_config_and_creates_backup(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-left-edge",
        "--config",
        str(config_path),
        "--rule",
        TEST_LEFT_EDGE_RULE,
        "--write",
    ])

    captured = capsys.readouterr()
    saved = config_path.read_text(encoding="utf-8")
    backups = list(tmp_path.glob("d2wc.lua.*.bak"))

    assert exit_code == 0
    assert f"OK: LEFT_EDGE_CORRECTION rule added: {TEST_LEFT_EDGE_RULE}" in captured.out
    assert "Backup:" in captured.out
    assert f'"{TEST_LEFT_EDGE_RULE}",' in saved
    assert backups
    assert backups[0].read_text(encoding="utf-8") == original


def test_cli_add_left_edge_rejects_duplicate_target(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "add-left-edge",
        "--config",
        str(config_path),
        "--rule",
        "d:dom0 c:qubes-qube-manager le:pos2",
        "--write",
    ])

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "left-edge rule already exists for target: d:dom0 c:qubes-qube-manager" in captured.out
    assert "Use modify-left-edge" in captured.out
    assert config_path.read_text(encoding="utf-8") == original
    assert not list(tmp_path.glob("*.bak"))


def test_cli_modify_left_edge_preview_reports_old_rule(tmp_path, capsys) -> None:
    config_path = copy_current_config(tmp_path)
    original = config_path.read_text(encoding="utf-8")

    main([
        "add-left-edge",
        "--config",
        str(config_path),
        "--rule",
        TEST_LEFT_EDGE_RULE,
        "--write",
    ])
    with_added = config_path.read_text(encoding="utf-8")

    exit_code = main([
        "modify-left-edge",
        "--config",
        str(config_path),
        "--old-rule",
        TEST_LEFT_EDGE_RULE,
        "--new-rule",
        TEST_LEFT_EDGE_RULE_UPDATED,
    ])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert f"Planned LEFT_EDGE_CORRECTION modify: {TEST_LEFT_EDGE_RULE_UPDATED}" in captured.out
    assert f"Old rule: {TEST_LEFT_EDGE_RULE}" in captured.out
    assert "Preview only: no files were modified." in captured.out
    assert config_path.read_text(encoding="utf-8") == with_added
    assert with_added != original
