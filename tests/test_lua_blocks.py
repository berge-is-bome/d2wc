from pathlib import Path

import pytest

from d2wc.core.lua_blocks import MANAGED_BLOCK_NAMES, ManagedBlockParser


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parser_finds_all_managed_blocks_in_current_lua_script() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    result = ManagedBlockParser().parse(source)

    assert tuple(result.blocks) == MANAGED_BLOCK_NAMES
    for name in MANAGED_BLOCK_NAMES:
        block = result.blocks[name]
        assert block.name == name
        assert block.text.startswith(f"local {name} =")
        assert block.text.rstrip().endswith("}")


def test_parser_reports_missing_managed_block() -> None:
    source = "local EXCLUDE = {}\n"

    with pytest.raises(ValueError, match="managed block not found: PIN"):
        ManagedBlockParser().parse(source)


def test_parser_ignores_braces_inside_strings() -> None:
    source = "local EXCLUDE = { \"c:weird-{class}\" }\n"

    block = ManagedBlockParser()._find_block(source, "EXCLUDE")

    assert block.text == "local EXCLUDE = { \"c:weird-{class}\" }"
