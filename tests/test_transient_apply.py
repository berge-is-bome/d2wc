from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from d2wc.core.transient_apply import (
    TRANSIENT_CONFIG_FILENAME,
    NoTransientApplyNeeded,
    apply_transient_rule_after_save,
    build_transient_apply_plan,
)
from d2wc.test_config_actions import ManagedSectionActionRequest, apply_managed_section_action


FULL_CONFIG = '''
local D2WC_MANAGED = true
local EXCLUDE = {
  "d:old c:excluded",
  "d:work c:target",
}
local PIN = {
  "d:old c:pinned",
  "d:work c:route-target",
  "d:work",
  "c:route-target",
  "d:other c:route-target",
  "d:work c:other",
  "c:elsewhere",
}
local WORKSPACE_ROUTES = {
  [1] = { "d:old c:routed", },
  [4] = { "d:work c:route-target", "d:other c:route", },
}
local GEOM = {
  half_left = { x = 0, y = 0, w = 1920, h = 2115 },
  centered_mid = { x = 10, y = 20, w = 800, h = 600 },
}
local WORKSPACE_PLACEMENT = {
  "d:personal c:okular g:half_left",
  "d:work c:example g:centered_mid",
}
local LEFT_EDGE_CORRECTION = {
  "d:old c:left le:pos1",
}

local function runtime_helper()
  return true
end

local function apply_workspace()
  set_window_workspace(4)
end

local function apply_pin()
  pin_window()
end

runtime_helper()
'''


class FakeTempDir:
    def __init__(self, path: Path):
        self.path = path

    def __enter__(self) -> str:
        self.path.mkdir(parents=True, exist_ok=True)
        return str(self.path)

    def __exit__(self, exc_type, exc, tb) -> None:
        shutil.rmtree(self.path, ignore_errors=True)


class FakeLongRunningProcess:
    pid = 4242

    def __init__(self) -> None:
        self.wait_calls: list[float | None] = []

    def wait(self, timeout=None) -> int:
        self.wait_calls.append(timeout)
        if timeout == 0:
            raise subprocess.TimeoutExpired("devilspie2", timeout)
        return 0


class FakeStubbornProcess:
    pid = 4343

    def wait(self, timeout=None) -> int:
        raise subprocess.TimeoutExpired("devilspie2", timeout)


def write_config(tmp_path: Path, source: str = FULL_CONFIG) -> Path:
    path = tmp_path / "managed.lua"
    path.write_text(source, encoding="utf-8")
    return path


def test_transient_plan_contains_only_selected_exclude_rule(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    plan = build_transient_apply_plan(
        path,
        ManagedSectionActionRequest(section="EXCLUDE", operation="modify", rule="d:work c:target"),
    )

    assert 'local D2WC_MANAGED = true' in plan.source
    assert '"d:work c:target",' in plan.source
    assert '"d:old c:excluded",' not in plan.source
    assert '"d:old c:pinned",' not in plan.source
    assert '"d:personal c:okular g:half_left",' not in plan.source
    assert "runtime_helper" in plan.source


def test_workspace_placement_plan_includes_only_referenced_geometry(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    plan = build_transient_apply_plan(
        path,
        ManagedSectionActionRequest(
            section="WORKSPACE_PLACEMENT",
            operation="add",
            rule="d:work c:example g:centered_mid",
        ),
    )

    assert '"d:work c:example g:centered_mid",' in plan.source
    assert '"d:personal c:okular g:half_left",' not in plan.source
    assert "centered_mid" in plan.source
    assert "x = 10" in plan.source
    assert "half_left" not in plan.source


def test_workspace_route_plan_contains_only_selected_route(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    plan = build_transient_apply_plan(
        path,
        ManagedSectionActionRequest(
            section="WORKSPACE_ROUTES",
            operation="modify",
            workspace=4,
            rule="d:work c:route-target",
        ),
    )

    assert '[4] = { "d:work c:route-target", },' in plan.source
    assert "d:old c:routed" not in plan.source
    assert "d:other c:route" not in plan.source


def test_workspace_route_plan_includes_matching_pin_context(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    plan = build_transient_apply_plan(
        path,
        ManagedSectionActionRequest(
            section="WORKSPACE_ROUTES",
            operation="modify",
            workspace=4,
            rule="d:work c:route-target",
        ),
    )

    assert '[4] = { "d:work c:route-target", },' in plan.source
    assert '"d:work c:route-target",' in plan.source
    assert '"d:work",' in plan.source
    assert '"c:route-target",' in plan.source
    assert plan.source.index("set_window_workspace") < plan.source.index("pin_window")


def test_workspace_route_plan_excludes_unrelated_pin_context(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    plan = build_transient_apply_plan(
        path,
        ManagedSectionActionRequest(
            section="WORKSPACE_ROUTES",
            operation="modify",
            workspace=4,
            rule="d:work c:route-target",
        ),
    )

    assert '"d:other c:route-target",' not in plan.source
    assert '"d:work c:other",' not in plan.source
    assert '"c:elsewhere",' not in plan.source
    assert '"d:old c:pinned",' not in plan.source


@pytest.mark.parametrize(
    "action_request",
    [
        ManagedSectionActionRequest(section="GEOM", operation="add", profile_name="new", x=1, y=2, w=100, h=100),
        ManagedSectionActionRequest(section="PIN", operation="delete", existing_rule="d:old c:pinned"),
    ],
)
def test_geom_and_delete_actions_do_not_build_transient_plan(tmp_path: Path, action_request: ManagedSectionActionRequest) -> None:
    path = write_config(tmp_path)

    with pytest.raises(NoTransientApplyNeeded):
        build_transient_apply_plan(path, action_request)


def test_transient_apply_writes_d2wc_lua_launches_folder_terminates_group_and_cleans_up(tmp_path: Path) -> None:
    path = write_config(tmp_path)
    temp_dir = tmp_path / "transient"
    launched: dict[str, object] = {}
    killed: list[tuple[int, int]] = []
    slept: list[float] = []
    process = FakeLongRunningProcess()

    def launcher(args, **kwargs):
        launched["args"] = args
        launched["kwargs"] = kwargs
        launched["source"] = (Path(args[2]) / TRANSIENT_CONFIG_FILENAME).read_text(encoding="utf-8")
        return process

    result = apply_transient_rule_after_save(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:target"),
        command_resolver=lambda command: command,
        temp_dir_factory=lambda: FakeTempDir(temp_dir),
        subprocess_launcher=launcher,
        sleep=slept.append,
        kill_process_group=lambda pid, sig: killed.append((pid, sig)),
        settle_timeout=0.25,
        terminate_timeout=0.5,
    )

    assert result.applied
    assert launched["args"] == ["devilspie2", "--folder", str(temp_dir)]
    assert launched["kwargs"]["start_new_session"] is True
    assert launched["kwargs"]["stdout"] is subprocess.DEVNULL
    assert launched["kwargs"]["stderr"] is subprocess.DEVNULL
    assert TRANSIENT_CONFIG_FILENAME == "d2wc.lua"
    assert '"d:work c:target",' in launched["source"]
    assert '"d:old c:pinned",' not in launched["source"]
    assert slept == [0.25]
    assert killed == [(process.pid, 15)]
    assert not temp_dir.exists()


def test_transient_apply_cleans_up_after_launch_failure(tmp_path: Path) -> None:
    path = write_config(tmp_path)
    temp_dir = tmp_path / "transient"

    def launcher(args, **kwargs):
        assert (temp_dir / TRANSIENT_CONFIG_FILENAME).exists()
        raise OSError("boom")

    result = apply_transient_rule_after_save(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:target"),
        command_resolver=lambda command: command,
        temp_dir_factory=lambda: FakeTempDir(temp_dir),
        subprocess_launcher=launcher,
    )

    assert not result.applied
    assert "Runtime apply warning: could not start devilspie2: boom" in result.warning
    assert not temp_dir.exists()


def test_transient_apply_cleans_up_after_termination_failure(tmp_path: Path) -> None:
    path = write_config(tmp_path)
    temp_dir = tmp_path / "transient"
    killed: list[tuple[int, int]] = []

    result = apply_transient_rule_after_save(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:target"),
        command_resolver=lambda command: command,
        temp_dir_factory=lambda: FakeTempDir(temp_dir),
        subprocess_launcher=lambda args, **kwargs: FakeStubbornProcess(),
        sleep=lambda seconds: None,
        kill_process_group=lambda pid, sig: killed.append((pid, sig)),
    )

    assert not result.applied
    assert "did not exit cleanly" in result.warning
    assert killed == [(4343, 15), (4343, 9)]
    assert not temp_dir.exists()


def test_missing_devilspie2_returns_warning_without_launching(tmp_path: Path) -> None:
    path = write_config(tmp_path)

    result = apply_transient_rule_after_save(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:target"),
        command_resolver=lambda command: None,
        subprocess_launcher=lambda *args, **kwargs: pytest.fail("should not launch"),
    )

    assert result.attempted
    assert not result.applied
    assert "could not find devilspie2" in result.warning


def test_apply_calls_transient_helper_only_after_successful_save(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = write_config(tmp_path)
    calls: list[ManagedSectionActionRequest] = []

    def fake_transient(config_path, request):
        calls.append(request)
        return type("Result", (), {"warning": ""})()

    monkeypatch.setattr("d2wc.test_config_actions.apply_transient_rule_after_save", fake_transient)

    ok_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="PIN", operation="add", rule="d:work c:new"),
    )
    failed_result = apply_managed_section_action(
        path,
        ManagedSectionActionRequest(section="PIN", operation="modify", rule="d:work c:no-existing"),
    )

    assert ok_result.ok
    assert not failed_result.ok
    assert len(calls) == 1
    assert calls[0].rule == "d:work c:new"
