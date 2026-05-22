"""Module and console entry point for d2wc."""

from __future__ import annotations

import sys
from collections.abc import Sequence

from d2wc.cli import main as cli_main
from d2wc.ui.gtk_app import GtkConfiguratorImportError, run_configurator


def main(argv: Sequence[str] | None = None) -> int:
    """Run d2wc.

    The first GTK proof is routed here so `python -m d2wc configure` can open a
    real window without refactoring the existing guarded CLI edit commands.
    """

    args = list(sys.argv[1:] if argv is None else argv)

    if args == ["configure"]:
        try:
            return run_configurator()
        except GtkConfiguratorImportError as exc:
            print(f"ERROR: {exc}")
            return 2

    return cli_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
