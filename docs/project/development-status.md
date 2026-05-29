# d2wc Development Status

## Current repository status

The current `main` branch is the first public beta baseline for the Qubes OS and Devilspie2 workflow.

Recent public-release milestones:

1. PR #30: `Prepare documentation for public release`
   1. Reworked the README as a public-facing description of what `d2wc` is.
   2. Split documentation into user-facing documentation under `docs/user/` and project documentation under `docs/project/`.
   3. Replaced old Qubes installation notes with [Install/Update for Qubes](../user/install-qubes.md).
2. PR #31: `Rework Qubes installer and managed config workflow`
   1. Removed the hardcoded source VM from `install-qubes.sh`.
   2. Added positional source-VM, `zenity`, and command-line prompt installer paths.
   3. Moved user-owned managed Lua files under `~/.config/d2wc/lua/`.
   4. Moved the extracted local installation source under `~/.local/share/d2wc/source/`.
   5. Kept `~/.config/devilspie2/d2wc.lua` as the Devilspie2-facing integration symlink.
   6. Added configurator File Open and Save As support for `d2wc` managed Lua files.
   7. Preserved unrelated Devilspie2 scripts and unrelated symlinks.

Recent merged baseline before the public-release documentation and installer workflow work:

```text
PR #29: Match action button width to dirty split state
Merge commit: d466f8d59f53abf0e390a3e1f68a31ed74f7414d
```

## Latest confirmed verification

Latest verification reported for PR #31:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
295 passed
```

Manual validation reported for PR #31:

1. Installer update warns when `d2wc` is already running.
2. Installer update preserves the active managed file symlink.
3. `d2wc` opens the active symlink target on startup.
4. Configure toast settings persist after close, reopen, and update.
5. Save As and File Open safely update `~/.config/devilspie2/d2wc.lua`.
6. Selecting `All` immediately displays `All`, not `Machine/Application`.
7. Dropdown placement behavior is fixed.

Before tagging or publishing the first public beta, run the normal local verification path again from current `main`:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

## Public beta scope

`d2wc` is ready for its first public beta release for the intended Qubes OS and Devilspie2 workflow.

Current public target:

1. Qubes OS with XFCE.
2. Devilspie2 window rules.
3. User-managed `d2wc` Lua files, not arbitrary pre-existing Devilspie2 Lua scripts.
4. Source-archive install/update flow for dom0.
5. GTK configurator as the normal user path for managing rules.

Broader X11/Linux desktop use remains part of the project direction, but should be treated as experimental until tested deliberately.

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
14. Compact success toasts.
15. Persistent toast timeout and opacity settings under `~/.config/d2wc/settings.json`.
16. Errors and validation failures still use blocking dialogs.
17. Per-workflow help from `Menu -> Help`.
18. `F1` shortcut for the current workflow help.
19. Stable GTK/X11 class for Devilspie2 matching:

```text
d2wc-configurator
```

20. Automatic inventory monitor captures startup and later known-window targets and adds their machine/application values to the top `Add` row dropdowns.
21. File Open for choosing another `d2wc` managed Lua file.
22. Save As for saving the current managed Lua file under a safe new name.
23. Window title shows the active managed file.
24. Edit operations, validation, guarded writes, and backups follow the currently open managed file.
25. Machine, Application, and similar target dropdowns display blank match components as `All` while preserving the generated Lua rule format.

The configurator does not currently auto-reload when the managed Lua file changes on disk. Users who edit a managed Lua file externally should reopen the configurator or reopen the file before continuing UI edits.

## Qubes/dom0 install behavior

The current Qubes source-archive workflow is documented in [Install/Update for Qubes](../user/install-qubes.md).

The current flow is:

1. Clone the repository in a networked source VM.
2. Create `/tmp/d2wc.tgz` from the current Git checkout.
3. Keep the source VM running until dom0 installation is finished.
4. Copy the dom0 installer from the source VM into dom0.
5. Run the dom0 installer with the source VM name as an argument, or let the installer show a `zenity` chooser or command-line prompt.
6. Shut down the source VM after the install/update completes.

The current user-path layout is:

```text
~/.cache/d2wc/
~/.local/share/d2wc/source/
~/.config/d2wc/lua/
~/.config/d2wc/settings.json
~/.config/devilspie2/d2wc.lua
```

The dom0 installer behavior is:

1. Copies and validates `/tmp/d2wc.tgz` from the selected source VM before replacing the local source tree.
2. Stages the copied archive under `~/.cache/d2wc/`.
3. Extracts the local installation source under `~/.local/share/d2wc/source/`.
4. Installs the Python package into the dom0 user Python site without dom0 network access.
5. Creates `~/.config/d2wc/lua/` if needed.
6. Creates `~/.config/d2wc/lua/d2wc.lua` from the bundled managed template only when a managed file is needed.
7. Creates or updates `~/.config/devilspie2/d2wc.lua` as a symlink only when safe.
8. Preserves unrelated files and symlinks under `~/.config/devilspie2/`.
9. Preserves existing `~/.config/d2wc/settings.json` user settings.
10. Warns and waits if one or more `d2wc` configurator instances are running during an update.

The normal installed launch command is:

```bash
d2wc
```

The explicit subcommand remains supported:

```bash
d2wc configure
```

## Managed config model

User-owned `d2wc` managed Lua files live under:

```text
~/.config/d2wc/lua/
```

The default managed file is:

```text
~/.config/d2wc/lua/d2wc.lua
```

Devilspie2 reads the active managed file through:

```text
~/.config/devilspie2/d2wc.lua
```

That path is expected to be a symlink into `~/.config/d2wc/lua/` when managed by `d2wc`.

`d2wc` must not overwrite arbitrary Devilspie2 Lua scripts or unrelated symlinks. File Open and Save As are only for `d2wc` managed Lua files that pass the managed-file validation rules.

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
18. Managed-config GTK editor for the active managed file.
19. File Open and Save As for `d2wc` managed Lua files.
20. Safe Devilspie2 integration symlink updates for the active managed file.
21. Persistent UI settings under `~/.config/d2wc/settings.json`.
22. Known-window inventory parser/model foundation for captured Devilspie2 debug/event text.
23. Bounded and continuous known-window inventory capture helpers.
24. Automatic GTK inventory monitor into Add-row dropdown values.
25. Qubes/dom0 source-archive install/update support.

## Active next work

The next planned development slice remains Lua event handoff.

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
