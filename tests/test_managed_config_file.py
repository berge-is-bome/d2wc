from pathlib import Path

from d2wc.managed_config_file import (
    activate_managed_config,
    active_managed_config_path,
    load_managed_config_snapshot,
    save_managed_config_as,
)

VALID_SOURCE = (Path(__file__).resolve().parents[1] / 'src' / 'd2wc.lua').read_text(encoding='utf-8')
SYNTHETIC_PIN_MARKER = 'd:pytest-symlink-target'


def test_load_managed_config_snapshot_validates_file(tmp_path: Path) -> None:
    config = tmp_path / '.config' / 'd2wc' / 'lua' / 'd2wc.lua'
    config.parent.mkdir(parents=True)
    config.write_text(VALID_SOURCE, encoding='utf-8')

    snapshot = load_managed_config_snapshot(config)

    assert snapshot.ok
    assert snapshot.path == config


def test_load_managed_config_snapshot_uses_active_symlink_target(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed_dir = tmp_path / '.config' / 'd2wc' / 'lua'
    managed_dir.mkdir(parents=True)
    default = managed_dir / 'd2wc.lua'
    active = managed_dir / 'file-a.lua'
    default.write_text(VALID_SOURCE, encoding='utf-8')
    # Synthetic marker used only to prove that the symlink target file was loaded.
    active.write_text(VALID_SOURCE.replace('local PIN = {', f'local PIN = {{\n  "{SYNTHETIC_PIN_MARKER}",'), encoding='utf-8')
    entry = tmp_path / '.config' / 'devilspie2' / 'd2wc.lua'
    entry.parent.mkdir(parents=True)
    entry.symlink_to(active)

    snapshot = load_managed_config_snapshot()

    assert active_managed_config_path() == active.resolve()
    assert snapshot.ok
    assert snapshot.path == active.resolve()
    assert snapshot.config is not None
    assert SYNTHETIC_PIN_MARKER in snapshot.config.pin


def test_load_managed_config_snapshot_falls_back_to_default_without_safe_symlink(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed_dir = tmp_path / '.config' / 'd2wc' / 'lua'
    managed_dir.mkdir(parents=True)
    default = managed_dir / 'd2wc.lua'
    default.write_text(VALID_SOURCE, encoding='utf-8')

    assert active_managed_config_path() == default
    assert load_managed_config_snapshot().path == default


def test_save_managed_config_as_requires_managed_directory(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed_dir = tmp_path / '.config' / 'd2wc' / 'lua'
    managed_dir.mkdir(parents=True)
    source = managed_dir / 'd2wc.lua'
    source.write_text(VALID_SOURCE, encoding='utf-8')

    outside = tmp_path / 'outside.lua'
    result = save_managed_config_as(source, outside)

    assert not result.ok
    assert 'managed configs must be saved under' in result.message


def test_save_managed_config_as_copies_valid_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed_dir = tmp_path / '.config' / 'd2wc' / 'lua'
    managed_dir.mkdir(parents=True)
    source = managed_dir / 'd2wc.lua'
    target = managed_dir / 'work.lua'
    source.write_text(VALID_SOURCE, encoding='utf-8')

    result = save_managed_config_as(source, target)

    assert result.ok
    assert result.path == target
    assert target.read_text(encoding='utf-8') == VALID_SOURCE


def test_activate_managed_config_creates_symlink(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed = tmp_path / '.config' / 'd2wc' / 'lua' / 'd2wc.lua'
    managed.parent.mkdir(parents=True)
    managed.write_text(VALID_SOURCE, encoding='utf-8')

    result = activate_managed_config(managed)

    entry = tmp_path / '.config' / 'devilspie2' / 'd2wc.lua'
    assert result.ok
    assert entry.is_symlink()
    assert entry.resolve() == managed.resolve()


def test_activate_managed_config_leaves_unmanaged_regular_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed = tmp_path / '.config' / 'd2wc' / 'lua' / 'd2wc.lua'
    managed.parent.mkdir(parents=True)
    managed.write_text(VALID_SOURCE, encoding='utf-8')
    entry = tmp_path / '.config' / 'devilspie2' / 'd2wc.lua'
    entry.parent.mkdir(parents=True)
    entry.write_text('print("user script")\n', encoding='utf-8')

    result = activate_managed_config(managed)

    assert not result.ok
    assert entry.is_file()
    assert not entry.is_symlink()
    assert entry.read_text(encoding='utf-8') == 'print("user script")\n'


def test_activate_managed_config_leaves_external_symlink(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    managed = tmp_path / '.config' / 'd2wc' / 'lua' / 'd2wc.lua'
    managed.parent.mkdir(parents=True)
    managed.write_text(VALID_SOURCE, encoding='utf-8')
    external = tmp_path / 'external.lua'
    external.write_text('print("external")\n', encoding='utf-8')
    entry = tmp_path / '.config' / 'devilspie2' / 'd2wc.lua'
    entry.parent.mkdir(parents=True)
    entry.symlink_to(external)

    result = activate_managed_config(managed)

    assert not result.ok
    assert entry.is_symlink()
    assert entry.resolve() == external.resolve()
