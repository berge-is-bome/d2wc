"""Read-only Devilspie2 window probe helpers for Qubes/dom0 desktops."""

from __future__ import annotations

import os
import select
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


PROBE_BEGIN = "D2WC_CLASS_PROBE_BEGIN"
PROBE_END = "D2WC_CLASS_PROBE_END"

PROBE_LUA = """local function safe(v)
  if v == nil then return "" end
  return tostring(v)
end

local class_instance_name = get_class_instance_name()

debug_print("D2WC_CLASS_PROBE_BEGIN")
debug_print( "Class instance name: " .. safe(class_instance_name) );
debug_print("D2WC_CLASS_PROBE_END")
"""


@dataclass(frozen=True)
class ActiveWindowInfo:
    """Read-only Devilspie2 class-instance snapshot from one window event."""

    class_instance_name: str | None = None
    raw_devilspie2_output: str | None = None
    error: str | None = None


def capture_selected_window(timeout_seconds: float = 45.0) -> ActiveWindowInfo:
    """Capture one Devilspie2 class-instance report.

    This function writes a temporary `debug.lua`, runs `devilspie2 --debug`
    against that temporary config home, waits for one bounded class-instance
    report, then terminates Devilspie2. It does not read or write the user's real
    d2wc or Devilspie2 configuration.
    """

    try:
        with tempfile.TemporaryDirectory(prefix="d2wc-devilspie2-probe-") as tmpdir:
            config_home = Path(tmpdir)
            script_dir = config_home / "devilspie2"
            script_dir.mkdir(parents=True, exist_ok=True)
            (script_dir / "debug.lua").write_text(PROBE_LUA, encoding="utf-8")
            return run_devilspie2_probe(config_home=config_home, timeout_seconds=timeout_seconds)
    except OSError as exc:
        return ActiveWindowInfo(error=f"Could not create temporary Devilspie2 probe config: {exc}")


def capture_active_window(timeout_seconds: float = 45.0) -> ActiveWindowInfo:
    """Backward-compatible wrapper for the current Devilspie2 probe proof."""

    return capture_selected_window(timeout_seconds=timeout_seconds)


def run_devilspie2_probe(config_home: Path, timeout_seconds: float = 45.0) -> ActiveWindowInfo:
    """Run Devilspie2 against a temporary config home and parse one class report."""

    env = os.environ.copy()
    env["XDG_CONFIG_HOME"] = str(config_home)

    try:
        process = subprocess.Popen(
            ["devilspie2", "--debug"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
    except FileNotFoundError:
        return ActiveWindowInfo(error="Required command not found: devilspie2")
    except OSError as exc:
        return ActiveWindowInfo(error=f"Could not start devilspie2 --debug: {exc}")

    output_lines: list[str] = []
    probe_lines: list[str] = []
    in_probe = False
    deadline = time.monotonic() + timeout_seconds

    try:
        while time.monotonic() < deadline:
            if process.poll() is not None:
                break

            if process.stdout is None:
                break

            readable, _, _ = select.select([process.stdout], [], [], 0.1)
            if not readable:
                continue

            line = process.stdout.readline()
            if line == "":
                continue

            clean_line = line.rstrip("\n")
            output_lines.append(clean_line)

            if clean_line == PROBE_BEGIN:
                in_probe = True
                probe_lines = []
                continue

            if clean_line == PROBE_END and in_probe:
                return parse_devilspie2_probe_output("\n".join(probe_lines))

            if in_probe:
                probe_lines.append(clean_line)

        raw_output = "\n".join(output_lines)
        return ActiveWindowInfo(
            raw_devilspie2_output=raw_output or None,
            error="Timed out waiting for a Devilspie2 class-instance probe report.",
        )
    finally:
        _terminate_process(process)


def _terminate_process(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=2)


def parse_devilspie2_probe_output(output: str) -> ActiveWindowInfo:
    """Parse the bounded output produced by the d2wc Devilspie2 class probe."""

    return ActiveWindowInfo(
        class_instance_name=parse_colon_field(output, "Class instance name"),
        raw_devilspie2_output=output,
    )


def parse_colon_field(output: str, field_name: str) -> str | None:
    """Parse one `Name: value` field from Devilspie2 debug output."""

    prefix = f"{field_name}:"
    for line in output.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None
