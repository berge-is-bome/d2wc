"""Module and console entry point for d2wc."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from d2wc.cli import main as cli_main
from d2wc.event_data import DEFAULT_EVENT_FIXTURE, EVENT_FIXTURE_NAMES, WindowEventData, get_event_fixture
from d2wc.event_preview import EventConfigAwareness, build_event_config_awareness, build_event_rule_preview
from d2wc.ui.gtk_app import GtkConfiguratorImportError, run_configurator


@dataclass(frozen=True)
class ConfigureInput:
    """Parsed read-only configurator input."""

    event_data: WindowEventData
    config_awareness: EventConfigAwareness | None = None


def main(argv: Sequence[str] | None = None) -> int:
    """Run d2wc."""

    args = list(sys.argv[1:] if argv is None else argv)

    if args[:1] == ["configure"]:
        return _run_configure(args[1:])

    return cli_main(args)


def _run_configure(argv: Sequence[str]) -> int:
    try:
        if not argv:
            return run_configurator()
        configure_input = _parse_configure_args(argv)
        return run_configurator(configure_input.event_data, configure_input.config_awareness)
    except GtkConfiguratorImportError as exc:
        print(f"ERROR: {exc}")
        return 2


def _parse_configure_args(argv: Sequence[str]) -> ConfigureInput:
    parser = argparse.ArgumentParser(
        prog="d2wc configure",
        description="Open the read-only GTK event-data UI proof.",
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
        help="Optional d2wc.lua path to inspect read-only for existing matching rules.",
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

    config_awareness = None
    if args.config is not None:
        config_awareness = _read_config_awareness(args.config, event_data)

    return ConfigureInput(event_data=event_data, config_awareness=config_awareness)


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
