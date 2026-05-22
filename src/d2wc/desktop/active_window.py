"""Read-only X11 window capture helpers for Qubes/dom0 desktops."""

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
    """Read-only identity snapshot for a selected X11 window.

    The class name is kept stable for now because the GTK proof already uses it,
    but the Qubes/dom0 capture path now selects a window with `xwininfo -frame`
    instead of assuming an AppVM can read another VM's active window.
    """

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


def capture_selected_window(runner: CommandRunner | None = None) -> ActiveWindowInfo:
    """Capture a user-selected X11 window from dom0.

    This is the Qubes-safe proof path. It runs `xwininfo -frame`, which prompts
    the user to click the target window from dom0. The selected window id is then
    optionally inspected with xprop for title/class/Qubes metadata. Missing xprop
    properties are tolerated because frame/client property placement can vary.
    """

    run = runner or _run_command

    try:
        xwininfo_output = run(["xwininfo", "-frame"])
    except CaptureCommandError as exc:
        return ActiveWindowInfo(error=str(exc))

    window_id = parse_xwininfo_window_id(xwininfo_output)
    if window_id is None:
        return ActiveWindowInfo(error="Could not determine selected window id from xwininfo output.")

    xprop_output = ""
    try:
        xprop_output = run(["xprop", "-id", window_id, "WM_NAME", "_NET_WM_NAME", "WM_CLASS", "_QUBES_VMNAME"])
    except CaptureCommandError:
        pass

    wm_class_instance, wm_class = parse_wm_class(xprop_output)
    title = parse_xprop_string(xprop_output, "_NET_WM_NAME") or parse_xprop_string(xprop_output, "WM_NAME")
    if title is None:
        title = parse_xwininfo_title(xwininfo_output)

    return ActiveWindowInfo(
        window_id=window_id,
        title=title,
        wm_class_instance=wm_class_instance,
        wm_class=wm_class,
        qubes_vmname=parse_xprop_string(xprop_output, "_QUBES_VMNAME"),
        geometry=parse_xwininfo_geometry(xwininfo_output),
    )


def capture_active_window(runner: CommandRunner | None = None) -> ActiveWindowInfo:
    """Backward-compatible wrapper for the current selected-window proof."""

    return capture_selected_window(runner=runner)


class CaptureCommandError(RuntimeError):
    """Raised when a window capture command fails."""


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
    """Parse `_NET_ACTIVE_WINDOW` output from `xprop -root`.

    Kept for tests and possible later use, but the current Qubes/dom0 proof uses
    `xwininfo -frame` selection instead.
    """

    for pattern in (
        r"window id #\s*(0x[0-9a-fA-F]+|0)\b",
        r"_NET_ACTIVE_WINDOW\([^)]*\):\s*(0x[0-9a-fA-F]+|0)\b",
    ):
        match = re.search(pattern, output)
        if match:
            window_id = match.group(1)
            if window_id in {"0", "0x0"}:
                return None
            return window_id

    return None


def parse_xwininfo_window_id(output: str) -> str | None:
    """Parse the selected window id from xwininfo output."""

    match = re.search(r"xwininfo:\s+Window id:\s+(0x[0-9a-fA-F]+)", output)
    if match:
        return match.group(1)
    return None


def parse_xwininfo_title(output: str) -> str | None:
    """Parse the selected window title from the first xwininfo line."""

    match = re.search(r'xwininfo:\s+Window id:\s+0x[0-9a-fA-F]+\s+"(.*)"', output)
    if match:
        return match.group(1)
    return None


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
