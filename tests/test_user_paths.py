from pathlib import Path

from d2wc.core.user_paths import (
    default_managed_config_dir,
    default_managed_config_path,
    devilspie2_entry_path,
    is_d2wc_managed_lua_file,
    is_safe_devilspie2_integration_target,
    is_safe_managed_filename,
)


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
    assert not is_safe_managed_filename('../d2wc.lua')
    assert not is_safe_managed_filename('my/d2wc.lua')


def test_managed_lua_marker_detection(tmp_path: Path) -> None:
    managed = tmp_path / 'managed.lua'
    managed.write_text('-- d2wc managed\nlocal EXCLUDE = {}\n', encoding='utf-8')
    plain = tmp_path / 'plain.lua'
    plain.write_text('local EXCLUDE = {}\n', encoding='utf-8')
    assert is_d2wc_managed_lua_file(managed)
    assert not is_d2wc_managed_lua_file(plain)


def test_symlink_safety_decisions(tmp_path: Path) -> None:
    target = tmp_path / 'd2wc.lua'
    assert is_safe_devilspie2_integration_target(target)

    unmanaged = tmp_path / 'unmanaged.lua'
    unmanaged.write_text('print("hello")\n', encoding='utf-8')
    assert not is_safe_devilspie2_integration_target(unmanaged)

    managed = tmp_path / 'managed.lua'
    managed.write_text('-- d2wc managed\n', encoding='utf-8')
    assert is_safe_devilspie2_integration_target(managed)

    link = tmp_path / 'link.lua'
    link.symlink_to(managed)
    assert is_safe_devilspie2_integration_target(link)
