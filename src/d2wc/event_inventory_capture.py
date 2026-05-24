"""Bounded Devilspie2 debug capture for known-window inventory."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
from typing import Callable, Sequence

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


@dataclass(frozen=True)
class Devilspie2InventoryCaptureResult:
    """Result from a bounded Devilspie2 inventory capture."""

    raw_text: str
    candidates: tuple[KnownWindowCandidate, ...]
    targets: tuple[KnownWindowTarget, ...]
    timed_out: bool
    returncode: int | None
    command: tuple[str, ...]


def capture_known_window_inventory(
    *,
    timeout_seconds: float = DEFAULT_CAPTURE_TIMEOUT_SECONDS,
    devilspie2_command: str = "devilspie2",
    runner: Runner | None = None,
) -> Devilspie2InventoryCaptureResult:
    """Capture known-window inventory through a temporary read-only probe script.

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


def _combine_output(stdout: str | bytes | None, stderr: str | bytes | None) -> str:
    parts = [_decode_output(stdout), _decode_output(stderr)]
    return "\n".join(part for part in parts if part)


def _decode_output(output: str | bytes | None) -> str:
    if output is None:
        return ""
    if isinstance(output, bytes):
        return output.decode("utf-8", errors="replace")
    return output
