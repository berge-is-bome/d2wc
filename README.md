# d2wc

Devilspie2 Workspace Configurator.

Created by André in collaboration with ChatGPT.

`d2wc` combines the active `devilspie2` Lua rules script with a Python configurator core and a GTK configurator proof. The Lua script remains the runtime engine. The Python side provides parser, validator, renderer, guarded CLI edit commands, safe-save behavior, event-data plumbing, a GTK test-config editor, and the first known-window inventory parser foundation.

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

The known-window inventory work has an initial parser in `src/d2wc/event_inventory.py`. It parses raw Devilspie2 debug/event text into normalized `KnownWindowCandidate` records, keeps only `WINDOW_TYPE_NORMAL` windows, normalizes the Qubes machine/domain value, and derives an application token from the class instance value. This is a parser/model/test slice only. It does not yet start `devilspie2 --debug`, capture live process output, build the Not configured row source, or populate GTK rows.

The GTK UI currently uses this dedicated test config:

```text
~/.config/devilspie2/d2wc-test.lua
```

The UI can prepare, load, replace, and edit that test config. It uses a workflow-focused managed-section editor with normalized workflow labels, split rule-part fields, searchable selectors for machine/application/profile values, row-level `Apply` actions, action-based row colors, dirty-row `Undo`, compact success toasts, and per-workflow help through the menu or `F1`. The editor supports add, modify, and delete for all six managed sections.

The real user config is not the GTK write target at this stage. The active direction is still to build around event-provided Devilspie2/Lua data. See [`docs/event-data-ui-direction.md`](docs/event-data-ui-direction.md).

Latest confirmed local verification is recorded in [`docs/development-status.md`](docs/development-status.md).

## Repository layout

```text
docs/
  backup-archives.md            Backup archive behavior for guarded writes.
  configurator-notification-settings.md
                                 Future Configure menu notification settings.
  development-status.md         Current PR status, latest local verification, and next work.
  event-data-ui-direction.md    Current GTK UI direction around Devilspie2 event data.
  product-development-brief.md  In-depth product and UI direction.
  lua-configurables.md          User-facing explanation of the Lua configuration sections.
  lua-design-history.md         Design context recovered from archived pre-repository Lua history.
  repository-layout.md          Repository structure and development conventions.
src/
  d2wc.lua                      Current devilspie2 Lua rules script.
  d2wc/                         Python configurator core, desktop integration, and GTK UI proof.
tests/                          Python tests for the configurator core and UI helpers.
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

Before a guarded write replaces a Lua config, `d2wc` stores the previous config snapshot as a timestamped member inside a per-config `.bak.tgz` archive. See [`docs/backup-archives.md`](docs/backup-archives.md).

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

1. Workflow selector for all six managed sections.
2. Configured and not-configured row views.
3. Row-level `Action` selector for `Add`, `Modify`, and `Delete`.
4. Split rule fields such as `Machine`, `Application`, `Geometry profile`, `Workspace`, and `Left edge`.
5. Searchable popup selectors for longer value lists.
6. Workspace dropdown populated from the X11 workspace count when available, with a fallback to workspace 1.
7. Row-level `Apply` buttons with compact success toasts.
8. Dirty rows split the action area into amber `Undo` and action-coloured `Apply` halves.
9. Action-based row coloring for add, modify, and delete rows.
10. Per-workflow help from the `Menu` button or `F1`.
11. Stable GTK/X11 class for Devilspie2 matching: `d2wc-configurator`.

Comments and blank separator lines inside the managed Lua sections are treated as user-managed content. The renderer should preserve them where practical, especially in rule-list sections where comments explain why a rule exists.

## Known-window inventory parser

The first known-window inventory slice is intentionally narrow and testable. `parse_known_window_candidates()` accepts captured Devilspie2 debug/event text and returns normalized `KnownWindowCandidate` records.

The parser currently supports both structured key names and the human-readable labels used by the documented manual probe, including:

1. `Domain:`
2. `Application name:`
3. `Window name:`
4. `Window Type:`
5. `Class instance name:`
6. `Window class:`
7. `Screen Geometry:`
8. `Window geometry:`

This parser is a foundation for the future Not configured view. It does not yet provide a live process-capture loop, cleaned row source, suppression layer, or GTK row population.

## Development direction

The CLI/core editing proof phase is complete for the managed Lua sections. The GTK development phase is focused on a test-config UI that exercises the same tested core edit operations safely before enabling real user config writes.

Current UI priorities:

1. Keep the test-config editor safe and clear.
2. Continue using `~/.config/devilspie2/d2wc-test.lua` as the GTK UI write target.
3. Continue refining the workflow-focused grid editor behavior on top of the PR #27 baseline when needed.
4. Build the known-window inventory from parsed Devilspie2 debug/event output before live process capture is wired deeply into the UI.
5. Keep real config writes behind an explicit future design review.
6. Later, wire Lua event handoff and suppression for already-known windows.

Important direction notes:

1. Devilspie2/Lua remains the event source.
2. If the user chooses the configurator from a window event, GTK should open with the data captured from that Lua event.
3. Duplicate configurator launches for intermediary events are acceptable for now.
4. Later suppression logic should avoid automatically opening the configurator for windows that already have a profile or handling rule.

The ordered future roadmap is maintained in [`docs/implementation-plan.md`](docs/implementation-plan.md).
