"""Devilspie2 debug capture and stream parsing for known-window inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Callable, Iterator, Sequence

from d2wc.event_inventory import (
    KnownWindowCandidate,
    KnownWindowTarget,
    build_known_window_targets,
    parse_known_window_candidates,
)

DEFAULT_CAPTURE_TIMEOUT_SECONDS = 2.0
PROBE_SCRIPT_NAME = "d2wc-known-window-inventory.lua"
PROBE_SCRIPT = """local function d2wc_value(value)
  if value == nil then
    return ""
  end
  return tostring(value)
end

debug_print("Domain: " .. d2wc_value(get_window_property( '_QUBES_VMNAME' )))
debug_print("Window Type: " .. d2wc_value(get_window_type()))
debug_print("Class instance name: " .. d2wc_value(get_class_instance_name()))
debug_print("")
"""

Runner = Callable[..., subprocess.CompletedProcess[str]]
PopenFactory = Callable[..., subprocess.Popen[str]]


@dataclass(frozen=True)
class Devilspie2InventoryCaptureResult:
    """Result from a bounded Devilspie2 inventory snapshot."""

    raw_text: str
    candidates: tuple[KnownWindowCandidate, ...]
    targets: tuple[KnownWindowTarget, ...]
    timed_out: bool
    returncode: int | None
    command: tuple[str, ...]


@dataclass(frozen=True)
class Devilspie2InventoryStreamEvent:
    """One parsed event block from continuous Devilspie2 debug output."""

    raw_text: str
    candidates: tuple[KnownWindowCandidate, ...]
    targets: tuple[KnownWindowTarget, ...]


class KnownWindowInventoryStreamParser:
    """Parse continuous Devilspie2 debug output into newly seen targets."""

    def __init__(self) -> None:
        self._current_lines: list[str] = []
        self._seen_targets: set[KnownWindowTarget] = set()

    def feed_line(self, line: str) -> tuple[Devilspie2InventoryStreamEvent, ...]:
        """Feed one debug-output line and return completed inventory events."""

        clean_line = line.rstrip("\r\n")
        if clean_line.strip() == "":
            return self._flush_current_block()
        self._current_lines.append(clean_line)
        return ()

    def feed_text(self, text: str) -> tuple[Devilspie2InventoryStreamEvent, ...]:
        """Feed a chunk of debug-output text and return completed events."""

        events: list[Devilspie2InventoryStreamEvent] = []
        for line in text.splitlines():
            events.extend(self.feed_line(line))
        return tuple(events)

    def finish(self) -> tuple[Devilspie2InventoryStreamEvent, ...]:
        """Flush a final unterminated block at stream end."""

        return self._flush_current_block()

    def _flush_current_block(self) -> tuple[Devilspie2InventoryStreamEvent, ...]:
        if not self._current_lines:
            return ()

        raw_text = "\n".join(self._current_lines)
        self._current_lines = []
        candidates = parse_known_window_candidates(raw_text)
        targets = tuple(
            target
            for target in build_known_window_targets(candidates)
            if target not in self._seen_targets
        )
        self._seen_targets.update(targets)
        if not candidates and not targets:
            return ()
        return (Devilspie2InventoryStreamEvent(raw_text=raw_text, candidates=candidates, targets=targets),)


def capture_known_window_inventory(
    *,
    timeout_seconds: float = DEFAULT_CAPTURE_TIMEOUT_SECONDS,
    devilspie2_command: str = "devilspie2",
    runner: Runner | None = None,
) -> Devilspie2InventoryCaptureResult:
    """Capture a bounded startup inventory snapshot through a read-only probe.

    The active user `d2wc.lua` rules script is not used. A temporary probe folder
    is created instead, containing only a small script that prints the domain,
    window type, and class instance name for Devilspie2 events.
    """

    with tempfile.TemporaryDirectory(prefix="d2wc-devilspie2-inventory-") as temp_dir:
        probe_dir = Path(temp_dir)
        _write_probe_script(probe_dir)
        command = _capture_command(devilspie2_command, probe_dir)
        raw_text, timed_out, returncode = _run_capture_command(
            command,
            timeout_seconds=timeout_seconds,
            runner=runner or subprocess.run,
        )

    candidates = parse_known_window_candidates(raw_text)
    targets = build_known_window_targets(candidates)
    return Devilspie2InventoryCaptureResult(
        raw_text=raw_text,
        candidates=candidates,
        targets=targets,
        timed_out=timed_out,
        returncode=returncode,
        command=tuple(command),
    )


def stream_known_window_inventory(
    *,
    devilspie2_command: str = "devilspie2",
    popen_factory: PopenFactory | None = None,
) -> Iterator[Devilspie2InventoryStreamEvent]:
    """Continuously stream newly seen known-window targets from Devilspie2.

    Startup output creates the initial inventory. Later debug output can add
    newly opened domain/class pairs while the monitor is running.
    """

    with tempfile.TemporaryDirectory(prefix="d2wc-devilspie2-inventory-") as temp_dir:
        probe_dir = Path(temp_dir)
        _write_probe_script(probe_dir)
        command = _capture_command(devilspie2_command, probe_dir)
        process = (popen_factory or subprocess.Popen)(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        parser = KnownWindowInventoryStreamParser()
        try:
            if process.stdout is None:
                return
            for line in process.stdout:
                yield from parser.feed_line(line)
            yield from parser.finish()
        finally:
            _terminate_process(process)


def _write_probe_script(probe_dir: Path) -> Path:
    probe_path = probe_dir / PROBE_SCRIPT_NAME
    probe_path.write_text(PROBE_SCRIPT, encoding="utf-8")
    probe_path.chmod(0o600)
    return probe_path


def _capture_command(devilspie2_command: str, probe_dir: Path) -> list[str]:
    return [devilspie2_command, "--debug", "--folder", str(probe_dir)]


def _run_capture_command(
    command: Sequence[str],
    *,
    timeout_seconds: float,
    runner: Runner,
) -> tuple[str, bool, int | None]:
    try:
        completed = runner(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        return _combine_output(exc.output, exc.stderr), True, None

    return _combine_output(completed.stdout, completed.stderr), False, completed.returncode


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        return


def _combine_output(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    parts = [_decode_output(stdout), _decode_output(stderr)]
    return "\n".join(part for part in parts if part)


def _decode_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output
