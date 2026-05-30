"""Module and console entry point for d2wc."""

from __future__ import annotations

import argparse
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
import fcntl
import os
import sys
from pathlib import Path

from d2wc.cli import main as cli_main
from d2wc.core.user_paths import d2wc_config_dir
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, EVENT_FIXTURE_NAMES, WindowEventData, get_event_fixture
from d2wc.event_preview import EventConfigAwareness, build_event_config_awareness, build_event_rule_preview
from d2wc.managed_config_file import load_managed_config_snapshot
from d2wc.test_config import (
    TestConfigPrepareResult,
    TestConfigSnapshot,
    load_test_config_snapshot,
    prepare_test_config,
)
from d2wc.ui.action_prompt import run_action_prompt
from d2wc.ui.gtk_app import GtkConfiguratorImportError, run_configurator

CONFIGURATOR_LOCK_FILENAME = "configurator.lock"


@dataclass(frozen=True)
class ConfigureInput:
    """Parsed configurator input."""

    event_data: WindowEventData
    config_awareness: EventConfigAwareness | None = None
    test_config_snapshot: TestConfigSnapshot | None = None
    prepare_result: TestConfigPrepareResult | None = None


def main(argv: Sequence[str] | None = None) -> int:
    """Run d2wc."""

    args = list(sys.argv[1:] if argv is None else argv)

    if not args:
        return _run_configure(())

    if args[:1] == ["configure"]:
        return _run_configure(args[1:])

    if args[:1] == ["prompt"]:
        return _run_prompt(args[1:])

    return cli_main(args)


def _run_configure(argv: Sequence[str]) -> int:
    try:
        configure_input = _parse_configure_args(argv, prog="d2wc configure")
        return _run_configurator_once(configure_input)
    except GtkConfiguratorImportError as exc:
        print(f"ERROR: {exc}")
        return 2


def _run_prompt(argv: Sequence[str]) -> int:
    try:
        configure_input = _parse_configure_args(argv, prog="d2wc prompt")
        decision = run_action_prompt(configure_input.event_data)
        if decision != "configure":
            return 0
        return _run_configurator_once(configure_input)
    except GtkConfiguratorImportError as exc:
        print(f"ERROR: {exc}")
        return 2


def _run_configurator_once(configure_input: ConfigureInput) -> int:
    with _configurator_instance_lock() as acquired:
        if not acquired:
            return 0
        return run_configurator(
            configure_input.event_data,
            configure_input.config_awareness,
            configure_input.test_config_snapshot,
            configure_input.prepare_result,
        )


@contextmanager
def _configurator_instance_lock() -> Iterator[bool]:
    """Hold a non-blocking process lock while one configurator window is open."""

    lock_dir = d2wc_config_dir()
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / CONFIGURATOR_LOCK_FILENAME
    with lock_path.open("w", encoding="utf-8") as lock_file:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return

        try:
            lock_file.seek(0)
            lock_file.truncate()
            lock_file.write(f"{os.getpid()}\n")
            lock_file.flush()
            yield True
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def _parse_configure_args(argv: Sequence[str], *, prog: str) -> ConfigureInput:
    parser = argparse.ArgumentParser(
        prog=prog,
        description="Open the GTK d2wc managed-config editor.",
    )
    parser.add_argument(
        "--event-fixture",
        choices=EVENT_FIXTURE_NAMES,
        default=DEFAULT_EVENT_FIXTURE,
        help="Representative Devilspie2 event-data fixture to display.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional d2wc managed Lua file to open in the configurator.",
    )
    parser.add_argument(
        "--test-config",
        action="store_true",
        help="Load the dedicated ~/.config/devilspie2/d2wc-test.lua file for UI testing.",
    )
    parser.add_argument(
        "--test-config-path",
        type=Path,
        default=None,
        help="Optional override for the UI test config path, mainly for tests and manual experiments.",
    )
    parser.add_argument(
        "--init-test-config",
        action="store_true",
        help="Create ~/.config/devilspie2/d2wc-test.lua from the bundled src/d2wc.lua if missing.",
    )
    parser.add_argument(
        "--replace-test-config",
        action="store_true",
        help="Replace ~/.config/devilspie2/d2wc-test.lua from the bundled src/d2wc.lua.",
    )
    parser.add_argument("--domain", default=None, help="Event domain from _QUBES_VMNAME.")
    parser.add_argument("--application-name", default=None, help="Event application name.")
    parser.add_argument("--window-name", default=None, help="Event window name.")
    parser.add_argument("--window-type", default=None, help="Event window type.")
    parser.add_argument("--class-instance-name", default=None, help="Event class instance name.")
    parser.add_argument("--window-class", default=None, help="Event window class.")
    parser.add_argument("--screen-width", type=float, default=None, help="Event screen width.")
    parser.add_argument("--screen-height", type=float, default=None, help="Event screen height.")
    parser.add_argument("--window-x", type=float, default=None, help="Event window x position.")
    parser.add_argument("--window-y", type=float, default=None, help="Event window y position.")
    parser.add_argument("--window-width", type=float, default=None, help="Event window width.")
    parser.add_argument("--window-height", type=float, default=None, help="Event window height.")

    args = parser.parse_args(list(argv))
    event_data = get_event_fixture(args.event_fixture).with_overrides(
        domain=args.domain,
        application_name=args.application_name,
        window_name=args.window_name,
        window_type=args.window_type,
        class_instance_name=args.class_instance_name,
        window_class=args.window_class,
        screen_width=args.screen_width,
        screen_height=args.screen_height,
        window_x=args.window_x,
        window_y=args.window_y,
        window_width=args.window_width,
        window_height=args.window_height,
    )

    prepare_result = None
    if args.init_test_config or args.replace_test_config:
        prepare_result = prepare_test_config(
            target_path=args.test_config_path,
            replace=args.replace_test_config,
        )

    test_config_snapshot = None
    if args.test_config or args.init_test_config or args.replace_test_config:
        test_config_snapshot = load_test_config_snapshot(args.test_config_path)
    elif args.config is not None:
        test_config_snapshot = load_managed_config_snapshot(args.config)
    else:
        test_config_snapshot = load_managed_config_snapshot()

    config_awareness = None
    if test_config_snapshot is not None and test_config_snapshot.path.exists():
        config_awareness = _read_config_awareness(test_config_snapshot.path, event_data)

    return ConfigureInput(
        event_data=event_data,
        config_awareness=config_awareness,
        test_config_snapshot=test_config_snapshot,
        prepare_result=prepare_result,
    )


def _read_config_awareness(config_path: Path, event_data: WindowEventData) -> EventConfigAwareness:
    try:
        source = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        return EventConfigAwareness(
            status="error",
            warnings=(f"Could not read config file read-only: {exc}",),
        )

    return build_event_config_awareness(source, build_event_rule_preview(event_data))


if __name__ == "__main__":
    raise SystemExit(main())
