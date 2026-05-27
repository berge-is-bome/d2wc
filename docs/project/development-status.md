# d2wc Development Status

## Current repository status

Public-release documentation branch:

```text
documentation-update-public-release
```

Public-release documentation PR:

```text
PR #30: Prepare documentation for public release
```

PR #30 scope:

1. Rewrite the README as a public-facing description of what `d2wc` is.
2. Split documentation into user-facing documentation under `docs/user/` and project documentation under `docs/project/`.
3. Replace the old Qubes installation notes and helper-archive documentation with [Install/Update for Qubes](../user/install-qubes.md).
4. Refresh stale documentation links and installer script references before the first public release.

Current merged baseline before PR #30:

```text
PR #29: Match action button width to dirty split state
Merge commit: d466f8d59f53abf0e390a3e1f68a31ed74f7414d
```

Recent merged baseline before PR #29:

```text
PR #28: Add known-window inventory integration
Merge commit: e45725c7a89c953eb5cd5da265e2db966c909247
```

Recent merged baseline before PR #28:

```text
PR #27: Polish GTK configurator grid editor
Merge commit: fe36986712e4e985ea3b7e06f925d94ab4f7649c
```

## Latest confirmed verification

Final verification before PR #29 was merged:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
282 passed
```

Manual verification reported during PR #29:

1. `python3 -m d2wc` opens the GTK configurator on the test machine.
2. `python3 -m d2wc configure` loads `~/.config/devilspie2/d2wc.lua` on the test machine.
3. The Qubes/dom0 source-tarball install flow works.
4. The dom0 installer preserves an existing `~/.config/devilspie2/d2wc.lua`.
5. The installed dom0 command opens the configurator from the real managed config after local config validation issues were corrected.
6. Normal `Apply` buttons match the width of the dirty `Undo` / `Apply` split state.

Before merging the public-release documentation branch, run the normal local verification path:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

## Current GTK UI behavior

The GTK managed-config editor currently supports:

1. Workflow selector for all six managed sections:
   1. `Exclude`
   2. `Pin`
   3. `Workspace routes`
   4. `Window geometry`
   5. `Workspace placement`
   6. `Left edge correction`
2. One top `Add` row per workflow, with configured rows below it.
3. Row-level `Action` selector for `Add`, `Modify`, and `Delete`.
4. Split rule fields instead of raw combined prefixed strings:
   1. `Machine`
   2. `Application`
   3. `Workspace`
   4. `Geometry profile`
   5. `Left edge`
   6. `Profile name`
   7. `X`, `Y`, `W`, and `H`
5. Searchable popup selectors for longer value lists.
6. Taller searchable dropdown popovers so more values are visible before scrolling.
7. Workspace dropdown populated from the current X11 workspace count when available, with a fallback to workspace 1.
8. Row-level `Apply` actions.
9. Row-level unsaved-edit detection.
10. Dirty-row split action area:
    1. left half: amber `Undo`
    2. right half: action-coloured `Apply`
11. Normal single-button `Apply` action area sized to match the dirty `Undo` / `Apply` split width.
12. Action-based row colours:
    1. `Add` = green
    2. `Modify` = purple
    3. `Delete` = red
13. Header row stays visible while configured rule rows scroll.
14. Compact success toast:
    1. text: `Operation completed successfully.`
    2. detailed write target and backup output is no longer shown on success.
15. Errors and validation failures still use blocking dialogs.
16. Per-workflow help from `Menu -> Help`.
17. `F1` shortcut for the current workflow help.
18. Stable GTK/X11 class for Devilspie2 matching:

```text
d2wc-configurator
```

19. Automatic inventory monitor captures startup and later known-window targets and adds their machine/application values to the top `Add` row dropdowns.

## Qubes/dom0 install behavior

The current Qubes source-archive workflow is documented in [Install/Update for Qubes](../user/install-qubes.md).

The current flow is:

1. Clone the repository in a networked DisposableVM.
2. Create `/tmp/d2wc.tgz` from the current Git checkout.
3. Keep the DisposableVM running until dom0 installation is finished.
4. Copy the dom0 installer from the DisposableVM into dom0.
5. Edit the DisposableVM name in the dom0 installer when needed.
6. Run the dom0 installer.
7. Shut down the DisposableVM after the install/update completes.

The dom0 installer behavior is:

1. Pulls `/tmp/d2wc.tgz` from the configured DisposableVM.
2. Extracts to `~/Qubes/d2wc`.
3. Creates `~/.config/devilspie2/d2wc.lua` from bundled `src/d2wc.lua` only if missing.
4. Removes a previous user-site `d2wc` installation when present.
5. Installs the new package into the dom0 user Python site without network access.
6. Configures `$HOME/.local/bin` for Bash or Fish with a managed shell-config block.
7. Launches the installed configurator on first install.
8. On later updates, reports that `d2wc` can be launched manually.

The normal installed launch command is:

```bash
d2wc
```

The explicit subcommand remains supported:

```bash
d2wc configure
```

## Known-window inventory parser, capture, stream, and row source

Current parser behavior:

1. Parse captured Devilspie2 debug/event text into `KnownWindowCandidate` records.
2. Accept structured keys such as `_QUBES_VMNAME`, `application_name`, `wm_class_instance`, and `window_type`.
3. Accept documented human-readable labels such as `Domain:`, `Application name:`, `Window Type:`, and `Class instance name:`.
4. Keep only `WINDOW_TYPE_NORMAL` records.
5. Normalize an empty Qubes VM name to `dom0`.
6. Normalize machine/domain text to lowercase.
7. Derive an application token from the rightmost class-instance segment after `:`.
8. Preserve the raw class instance value and source block for debugging.

Current capture and stream behavior:

1. `src/d2wc/event_inventory_capture.py` writes a temporary read-only Devilspie2 probe script.
2. The probe script prints only the values needed for inventory: domain/machine, window type, and class instance name.
3. The active user `d2wc.lua` rules script is not used for inventory capture.
4. The bounded snapshot helper captures startup output and turns it into candidates and targets.
5. `KnownWindowInventoryStreamParser` parses continuous debug output block by block.
6. Startup output creates the initial inventory.
7. Later debug output can add newly opened domain/class pairs while the monitor is running.
8. Repeated observations are kept internal and do not produce visible duplicate targets.
9. Stream behavior is tested with mocked process/output objects, so pytest does not require real Devilspie2.

Current row-source behavior:

1. Convert parsed `KnownWindowCandidate` observations into one selectable `KnownWindowTarget` per safe machine/application pair.
2. Keep repeated observations internal and do not display observation counts.
3. Skip unsafe whitespace-containing rule tokens until the grammar supports them.
4. Suppress targets already configured for the selected workflow.
5. Use inventory targets to populate Machine/Application dropdown values for target-based workflows.
6. Do not create `GEOM` suggestions from inventory targets, because the inventory target only carries machine/application data.

Current GTK integration behavior:

1. The managed editor accepts prepared inventory targets.
2. The inventory monitor starts automatically when the GTK configurator opens.
3. Startup debug output populates the initial Machine/Application dropdown values.
4. Later debug-output events add newly seen domain/class values while the configurator remains open.
5. Captured targets are merged into editor state without visible duplicate rows.
6. Each workflow uses one top `Add` row and configured rows below it.
7. Captured inventory values appear in the Machine/Application dropdowns for the top `Add` row.
8. The monitor is stopped when the GTK window closes.

## Current safe capability

The current Python core supports:

1. Editable development installation.
2. Read-only validation of managed Lua blocks.
3. Dry-run rendering to stdout.
4. Power-loss-oriented safe-save behavior.
5. Save preview by default.
6. Guarded CLI save behavior requiring `--write` before modification.
7. In-memory and guarded CLI add, modify, and delete operations for `GEOM`.
8. In-memory and guarded CLI add, modify, and delete operations for `WORKSPACE_PLACEMENT`.
9. In-memory and guarded CLI add, modify, and delete operations for `WORKSPACE_ROUTES`.
10. In-memory and guarded CLI add, modify, and delete operations for `PIN`.
11. In-memory and guarded CLI add, modify, and delete operations for `EXCLUDE`.
12. In-memory and guarded CLI add, modify, and delete operations for `LEFT_EDGE_CORRECTION`.
13. Marker-tail preservation for `-- add more here` in edited rule-list sections.
14. Token-order-independent rule parsing and modify/delete matching.
15. Exact duplicate target rejection where duplicates would make behavior ambiguous.
16. GTK event-data fixture and command-argument plumbing.
17. Dedicated test-config preparation and loading for development.
18. Managed-config GTK editor for `~/.config/devilspie2/d2wc.lua` by default.
19. Known-window inventory parser/model foundation for captured Devilspie2 debug/event text.
20. Bounded and continuous known-window inventory capture helpers.
21. Automatic GTK inventory monitor into Add-row dropdown values.
22. Qubes/dom0 source-tarball install/update support.

## Active next work

After PR #30, the next planned development slice remains Lua event handoff.

Lua event handoff means:

1. Devilspie2 Lua event captures event data directly.
2. Event data is passed safely into `python3 -m d2wc` or `d2wc`.
3. GTK opens with that specific event context.
4. This lower-level plumbing comes before any future automatic `configure this new window?` prompt flow.

The three-option user flow and suppression behavior should come after the handoff proof.

## Future restore work

Applied-write restore is documented as future work and should remain separate from unsaved row-level undo.

Expected restore direction:

1. Restore from the existing safe-save backup archive path.
2. Show backup members newest first.
3. Allow preview or inspection before restore.
4. Validate the restore candidate before replacing the active file.
5. Reuse staged write, sync, and backup safety rules.
6. Keep restore scoped carefully and review real-config restore behavior before enabling it broadly.

## Test command guidance

Install the project in editable mode from the repository root:

```bash
python3 -m pip install -e .
```

Use the four-command renderer verification path when renderer behavior changes:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m d2wc render --config src/d2wc.lua --stdout > /tmp/d2wc-rendered.lua
python3 -m d2wc validate --config /tmp/d2wc-rendered.lua
python3 -m pytest
```

When renderer behavior has not changed, use this verification path:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

For the normal GTK managed-config workflow:

```bash
python3 -m d2wc
```

For the explicit GTK managed-config workflow:

```bash
python3 -m d2wc configure
```

For the development test-config workflow:

```bash
python3 -m d2wc configure --test-config
```

For a clean development test-config baseline:

```bash
python3 -m d2wc configure --replace-test-config
```

## Useful Devilspie2 event data

Start with these event-provided functions:

```lua
get_class_instance_name()
get_window_property( '_QUBES_VMNAME' )
get_screen_geometry()
get_window_geometry()
```

Keep the exact known-working Qubes property call form:

```lua
get_window_property( '_QUBES_VMNAME' )
```

Known behavior:

1. `devilspie2 --debug` prints an initial startup dump for all currently known or processed windows.
2. After startup, `devilspie2 --debug` behaves like an append-only event stream.
3. Capturing the first debug output is not target selection.
4. Capturing the next event after startup is unreliable because menus and launchers can generate intermediary events.
5. The current `d2wc.lua` already filters non-normal windows with `WINDOW_TYPE_NORMAL`.
6. The known-window inventory monitor treats this as list building, not single target selection.
7. Startup output builds the initial list and later output adds newly opened domain/class targets.

## Historical Lua script preservation

The pre-repository `d2wc.lua` history has been preserved in Git and connected to `main`.

A tag points to the archived history:

```text
pre-repo-lua-history
```
