# d2wc Development Status

## Current repository status

Current active UI branch:

```text
configurator-grid-editor-ui
```

Current branch scope:

1. Polish the GTK test-config editor into a workflow-focused grid UI.
2. Keep all writes scoped to the dedicated test config:

```text
~/.config/devilspie2/d2wc-test.lua
```

3. Keep real user config writes out of scope.
4. Prepare this branch for a PR into `main`.

Previous merged baseline:

```text
PR #23: Add managed-section test-config actions
Merge commit: 7f4c0141b9a7a7220109ce43c2d65860a6f946dd
```

Known-window inventory work has moved to a separate active branch:

```text
configurator-known-window-inventory
```

That branch should handle cleaned `devilspie2 --debug` or Lua/Devilspie2 event inventory for not-configured windows. It is not part of the grid editor polish PR.

## Latest confirmed local verification

Verification reported for `configurator-grid-editor-ui`:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
python3 -m d2wc configure --test-config
```

Latest confirmed pytest result:

```text
262 passed
```

Manual GTK verification reported:

1. The workflow grid editor opens with `python3 -m d2wc configure --test-config`.
2. The row colour styling works.
3. Wrapped rows now have aligned columns through GTK size groups.
4. The configurator publishes the stable window class `d2wc-configurator`.
5. The workspace selector reflects the current X11 workspace count when available, with a fallback to workspace 1.
6. Dirty rows split the action area into amber `Undo` and action-coloured `Apply` halves.
7. `Undo` restores unsaved row edits.
8. `Apply` remains available for dirty rows.
9. Successful apply actions show a compact translucent toast instead of a blocking dialog.

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
11. Per-workflow help from `Menu -> Help`.
12. `F1` shortcut for the current workflow help.
13. Stable GTK/X11 class for Devilspie2 matching:

```text
d2wc-configurator
```

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

## Active next work outside this PR

Known-window inventory is the next active branch:

```text
configurator-known-window-inventory
```

Expected scope:

1. Capture or parse known `WINDOW_TYPE_NORMAL` windows from Devilspie2/Lua event data or `devilspie2 --debug` output.
2. Extract and normalize the Qubes VM name as `Machine`.
3. Extract and normalize the class instance token as `Application`.
4. Suppress rows already configured for the selected workflow.
5. Populate the not-configured row mode from the cleaned inventory.

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
6. The known-window inventory branch should treat this as list building, not single target selection.

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
