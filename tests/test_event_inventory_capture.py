import subprocess
from pathlib import Path
from typing import Any

from d2wc.event_inventory import KnownWindowTarget
from d2wc.event_inventory_capture import (
    PROBE_SCRIPT,
    PROBE_SCRIPT_NAME,
    KnownWindowInventoryStreamParser,
    capture_known_window_inventory,
    stream_known_window_inventory,
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


def test_stream_parser_emits_new_targets_from_startup_and_later_events() -> None:
    parser = KnownWindowInventoryStreamParser()

    startup_events = parser.feed_text(
        "Domain: personal\n"
        "Window Type: WINDOW_TYPE_NORMAL\n"
        "Class instance name: personal:Navigator\n"
        "\n"
        "Domain: personal\n"
        "Window Type: WINDOW_TYPE_NORMAL\n"
        "Class instance name: personal:Navigator\n"
        "\n"
    )
    later_events = parser.feed_text(
        "Domain: work\n"
        "Window Type: WINDOW_TYPE_NORMAL\n"
        "Class instance name: work:Terminal\n"
        "\n"
    )

    assert [event.targets for event in startup_events] == [
        (KnownWindowTarget(machine="personal", application="navigator"),),
        (),
    ]
    assert [event.targets for event in later_events] == [
        (KnownWindowTarget(machine="work", application="terminal"),),
    ]


def test_stream_parser_flushes_final_unterminated_block() -> None:
    parser = KnownWindowInventoryStreamParser()
    assert parser.feed_text(
        "Domain: work\n"
        "Window Type: WINDOW_TYPE_NORMAL\n"
        "Class instance name: work:Terminal\n"
    ) == ()

    events = parser.finish()

    assert len(events) == 1
    assert events[0].targets == (KnownWindowTarget(machine="work", application="terminal"),)


def test_stream_known_window_inventory_runs_probe_and_yields_events() -> None:
    fake_processes: list[FakeProcess] = []

    def popen_factory(command, **kwargs):
        probe_dir = Path(command[-1])
        probe_path = probe_dir / PROBE_SCRIPT_NAME
        assert probe_path.read_text(encoding="utf-8") == PROBE_SCRIPT
        assert kwargs["stdout"] == subprocess.PIPE
        assert kwargs["stderr"] == subprocess.STDOUT
        assert kwargs["text"] is True

        process = FakeProcess(
            [
                "Domain: personal\n",
                "Window Type: WINDOW_TYPE_NORMAL\n",
                "Class instance name: personal:Navigator\n",
                "\n",
                "Domain: work\n",
                "Window Type: WINDOW_TYPE_NORMAL\n",
                "Class instance name: work:Terminal\n",
                "\n",
            ]
        )
        fake_processes.append(process)
        return process

    events = tuple(stream_known_window_inventory(popen_factory=popen_factory))

    assert [event.targets for event in events] == [
        (KnownWindowTarget(machine="personal", application="navigator"),),
        (KnownWindowTarget(machine="work", application="terminal"),),
    ]
    assert fake_processes[0].terminated is False


class FakeProcess:
    def __init__(self, stdout_lines: list[str]) -> None:
        self.stdout = iter(stdout_lines)
        self.terminated = False

    def poll(self) -> int:
        return 0

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout=None) -> int:
        return 0
