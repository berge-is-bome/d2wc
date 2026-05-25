# d2wc Development Status

## Current repository status

Current active branch:

```text
configurator-action-button-size
```

Current branch scope:

1. Polish the GTK managed-config editor action-button sizing and small usability details.
2. Add the Qubes/dom0 source-tarball install and update workflow.
3. Make the installed `d2wc` command open the configurator directly.
4. Load the d2wc-managed real config by default:

```text
~/.config/devilspie2/d2wc.lua
```

5. Keep existing user Devilspie2 scripts untouched. `d2wc` owns only `d2wc.lua`.

Current merged baseline:

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

Verification reported before PR #28 was merged:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
281 passed
```

Manual GTK smoke testing after PR #28 confirmed that automatic known-window inventory values populate the Machine/Application dropdowns.

Manual verification reported during PR #29:

1. `python3 -m d2wc` opens the GTK configurator on the test machine.
2. `python3 -m d2wc configure` loads `~/.config/devilspie2/d2wc.lua` on the test machine.
3. The Qubes/dom0 source-tarball install flow works.
4. The dom0 installer preserves an existing `~/.config/devilspie2/d2wc.lua`.
5. The installed dom0 command opens the configurator from the real managed config after local config validation issues were corrected.

Before merging PR #29, run the normal local verification path:

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
11. Normal single-button `Apply` action area sized to match the dirty `Undo`/`Apply` split width.
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

The Qubes source-tarball workflow now has two helper scripts:

1. `d2wc-prepare-archive.sh`
   1. Runs in a networked DisposableVM.
   2. Clones or updates the repo checkout.
   3. Creates `/tmp/d2wc.tgz`.
   4. Copies `d2wc-installation.sh` to `/tmp/d2wc-installation.sh`.
2. `d2wc-installation.sh`
   1. Runs in dom0.
   2. Uses `VM="disp1234"` as the documented placeholder.
   3. Pulls `/tmp/d2wc.tgz` from that VM.
   4. Extracts to `~/Qubes/d2wc`.
   5. Creates `~/.config/devilspie2/d2wc.lua` from bundled `src/d2wc.lua` only if missing.
   6. Reinstalls the Python package into the dom0 user site.
   7. Configures `$HOME/.local/bin` for Bash or Fish with a managed shell-config block.
   8. Launches the installed configurator using `$HOME/.local/bin/d2wc`.

The user-facing install guide is:

```text
docs/qubes-dom0-installation.md
```

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
22. Qubes/dom0 source-tarball install/update helper scripts.

## Active next work

After PR #29, the next planned development slice is Lua event handoff.

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
archive/d2wc-lua-pre-repo-history
```

Inspect the preserved Lua evolution with:

```bash
git log --oneline --reverse archive/d2wc-lua-pre-repo-history -- src/d2wc.lua
```

Design context recovered from that history is recorded in [Lua Design History Notes](lua-design-history.md).

## Completed proof summary

1. PR #3: safe-save proof.
2. PR #4: `GEOM` edit proof.
3. PR #5: `WORKSPACE_PLACEMENT` edit proof.
4. PR #7, PR #8, PR #9: `WORKSPACE_ROUTES` edit proof and comment preservation fixes.
5. PR #11: `PIN` and `EXCLUDE` edit proof.
6. PR #12: `LEFT_EDGE_CORRECTION` edit proof.
7. PR #13: documentation refresh after managed-section edit proofs.
8. PR #14: first GTK launch proof.
9. PR #15: selected-window geometry diagnostic proof.
10. PR #19: event-data GTK UI proof.
11. PR #20: read-only event proposal preview.
12. PR #21: test-config configurator UI proof.
13. PR #22: test-config proposal action buttons.
14. PR #23: managed-section test-config actions.
15. PR #26: known-window inventory parser foundation.
16. PR #27: workflow-focused grid editor polish.
17. PR #28: known-window inventory integration.
18. PR #29: Qubes install flow, real managed config launch path, and GTK polish.
