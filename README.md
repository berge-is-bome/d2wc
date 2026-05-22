# d2wc

Devilspie2 Workspace Configurator.

`d2wc` is intended to make Linux window placement easier to configure by combining a `devilspie2` Lua rules script with a small configurator UI. The current implementation is the active Lua rules engine plus a Python configurator core proof with parser, validator, renderer, guarded CLI edit commands, safe-save behavior, the read-only GTK launch proof, the read-only Qubes/dom0 selected-window geometry proof, and the first read-only Devilspie2 window probe proof.

## Current status

The repository now starts from the current `d2wc` Lua script version `0.1.12.3`.

The active Lua script supports:

1. Excluding domains, classes, or domain/class combinations from automation.
2. Pinning selected windows so they appear on all workspaces.
3. Routing windows to workspaces by domain, class, or domain/class match.
4. Applying named geometry profiles to matching windows.
5. Applying optional left-edge correction for windows that do not land exactly at `x = 0` when `set_window_geometry()` is used.

The Python core currently supports validation, render preview, safe-save behavior, and guarded add, modify, and delete commands for all managed Lua sections:

1. `GEOM`
2. `WORKSPACE_PLACEMENT`
3. `WORKSPACE_ROUTES`
4. `PIN`
5. `EXCLUDE`
6. `LEFT_EDGE_CORRECTION`

The GTK proof opens a read-only window launched by `python -m d2wc configure` or `d2wc configure`. On Qubes, it must run from dom0. The current branch uses a temporary Devilspie2 debug probe to capture one `WINDOW_TYPE_NORMAL` window report, then displays the domain, application name, window name, window type, class instance name, window class, screen geometry, and window geometry. It does not read or write user config files or edit rules.

Latest confirmed local verification is recorded in [`docs/development-status.md`](docs/development-status.md). The latest reported result after PR #12 was `197 passed`.

## Repository layout

```text
docs/
  development-status.md          Current PR status, latest local verification, and next work.
  devilspie2-window-probe.md     Devilspie2 probe functions, sample output, and field mapping.
  product-development-brief.md   In-depth product and UI direction.
  lua-configurables.md           User-facing explanation of the Lua configuration sections.
  lua-design-history.md          Design context recovered from archived pre-repository Lua history.
  repository-layout.md           Repository structure and development conventions.
src/
  d2wc.lua                       Current devilspie2 Lua rules script.
  d2wc/                          Python configurator core, desktop integration, and GTK UI proof.
tests/                           Python tests for the configurator core and desktop proof helpers.
```

## Local development

Install `python3-pip` with your package manager, then install the project in editable mode from the repository root:

```bash
python -m pip install -e .
```

Re-run the editable install command after switching to a branch that changes `[project.scripts]`; otherwise the generated `d2wc` console wrapper may still point at the previously installed entry point.

For normal source-checkout testing:

```bash
python -m d2wc --help
python -m d2wc validate --config src/d2wc.lua
python -m d2wc render --config src/d2wc.lua --stdout
python -m pytest
```

When renderer behavior changes, use the stronger renderer verification path:

```bash
python -m d2wc validate --config src/d2wc.lua
python -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python -m d2wc validate --config /tmp/d2wc-rendered.lua
python -m pytest
```

The `validate` command is read-only. It parses and validates the managed Lua sections but does not modify any file.

The `render` command is read-only in ordinary preview use. Guarded edit commands preview by default and apply changes only when `--write` is supplied.

The GTK proof can be launched directly from the source checkout with:

```bash
python -m d2wc configure
```

or, after refreshing the editable install:

```bash
d2wc configure
```

For a dom0 archive test without editable installation, use:

```bash
PYTHONPATH=src python3 -m d2wc configure
```

The current GTK proof is read-only. On Qubes, it must run from dom0 so it can run Devilspie2 against visible windows. It uses a temporary Devilspie2 script folder, waits for one normal-window probe report, opens a GTK window with the captured details, and closes cleanly. It does not read or write the user's real d2wc or Devilspie2 config files.

Comments and blank separator lines inside the managed Lua sections are treated as user-managed content. The renderer should preserve them where practical, especially in rule-list sections where comments explain why a rule exists.

## Development direction

The CLI/core editing proof phase is complete for the managed Lua sections. The current development phase is Devilspie2-backed window probing from the GTK configurator.

The immediate goal is intentionally small:

1. `python -m d2wc configure` runs from dom0 on Qubes.
2. The command starts a temporary Devilspie2 debug probe.
3. The user opens or focuses a normal application window while the probe is running.
4. The GTK window displays the Devilspie2-captured domain, class, title, screen geometry, and window geometry.
5. The window opens cleanly on the Qubes/XFCE target environment.
6. The window closes cleanly.
7. No config writes happen from this UI proof.
8. Rule editing UI remains a later stage.

Planned longer-term entry points remain:

1. Command or keyboard shortcut to open the configurator for a probed window.
2. Optional system tray menu for setup or troubleshooting.
3. Optional direct `Configure` flow after a user resizes a window and releases the primary mouse button.
4. Optional small pointer-anchored menu after resize with `Cancel` and `Configure`.

The ordered future roadmap is maintained in [`docs/implementation-plan.md`](docs/implementation-plan.md).
