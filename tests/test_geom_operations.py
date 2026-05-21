from pathlib import Path

import pytest

from d2wc.core.geom_operations import (
    GeometryOperationError,
    GeometryProfileExistsError,
    GeometryProfileInUseError,
    GeometryProfileNotFoundError,
    add_geometry_profile_to_source,
    delete_geometry_profile_from_source,
    modify_geometry_profile_in_source,
)
from d2wc.core.lua_blocks import ManagedBlockParser
from d2wc.core.managed_config import GeometryProfile
from d2wc.core.validation import validate_managed_blocks


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_add_geometry_profile_appends_profile_and_preserves_existing_comments() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  -- geometry note
  half_left = { x = 0, y = 0, w = 100, h = 100 }, -- left note
}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = add_geometry_profile_to_source(
        source,
        GeometryProfile(name="custom_left", x=10, y=20, w=300, h=400),
    )

    assert result.validation.ok
    assert result.operation == "add"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "  -- geometry note" in result.source
    assert "-- left note" in result.source
    assert "  custom_left" in result.source
    assert "x = 10" in result.source
    assert "y = 20" in result.source
    assert "w = 300" in result.source
    assert "h = 400" in result.source

    parsed = ManagedBlockParser().parse(result.source)
    validation = validate_managed_blocks(parsed.blocks)
    assert validation.ok


def test_add_geometry_profile_rejects_duplicate() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    with pytest.raises(GeometryProfileExistsError, match="geometry profile already exists: half_left"):
        add_geometry_profile_to_source(
            source,
            GeometryProfile(name="half_left", x=1, y=2, w=300, h=400),
        )


def test_modify_geometry_profile_updates_existing_profile() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 }, -- left note
}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
'''

    result = modify_geometry_profile_in_source(
        source,
        GeometryProfile(name="half_left", x=9, y=8, w=700, h=600),
    )

    assert result.validation.ok
    assert result.operation == "modify"
    assert "x = 9" in result.source
    assert "y = 8" in result.source
    assert "w = 700" in result.source
    assert "h = 600" in result.source
    assert "-- left note" in result.source


def test_modify_geometry_profile_rejects_missing_profile() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    with pytest.raises(GeometryProfileNotFoundError, match="geometry profile not found: not_there"):
        modify_geometry_profile_in_source(
            source,
            GeometryProfile(name="not_there", x=1, y=2, w=300, h=400),
        )


def test_delete_geometry_profile_removes_unused_profile_and_preserves_notes() -> None:
    source = '''before
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  -- geometry note
  throwaway = { x = 0, y = 0, w = 100, h = 100 }, -- remove me
  keep_me = { x = 5, y = 6, w = 300, h = 400 }, -- keep me
}
local WORKSPACE_PLACEMENT = {}
local LEFT_EDGE_CORRECTION = {}
after
'''

    result = delete_geometry_profile_from_source(source, "throwaway")

    assert result.validation.ok
    assert result.profile_name == "throwaway"
    assert "before\n" in result.source
    assert "\nafter\n" in result.source
    assert "  -- geometry note" in result.source
    assert "throwaway" not in result.source
    assert "remove me" not in result.source
    assert "keep_me" in result.source
    assert "-- keep me" in result.source


def test_delete_geometry_profile_rejects_missing_profile() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    with pytest.raises(GeometryProfileNotFoundError, match="geometry profile not found: not_there"):
        delete_geometry_profile_from_source(source, "not_there")


def test_delete_geometry_profile_rejects_profile_used_by_placement_rule() -> None:
    source = '''
local EXCLUDE = {}
local PIN = {}
local WORKSPACE_ROUTES = {}
local GEOM = {
  half_left = { x = 0, y = 0, w = 100, h = 100 },
}
local WORKSPACE_PLACEMENT = {
  "c:okular g:half_left",
}
local LEFT_EDGE_CORRECTION = {}
'''

    with pytest.raises(GeometryProfileInUseError, match="still used by WORKSPACE_PLACEMENT: half_left"):
        delete_geometry_profile_from_source(source, "half_left")


def test_add_geometry_profile_rejects_invalid_profile_name() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    with pytest.raises(GeometryOperationError, match="invalid geometry profile name"):
        add_geometry_profile_to_source(
            source,
            GeometryProfile(name="1bad", x=1, y=2, w=300, h=400),
        )


def test_add_geometry_profile_rejects_too_small_profile() -> None:
    source = (REPO_ROOT / "src" / "d2wc.lua").read_text(encoding="utf-8")

    with pytest.raises(GeometryOperationError, match="width must be at least 10"):
        add_geometry_profile_to_source(
            source,
            GeometryProfile(name="tiny", x=1, y=2, w=9, h=400),
        )
