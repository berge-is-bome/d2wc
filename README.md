# d2wc

Devilspie2 Workspace Configurator.

`d2wc` is intended to make Linux window placement easier to configure by combining a `devilspie2` Lua rules script with a small configurator UI. The current implementation is the Lua rules engine plus an early read-only Python configurator core proof. The next development step is to finish the safe save and backup workflow before any real user configuration writes are allowed.

## Current status

The repository now starts from the current `d2wc` Lua script version `0.1.12.3`.

The active Lua script supports:

1. Excluding domains, classes, or domain/class combinations from automation.
2. Pinning selected windows so they appear on all workspaces.
3. Routing windows to workspaces by domain, class, or domain/class match.
4. Applying named geometry profiles to matching windows.
5. Applying optional left-edge correction for windows that do not land exactly at `x = 0` when `set_window_geometry()` is used.

The Python core proof currently supports read-only validation and dry-run rendering of the managed Lua sections.

Latest confirmed local verification is recorded in [`docs/development-status.md`](docs/development-status.md). The current confirmed result is that `src/d2wc.lua` validates, rendered output validates, and the full pytest suite passes with 59 tests.

## Repository layout

```text
docs/
  development-status.md          Current PR status, latest local verification, and next work.
  product-development-brief.md   In-depth product and UI direction.
  lua-configurables.md           User-facing explanation of the Lua configuration sections.
  repository-layout.md           Repository structure and development conventions.
src/
  d2wc.lua                       Current devilspie2 Lua rules script.
  d2wc/                          Python configurator core proof.
tests/                           Python tests for the read-only core proof.
```

## Local development

The project uses a Python `src/` layout.

For quick source-checkout testing without installing the package:

```bash
PYTHONPATH=src python -m d2wc --help
PYTHONPATH=src python -m d2wc validate --config src/d2wc.lua
PYTHONPATH=src python -m d2wc render --config src/d2wc.lua --stdout
PYTHONPATH=src python -m pytest
```

When renderer behavior changes, use the stronger renderer verification path:

```bash
PYTHONPATH=src python -m d2wc validate --config src/d2wc.lua
PYTHONPATH=src python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
PYTHONPATH=src python -m d2wc validate --config /tmp/d2wc-rendered.lua
PYTHONPATH=src python -m pytest
```

For editable development installation:

```bash
python -m pip install -e .[dev]
d2wc validate --config src/d2wc.lua
d2wc render --config src/d2wc.lua --stdout
python -m pytest
```

The `validate` command is read-only. It parses and validates the managed Lua sections but does not write or modify any file.

The `render` command is also read-only in this proof stage. It requires `--stdout` and prints the rendered Lua to standard output only.

Comments and blank separator lines inside the managed Lua sections are treated as user-managed content. The renderer must preserve them, and the future configurator should expose simple actions to add a user comment or insert a blank separator line.

## Development direction

The first production goal is not a flamboyant desktop tool. The goal is a minimal configurator that hides as much manual rule-writing as possible while still allowing the user to review and edit the result before it is written to the Lua script.

Planned entry points:

1. Command or keyboard shortcut to open the configurator for the active window.
2. Optional system tray menu for setup or troubleshooting.
3. Optional direct `Configure` flow after a user resizes a window and releases the primary mouse button.
4. Optional small pointer-anchored menu after resize with `Cancel` and `Configure`.

The configurator should eventually update the Lua sections `EXCLUDE`, `PIN`, `WORKSPACE_ROUTES`, `GEOM`, `WORKSPACE_PLACEMENT`, and `LEFT_EDGE_CORRECTION` without requiring the user to edit Lua manually.
