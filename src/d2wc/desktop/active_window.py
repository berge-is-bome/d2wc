"""Read-only active-window capture helpers for X11 desktops."""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass

CommandRunner = Callable[[Sequence[str]], str]


@dataclass(frozen=True)
class WindowGeometry:
    """Window geometry reported by xwininfo."""

    x: int | None = None
    y: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True)
class ActiveWindowInfo:
    """Read-only identity snapshot for the currently active X11 window."""

    window_id: str | None = None
    title: str | None = None
    wm_class_instance: str | None = None
    wm_class: str | None = None
    qubes_vmname: str | None = None
    geometry: WindowGeometry = WindowGeometry()
    error: str | None = None

    @property
    def domain(self) -> str | None:
        """Return the Qubes domain, treating an empty VM name as dom0."""

        if self.qubes_vmname == "":
            return "dom0"
        return self.qubes_vmname


def capture_active_window(runner: CommandRunner | None = None) -> ActiveWindowInfo:
    """Capture basic information about the active X11 window.

    The function is read-only. It shells out to common X11 tools and never reads
    or writes the d2wc Lua configuration.
    """

    run = runner or _run_command

    try:
        root_output = run(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
    except CaptureCommandError as exc:
        return ActiveWindowInfo(error=str(exc))

    window_id = parse_active_window_id(root_output)
    if window_id is None:
        return ActiveWindowInfo(error="Could not determine active window id from xprop output.")

    try:
        window_output = run(["xprop", "-id", window_id, "WM_NAME", "WM_CLASS", "_QUBES_VMNAME"])
    except CaptureCommandError as exc:
        return ActiveWindowInfo(window_id=window_id, error=str(exc))

    try:
        geometry_output = run(["xwininfo", "-id", window_id])
        geometry = parse_xwininfo_geometry(geometry_output)
    except CaptureCommandError:
        geometry = WindowGeometry()

    return ActiveWindowInfo(
        window_id=window_id,
        title=parse_xprop_string(window_output, "WM_NAME"),
        wm_class_instance=parse_wm_class(window_output)[0],
        wm_class=parse_wm_class(window_output)[1],
        qubes_vmname=parse_xprop_string(window_output, "_QUBES_VMNAME"),
        geometry=geometry,
    )


class CaptureCommandError(RuntimeError):
    """Raised when an active-window capture command fails."""


def _run_command(command: Sequence[str]) -> str:
    try:
        result = subprocess.run(
            list(command),
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as exc:
        raise CaptureCommandError(f"Required command not found: {command[0]}") from exc
    except subprocess.CalledProcessError as exc:
        message = (exc.stderr or exc.stdout or str(exc)).strip()
        raise CaptureCommandError(f"Command failed: {' '.join(command)}: {message}") from exc

    return result.stdout


def parse_active_window_id(output: str) -> str | None:
    """Parse `_NET_ACTIVE_WINDOW` output from `xprop -root`."""

    match = re.search(r"window id #\s*(0x[0-9a-fA-F]+|0)", output)
    if not match:
        return None

    window_id = match.group(1)
    if window_id == "0":
        return None
    return window_id


def parse_xprop_string(output: str, property_name: str) -> str | None:
    """Parse one quoted string property from xprop output."""

    pattern = rf"^{re.escape(property_name)}\([^)]*\) = \"(.*)\"$"
    for line in output.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1)
    return None


def parse_wm_class(output: str) -> tuple[str | None, str | None]:
    """Parse WM_CLASS into instance and class strings."""

    pattern = r'^WM_CLASS\([^)]*\) = "(.*)", "(.*)"$'
    for line in output.splitlines():
        match = re.match(pattern, line)
        if match:
            return match.group(1), match.group(2)
    return None, None


def parse_xwininfo_geometry(output: str) -> WindowGeometry:
    """Parse geometry fields from xwininfo output."""

    return WindowGeometry(
        x=_parse_xwininfo_int(output, "Absolute upper-left X"),
        y=_parse_xwininfo_int(output, "Absolute upper-left Y"),
        width=_parse_xwininfo_int(output, "Width"),
        height=_parse_xwininfo_int(output, "Height"),
    )


def _parse_xwininfo_int(output: str, label: str) -> int | None:
    pattern = rf"^\s*{re.escape(label)}:\s*(-?\d+)\s*$"
    for line in output.splitlines():
        match = re.match(pattern, line)
        if match:
            return int(match.group(1))
    return None
