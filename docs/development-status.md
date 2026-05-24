# d2wc Development Status

## Current repository status

Current active branch:

```text
configurator-known-window-inventory
```

Current branch scope:

1. Continue from the PR #27 workflow-focused grid editor baseline.
2. Keep all writes scoped to the dedicated test config:

```text
~/.config/devilspie2/d2wc-test.lua
```

3. Keep real user config writes out of scope.
4. Build the known-window inventory in small testable slices before live capture is wired into the UI.

Current merged baseline:

```text
PR #27: Polish GTK configurator grid editor
Merge commit: fe36986712e4e985ea3b7e06f925d94ab4f7649c
```

Known-window parser foundation already merged into this branch:

```text
PR #26: Add initial known-window inventory parser for Devilspie2 event/debug text
Merge commit: bcb152c81f85e79c0927991fd81351f0e3f71321
```

The branch now includes the latest grid editor UI work, the known-window inventory parser foundation, target grouping/suppression helpers, pure grid row helpers, bounded inventory capture, and a continuous debug-output stream parser.

## Latest confirmed local verification

Latest verification reported on `configurator-known-window-inventory` after adding continuous inventory stream parsing:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
280 passed
```

Manual GTK verification previously reported after PR #27:

1. The workflow grid editor opens with `python3 -m d2wc configure --test-config`.
2. The row colour styling works.
3. Wrapped rows have aligned columns through GTK size groups.
4. The configurator publishes the stable window class `d2wc-configurator`.
5. The workspace selector reflects the current X11 workspace count when available, with a fallback to workspace 1.
6. Dirty rows split the action area into amber `Undo` and action-coloured `Apply` halves.
7. `Undo` restores unsaved row edits.
8. `Apply` remains available for dirty rows.
9. Successful apply actions show a compact translucent toast instead of a blocking dialog.

Verification reported on PR #26:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
The PR branch validation passed.
The full pytest suite passed locally with the known-window inventory parser tests included.
```

Earlier verification for PR #23:

```text
257 pytest tests passed.
The dom0 installed-wheel test was clear.
The managed editor add, modify, delete, Apply, and field-clearing behavior were confirmed.
```

## Current GTK UI behavior

The GTK test-config editor currently supports:

1. Workflow selector for all six managed sections:
   1. `Exclude`
   2. `Pin`
   3. `Workspace routes`
   4. `Window geometry`
   5. `Workspace placement`
   6. `Left edge correction`
2. Configured and not-configured row modes.
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
6. Workspace dropdown populated from the current X11 workspace count when available, with a fallback to workspace 1.
7. Row-level `Apply` actions.
8. Row-level unsaved-edit detection.
9. Dirty-row split action area:
   1. left half: amber `Undo`
   2. right half: action-coloured `Apply`
10. Action-based row colours:
   1. `Add` = green
   2. `Modify` = purple
   3. `Delete` = red
11. Compact translucent success toast:
   1. text: `Operation completed successfully.`
   2. detailed write target and backup output is no longer shown on success.
12. Errors and validation failures still use blocking dialogs.
13. Per-workflow help from `Menu -> Help`.
14. `F1` shortcut for the current workflow help.
15. Stable GTK/X11 class for Devilspie2 matching:

```text
d2wc-configurator
```

16. Menu currently has `Help`. Future `Configure` menu behavior is documented for notification settings.

## Known-window inventory parser, capture, stream, and row source

The first parser slice added `src/d2wc/event_inventory.py` and `tests/test_event_inventory.py`.

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
5. Convert inventory targets into Not configured grid rows for target-based workflows:
   1. `EXCLUDE`
   2. `PIN`
   3. `WORKSPACE_ROUTES`
   4. `WORKSPACE_PLACEMENT`
   5. `LEFT_EDGE_CORRECTION`
6. Do not create `GEOM` rows from inventory targets, because the inventory target only carries machine/application data.

Current refactor state:

1. `src/d2wc/ui/grid_rows.py` contains the pure row models and row builders.
2. `src/d2wc/ui/managed_actions.py` remains focused on GTK widget assembly, row controls, Apply/Undo behavior, toasts, and dialogs.
3. `tests/test_managed_grid_rows.py` now tests the row-builder module directly.

Not included yet:

1. Auto-refreshing GTK from live captured inventory.
2. UI lifecycle controls for starting/stopping the long-running monitor.
3. Handling quoted or whitespace-containing rule tokens in the grammar.

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
17. Dedicated test-config preparation and loading.
18. Test-config-only generic add, modify, and delete backend for all six managed sections.
19. Workflow-focused GTK grid editor scoped to `~/.config/devilspie2/d2wc-test.lua`.
20. Known-window inventory parser/model foundation for captured Devilspie2 debug/event text.
21. Known-window row-source helpers for Not configured target workflows.
22. Bounded and continuous known-window inventory capture helpers.

## Active next work

Known-window inventory is the active branch work.

Expected next slice:

1. Wire captured inventory targets into GTK Not configured rows.
2. Keep target suppression section-aware.
3. Keep the integration manually triggered or otherwise bounded at first.
4. Keep real config writes out of scope.
5. Avoid an unreviewed long-running background UX until the lifecycle and notification behavior are designed.

## Future restore work

Applied-write restore is documented as future work and should remain separate from unsaved row-level undo.

Expected restore direction:

1. Restore from the existing safe-save backup archive path.
2. Show backup members newest first.
3. Allow preview or inspection before restore.
4. Validate the restore candidate before replacing the active file.
5. Reuse staged write, sync, and backup safety rules.
6. Keep restore scoped to `~/.config/devilspie2/d2wc-test.lua` until real-config writes are explicitly reviewed.

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

For the current GTK test-config workflow:

```bash
python3 -m d2wc configure --test-config
```

For a clean GTK test-config baseline:

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
6. The known-window inventory branch treats this as list building, not single target selection.
7. For the inventory monitor, startup output builds the initial list and later output adds newly opened domain/class targets.

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
