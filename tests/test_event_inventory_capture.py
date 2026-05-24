import subprocess
from pathlib import Path
from typing import Any

from d2wc.event_inventory import KnownWindowTarget
from d2wc.event_inventory_capture import (
    PROBE_SCRIPT,
    PROBE_SCRIPT_NAME,
    capture_known_window_inventory,
)


def test_capture_known_window_inventory_writes_probe_and_builds_targets() -> None:
    calls: list[dict[str, Any]] = []

    def runner(command, **kwargs):
        calls.append({"command": command, **kwargs})
        probe_dir = Path(command[-1])
        probe_path = probe_dir / PROBE_SCRIPT_NAME
        assert probe_path.read_text(encoding="utf-8") == PROBE_SCRIPT
        assert oct(probe_path.stat().st_mode & 0o777) == "0o600"
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "Domain: personal\n"
                "Window Type: WINDOW_TYPE_NORMAL\n"
                "Class instance name: personal:Navigator\n"
                "\n"
                "Domain: personal\n"
                "Window Type: WINDOW_TYPE_NORMAL\n"
                "Class instance name: personal:Navigator\n"
                "\n"
                "Domain: work\n"
                "Window Type: WINDOW_TYPE_DIALOG\n"
                "Class instance name: work:Dialog\n"
            ),
            stderr="",
        )

    result = capture_known_window_inventory(timeout_seconds=0.25, runner=runner)

    assert calls == [
        {
            "command": ["devilspie2", "--debug", "--folder", calls[0]["command"][-1]],
            "check": False,
            "capture_output": True,
            "text": True,
            "timeout": 0.25,
        }
    ]
    assert result.timed_out is False
    assert result.returncode == 0
    assert result.targets == (KnownWindowTarget(machine="personal", application="navigator"),)


def test_capture_known_window_inventory_preserves_timeout_output() -> None:
    def runner(command, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd=command,
            timeout=kwargs["timeout"],
            output=(
                "Domain: work\n"
                "Window Type: WINDOW_TYPE_NORMAL\n"
                "Class instance name: work:Terminal\n"
            ),
            stderr="",
        )

    result = capture_known_window_inventory(timeout_seconds=0.1, runner=runner)

    assert result.timed_out is True
    assert result.returncode is None
    assert result.targets == (KnownWindowTarget(machine="work", application="terminal"),)
    assert result.raw_text == (
        "Domain: work\n"
        "Window Type: WINDOW_TYPE_NORMAL\n"
        "Class instance name: work:Terminal\n"
    )
