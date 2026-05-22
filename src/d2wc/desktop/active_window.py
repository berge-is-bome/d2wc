"""Read-only Devilspie2 window probe helpers for Qubes/dom0 desktops."""

from __future__ import annotations

import os
import select
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


PROBE_BEGIN = "D2WC_PROBE_BEGIN"
PROBE_END = "D2WC_PROBE_END"

PROBE_LUA = """local function safe(v)
  if v == nil then return "" end
  return tostring(v)
end

if get_window_type() ~= "WINDOW_TYPE_NORMAL" then
  return
end

debug_print("D2WC_PROBE_BEGIN")
debug_print( "Domain: " .. safe(get_window_property( '_QUBES_VMNAME' )) );
debug_print( "Application name: " .. safe(get_application_name()) );
debug_print( "Window name: " .. safe(get_window_name()) );
debug_print( "Window Type: " .. safe(get_window_type()) );
debug_print( "Class instance name: " .. safe(get_class_instance_name()) );
debug_print( "Window class: " .. safe(get_window_class()) );
local sx, sy = get_screen_geometry()
print( "Screen Geometry: x = " .. safe(sx) .. " y = " .. safe(sy) );
local x, y, w, h = get_window_geometry()
print( "Window geometry:  x = " .. safe(x) .. " y = " .. safe(y) .. " w = " .. safe(w) .. " h = " .. safe(h) );
debug_print("D2WC_PROBE_END")
"""


@dataclass(frozen=True)
class ScreenGeometry:
    """Screen geometry reported by Devilspie2."""

    x: float | None = None
    y: float | None = None


@dataclass(frozen=True)
class WindowGeometry:
    """Window geometry reported by Devilspie2."""

    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None

    @property
    def size_text(self) -> str | None:
        """Return WIDTHxHEIGHT text when both dimensions are known."""

        if self.width is None or self.height is None:
            return None
        return f"{format_probe_number(self.width)}x{format_probe_number(self.height)}"


@dataclass(frozen=True)
class ActiveWindowInfo:
    """Read-only Devilspie2 snapshot for a normal application window."""

    domain: str | None = None
    application_name: str | None = None
    window_name: str | None = None
    window_type: str | None = None
    class_instance_name: str | None = None
    window_class: str | None = None
    screen_geometry: ScreenGeometry = ScreenGeometry()
    geometry: WindowGeometry = WindowGeometry()
    raw_devilspie2_output: str | None = None
    error: str | None = None

    @property
    def normalized_domain(self) -> str | None:
        """Return the Qubes domain, treating an empty VM name as dom0."""

        if self.domain == "":
            return "dom0"
        return self.domain


def capture_selected_window(timeout_seconds: float = 45.0) -> ActiveWindowInfo:
    """Capture one normal window report through Devilspie2 debug output.

    This function writes a temporary `debug.lua`, runs `devilspie2 --debug`
    against that temporary config home, waits for one complete probe report, then
    terminates Devilspie2. It does not read or write the user's real d2wc or
    Devilspie2 configuration.
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
    """Run Devilspie2 against a temporary config home and parse one probe report."""

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
            error="Timed out waiting for a Devilspie2 normal-window probe report.",
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
    """Parse the bounded output produced by the d2wc Devilspie2 probe script."""

    fields = _parse_colon_fields(output)

    return ActiveWindowInfo(
        domain=fields.get("Domain"),
        application_name=fields.get("Application name"),
        window_name=fields.get("Window name"),
        window_type=fields.get("Window Type"),
        class_instance_name=fields.get("Class instance name"),
        window_class=fields.get("Window class"),
        screen_geometry=parse_screen_geometry(fields.get("Screen Geometry")),
        geometry=parse_window_geometry(fields.get("Window geometry")),
        raw_devilspie2_output=output,
    )


def _parse_colon_fields(output: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in output.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
    return fields


def parse_screen_geometry(value: str | None) -> ScreenGeometry:
    """Parse `x = WIDTH y = HEIGHT` screen geometry text."""

    if value is None:
        return ScreenGeometry()

    parts = _parse_named_numbers(value)
    return ScreenGeometry(x=parts.get("x"), y=parts.get("y"))


def parse_window_geometry(value: str | None) -> WindowGeometry:
    """Parse `x = X y = Y w = W h = H` window geometry text."""

    if value is None:
        return WindowGeometry()

    parts = _parse_named_numbers(value)
    return WindowGeometry(
        x=parts.get("x"),
        y=parts.get("y"),
        width=parts.get("w"),
        height=parts.get("h"),
    )


def _parse_named_numbers(value: str) -> dict[str, float]:
    parts: dict[str, float] = {}
    tokens = value.split()

    for index, token in enumerate(tokens):
        if token not in {"x", "y", "w", "h"}:
            continue
        if index + 2 >= len(tokens) or tokens[index + 1] != "=":
            continue
        try:
            parts[token] = float(tokens[index + 2])
        except ValueError:
            continue

    return parts


def format_probe_number(value: float | None) -> str:
    """Format Devilspie2 numeric output compactly for display."""

    if value is None:
        return "unknown"
    if value.is_integer():
        return str(int(value))
    return str(value)
