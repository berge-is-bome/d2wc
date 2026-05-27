from pathlib import Path

from d2wc.core.user_paths import (
    default_managed_config_dir,
    default_managed_config_path,
    devilspie2_entry_path,
    is_d2wc_managed_lua_file,
    is_safe_devilspie2_integration_target,
    is_safe_managed_filename,
)

VALID_SOURCE = (Path(__file__).resolve().parents[1] / 'src' / 'd2wc.lua').read_text(encoding='utf-8')


def test_default_managed_paths() -> None:
    home = Path('/tmp/example-home')
    assert default_managed_config_dir(home) == home / '.config/d2wc/lua'
    assert default_managed_config_path(home) == home / '.config/d2wc/lua/d2wc.lua'
    assert devilspie2_entry_path(home) == home / '.config/devilspie2/d2wc.lua'


def test_safe_managed_filename_validation() -> None:
    assert is_safe_managed_filename('d2wc.lua')
    assert is_safe_managed_filename('profile-2.lua')
    assert not is_safe_managed_filename('')
    assert not is_safe_managed_filename('d2wc')
    assert not is_safe_managed_filename('d2wc.txt')
    assert not is_safe_managed_filename('../d2wc.lua')
    assert not is_safe_managed_filename('my/d2wc.lua')
    assert not is_safe_managed_filename('bad..name.lua')


def test_marker_only_is_not_managed_lua_file(tmp_path: Path) -> None:
    marker_only = tmp_path / 'marker-only.lua'
    marker_only.write_text('-- d2wc managed\n', encoding='utf-8')
    assert not is_d2wc_managed_lua_file(marker_only)


def test_valid_managed_lua_file_passes_parser_and_validation(tmp_path: Path) -> None:
    managed = tmp_path / 'managed.lua'
    managed.write_text(VALID_SOURCE, encoding='utf-8')
    assert is_d2wc_managed_lua_file(managed)


def test_symlink_safety_decisions(tmp_path: Path) -> None:
    managed_dir = tmp_path / '.config' / 'd2wc' / 'lua'
    managed_dir.mkdir(parents=True)
    entry = tmp_path / '.config' / 'devilspie2' / 'd2wc.lua'
    entry.parent.mkdir(parents=True)

    assert is_safe_devilspie2_integration_target(entry, managed_dir)

    unmanaged = entry
    unmanaged.write_text('print("hello")\n', encoding='utf-8')
    assert not is_safe_devilspie2_integration_target(unmanaged, managed_dir)
    unmanaged.unlink()

    managed_file = managed_dir / 'd2wc.lua'
    managed_file.write_text(VALID_SOURCE, encoding='utf-8')
    entry.symlink_to(managed_file)
    assert is_safe_devilspie2_integration_target(entry, managed_dir)

    entry.unlink()
    outside = tmp_path / 'outside.lua'
    outside.write_text(VALID_SOURCE, encoding='utf-8')
    entry.symlink_to(outside)
    assert not is_safe_devilspie2_integration_target(entry, managed_dir)
