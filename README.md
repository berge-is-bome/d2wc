# d2wc

Devilspie2 Workspace Configurator.

`d2wc` combines the active `devilspie2` Lua rules script with a Python configurator core and a GTK configurator proof. The Lua script remains the runtime engine. The Python side provides parser, validator, renderer, guarded CLI edit commands, safe-save behavior, event-data plumbing, and a GTK test-config editor.

## Current status

The repository starts from the current `d2wc` Lua script version `0.1.12.3`.

The active Lua script supports:

1. Excluding domains, classes, or domain/class combinations from automation.
2. Pinning selected windows so they appear on all workspaces.
3. Routing windows to workspaces by domain, class, or domain/class match.
4. Applying named geometry profiles to matching windows.
5. Applying optional left-edge correction for windows that do not land exactly at `x = 0` when `set_window_geometry()` is used.

The Python core supports validation, render preview, safe-save behavior, and guarded add, modify, and delete commands for all managed Lua sections:

1. `GEOM`
2. `WORKSPACE_PLACEMENT`
3. `WORKSPACE_ROUTES`
4. `PIN`
5. `EXCLUDE`
6. `LEFT_EDGE_CORRECTION`

The GTK UI currently uses this dedicated test config:

```text
~/.config/devilspie2/d2wc-test.lua
```

The UI can prepare, load, replace, display, and edit that test config. It uses a managed-section editor with `Section`, `Action`, existing-entry, target-entry, profile, workspace, and geometry fields, plus a single `Apply` action. The editor supports add, modify, and delete for all six managed sections.

The real user config is not the GTK write target at this stage. The active direction is still to build around event-provided Devilspie2/Lua data. See [`docs/event-data-ui-direction.md`](docs/event-data-ui-direction.md).

Latest confirmed local verification is recorded in [`docs/development-status.md`](docs/development-status.md).

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
tests/                           Python tests for the configurator core and UI helpers.
```

## Local development

Install `python3-pip` with your package manager, then install the project in editable mode from the repository root:

```bash
python3 -m pip install -e .
```

Re-run the editable install command after switching to a branch that changes `[project.scripts]`; otherwise the generated `d2wc` console wrapper may still point at the previously installed entry point.

For normal source-checkout testing after editable install:

```bash
python3 -m d2wc --help
python3 -m d2wc validate --config src/d2wc.lua
python3 -m d2wc render --config src/d2wc.lua --stdout
python3 -m pytest
```

When renderer behavior changes, use the stronger renderer verification path:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python3 -m d2wc validate --config /tmp/d2wc-rendered.lua
python3 -m pytest
```

The `validate` command is read-only. It parses and validates the managed Lua sections but does not modify any file.

The `render` command is read-only in ordinary preview use. Guarded edit commands preview by default and apply changes only when `--write` is supplied.

## GTK test-config workflow

Launch the GTK configurator after installing the current checkout:

```bash
python3 -m d2wc configure
```

For UI development, use the dedicated test config commands:

```bash
python3 -m d2wc configure --init-test-config
python3 -m d2wc configure --test-config
python3 -m d2wc configure --replace-test-config
```

Command meanings:

1. `--init-test-config` creates `~/.config/devilspie2/d2wc-test.lua` from bundled `src/d2wc.lua` if it is missing, then loads it.
2. `--test-config` loads the existing `~/.config/devilspie2/d2wc-test.lua` without replacing it.
3. `--replace-test-config` replaces `~/.config/devilspie2/d2wc-test.lua` from bundled `src/d2wc.lua`, then loads it.
4. `--test-config-path <path>` overrides the test config path for disposable automated tests and isolated manual experiments.

`d2wc` uses `~/.config/devilspie2/d2wc-test.lua` as the GTK test-config path. Devilspie2 loads Lua scripts from `~/.config/devilspie2/`; users with custom Devilspie2 layouts need to adapt their own runtime setup accordingly.

Current GTK test-config features:

1. Managed-section editor at the top of the window.
2. `Section` selector for all six managed sections.
3. `Action` selector for `Add`, `Modify`, and `Delete`.
4. Section/action-aware editable fields.
5. Single `Apply` button next to `Close`.
6. Display of the current managed-section contents below the editor.
7. Automatic reload of displayed test-config sections after each successful edit.
8. Action result text with success/error details and backup path.

Comments and blank separator lines inside the managed Lua sections are treated as user-managed content. The renderer should preserve them where practical, especially in rule-list sections where comments explain why a rule exists.

## Development direction

The CLI/core editing proof phase is complete for the managed Lua sections. The GTK development phase is focused on a test-config UI that exercises the same tested core edit operations safely before enabling real user config writes.

Current UI priorities:

1. Keep the test-config editor safe and clear.
2. Continue using `~/.config/devilspie2/d2wc-test.lua` as the GTK UI write target.
3. Build the next spreadsheet-style editor on a follow-up branch.
4. Keep real config writes behind an explicit future design review.
5. Later, wire Lua event handoff and suppression for already-known windows.

Important direction notes:

1. Devilspie2/Lua remains the event source.
2. If the user chooses the configurator from a window event, GTK should open with the data captured from that Lua event.
3. Duplicate configurator launches for intermediary events are acceptable for now.
4. Later suppression logic should avoid automatically opening the configurator for windows that already have a profile or handling rule.

The ordered future roadmap is maintained in [`docs/implementation-plan.md`](docs/implementation-plan.md).
