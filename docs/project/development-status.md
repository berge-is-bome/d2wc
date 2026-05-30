# d2wc Development Status

## Current repository status

The current `main` branch is the first public beta baseline for the Qubes OS and Devilspie2 workflow.

The `gtk-ui-improvement-post-lua-handoff` branch adds GTK polish, prompt-entry workflow, managed-marker cleanup, and documentation updates on top of that baseline.

Recent public-release milestones already merged to `main`:

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
3. PR #32: `Rework Qubes installer and managed-config XDG integration`
   1. Preserved the active managed file through safe symlink handling.
   2. Kept bare `d2wc` as the normal installed configurator launch command.
   3. Kept `d2wc configure` as the explicit supported configurator subcommand.
4. PR #34: `Add Lua event handoff workflow`
   1. Added Lua event handoff from `src/d2wc.lua` to `d2wc`.
   2. Added `D2WC_EVENT_HANDOFF_ENABLED` as the per-managed-file handoff toggle.
   3. Added configurator recursion suppression through the stable GTK/X11 class `d2wc-configurator`.
   4. Added automatic launch suppression for windows that already match managed target rules.
   5. Added targeted managed Lua runtime migration during installer updates.

Recent branch work on `gtk-ui-improvement-post-lua-handoff`:

1. Replaced the separate Configure dialog with an in-window settings view.
2. Added `Behavior` and `Notifications` settings pages.
3. Moved automatic handoff controls under `Menu -> Configure -> Behavior`.
4. Added `D2WC_EVENT_HANDOFF_ENTRY_POINT` with `configurator` and `prompt` modes.
5. Added the `d2wc prompt` entry point.
6. Added the Cancel/Configure prompt button for unconfigured window events.
7. Positioned the prompt near the bottom-right corner of the event window using geometry passed from Devilspie2.
8. Added prompt recursion suppression with the GTK/X11 class `d2wc-action-prompt`.
9. Added single-instance locks for configurator and prompt processes.
10. Replaced the comment-based managed marker with `local D2WC_MANAGED = true`.
11. Updated installer, migration, snapshot, and test paths to require the new marker.
12. Simplified the default managed Lua header to version-only project identification.
13. Adopted the `0.1.13` managed Lua template structure.
14. Removed the old two-point GTK font-size override.
15. Changed normal `d2wc` and `d2wc configure` launches so the built-in event fixture is opt-in only.
16. Normalized the missing-marker load error to `could not load config file: missing D2WC_MANAGED marker`.
17. Changed missing-marker load failures to use a toast instead of the main error view.
18. Updated tests for the new marker and opt-in event-fixture behavior.

## Latest confirmed verification

Latest verification before these final documentation updates was reported as:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

Result:

```text
292 passed
```

After the final documentation updates and any local commits, run the normal verification path again:

```bash
python3 -m d2wc validate --config src/d2wc.lua
python3 -m pytest
```

## Public beta scope

`d2wc` remains ready for its intended first public beta release scope once the current branch is verified and merged.

Current public target:

1. Qubes OS with XFCE.
2. Devilspie2 window rules.
3. User-managed `d2wc` Lua files, not arbitrary pre-existing Devilspie2 Lua scripts.
4. Source-archive install/update flow for dom0.
5. GTK configurator as the normal user path for managing rules.
6. Optional automatic configurator launch for unconfigured normal windows through Lua event handoff.
7. Optional prompt button handoff for users who prefer a confirm-before-configure workflow.

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
16. Missing managed-marker load errors shown as toasts.
17. Other errors and validation failures still use blocking dialogs.
18. Per-workflow help from `Menu -> Help`.
19. `F1` shortcut for the current workflow help.
20. Stable GTK/X11 class for Devilspie2 matching:

```text
d2wc-configurator
```

21. Automatic inventory monitor captures startup and later known-window targets and adds their machine/application values to the top `Add` row dropdowns.
22. File Open for choosing another `d2wc` managed Lua file.
23. Save As for saving the current managed Lua file under a safe new name.
24. Window title shows the active managed file.
25. Edit operations, validation, guarded writes, and backups follow the currently open managed file.
26. Machine, Application, and similar target dropdowns display blank match components as `All` while preserving the generated Lua rule format.
27. `Menu -> Configure` opens an in-window settings view:
    1. `Behavior`
    2. `Notifications`
28. `Behavior` toggles `D2WC_EVENT_HANDOFF_ENABLED` in the active managed Lua file.
29. `Behavior` selects `D2WC_EVENT_HANDOFF_ENTRY_POINT` in the active managed Lua file.
30. `Notifications` controls toast timeout and toast opacity.
31. Normal command launches do not inject the example event fixture unless `--event-fixture` is explicitly requested.

The configurator does not currently auto-reload when the managed Lua file changes on disk. Users who edit a managed Lua file externally should reopen the configurator or reopen the file before continuing UI edits.

## Qubes/dom0 install behavior

The current Qubes source-archive workflow is documented in [Install/Update for Qubes](../user/install-qubes.md).

The current flow is:

1. Clone the repository in a networked source VM.
2. Create `/tmp/d2wc.tgz` from the current Git checkout.
3. Keep the source VM running until dom0 installation is finished.
4. Copy the dom0 installer from the source VM into dom0.
5. Run the dom0 installer with the source VM name as an argument, or let the installer show a `zenity` chooser or command-line prompt.
6. If the source VM was a disposable it can now be closed.

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
6. Creates `~/.config/d2wc/lua/d2wc.lua` from the bundled managed template on first install.
7. Runs targeted runtime migrations over marked managed Lua files under `~/.config/d2wc/lua/`.
8. Creates or updates `~/.config/devilspie2/d2wc.lua` as a symlink only when safe.
9. Preserves unrelated files and symlinks under `~/.config/devilspie2/`.
10. Preserves existing `~/.config/d2wc/settings.json` user settings.
11. Warns and waits if one or more `d2wc` configurator instances are running during an update.

The installer now requires managed Lua files to contain:

```lua
local D2WC_MANAGED = true
```

Files without that marker are not treated as `d2wc` managed files.

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

## Lua event handoff behavior

Lua event handoff is documented in [Lua Event Handoff](lua-event-handoff.md).

Current behavior:

1. Devilspie2 runs the active managed Lua file on window events.
2. `d2wc.lua` filters to `WINDOW_TYPE_NORMAL` windows.
3. `D2WC_EVENT_HANDOFF_ENABLED` controls automatic launching per managed Lua file.
4. `D2WC_EVENT_HANDOFF_ENTRY_POINT` selects direct configurator or prompt mode.
5. The configurator's GTK/X11 class `d2wc-configurator` is suppressed to avoid recursive configurator launches.
6. The prompt's GTK/X11 class `d2wc-action-prompt` is suppressed to avoid recursive prompt launches.
7. Windows already matching managed target rules are suppressed.
8. `GEOM` alone does not suppress handoff because geometry profiles do not target windows by themselves.
9. Prompt mode receives event-window geometry from Devilspie2 and places the prompt near that window.

Configured-window suppression counts these managed sections:

1. `EXCLUDE`
2. `PIN`
3. `WORKSPACE_ROUTES`
4. `WORKSPACE_PLACEMENT`
5. `LEFT_EDGE_CORRECTION`
