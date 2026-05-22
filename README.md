# d2wc

Devilspie2 Workspace Configurator.

`d2wc` is intended to make Linux window placement easier to configure by combining a `devilspie2` Lua rules script with a small configurator UI. The current implementation is the active Lua rules engine plus a Python configurator core proof with parser, validator, renderer, guarded CLI edit commands, safe-save behavior, the read-only GTK launch proof, and a read-only Qubes/dom0 selected-window geometry proof.

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

The GTK proof can open a read-only window launched by `python -m d2wc configure` or `d2wc configure`. The most recent merged desktop proof confirmed Qubes/dom0 selected-window geometry capture with `xwininfo -frame`. That proof is useful as a diagnostic, but it is no longer the active UI direction.

The active next direction is to build the GTK configurator around event-provided Devilspie2/Lua data. See [`docs/event-data-ui-direction.md`](docs/event-data-ui-direction.md).

Latest confirmed local verification is recorded in [`docs/development-status.md`](docs/development-status.md). The latest reported result after PR #15 manual work was the selected-window geometry proof working from dom0.

## Repository layout

```text
docs/
  development-status.md          Current PR status, latest local verification, and next work.
  event-data-ui-direction.md     Current GTK UI direction around Devilspie2 event data.
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

The GTK proof is read-only. It does not read or write config files.

Comments and blank separator lines inside the managed Lua sections are treated as user-managed content. The renderer should preserve them where practical, especially in rule-list sections where comments explain why a rule exists.

## Development direction

The CLI/core editing proof phase is complete for the managed Lua sections. The next development phase is the event-data GTK UI proof.

The immediate goal is intentionally small:

1. Accept representative Devilspie2/Lua event data from a Python fixture or command arguments.
2. Open GTK with clear sections for identity and geometry.
3. Display the captured event values.
4. Perform no config writes.
5. Perform no automatic rule generation.
6. Avoid live target-selection experiments in this branch.
7. Later UI stages can wire displayed event data into the already-tested `GEOM` and `WORKSPACE_PLACEMENT` core edit operations first.

Important direction notes:

1. Devilspie2/Lua remains the event source.
2. If the user chooses the configurator from a window event, GTK should open with the data captured from that Lua event.
3. Duplicate configurator launches for intermediary events are acceptable for now.
4. Later suppression logic should avoid automatically opening the configurator for windows that already have a profile or handling rule.

Planned longer-term entry points remain:

1. Command or keyboard shortcut to open the configurator for event-provided window data.
2. Optional system tray menu for setup or troubleshooting.
3. Optional direct `Configure` flow after a user resizes a window and releases the primary mouse button.
4. Optional small pointer-anchored menu after resize with `Cancel` and `Configure`.

The ordered future roadmap is maintained in [`docs/implementation-plan.md`](docs/implementation-plan.md).
