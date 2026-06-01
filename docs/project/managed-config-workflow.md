# Managed Config Workflow

The managed-config model keeps `d2wc` managed Lua files separate from arbitrary user Devilspie2 scripts while still letting Devilspie2 load the active managed file normally.

Related implementation details live elsewhere:

1. [Installation Workflow](installation-workflow.md) documents installer behavior and managed Lua runtime refreshes.
2. [Lua Event Handoff](lua-event-handoff.md) documents automatic window-event launching, prompt mode, and handoff runtime settings.
3. [Backup Archives](backup-archives.md) documents backup archive creation and safe-save ordering.
4. [UI Flow](ui-flow.md) documents the configurator from the user's point of view.

## Current path model

The current Qubes/dom0 installer uses these user paths:

```text
~/.cache/d2wc/
~/.local/share/d2wc/source/
~/.config/d2wc/lua/
~/.config/d2wc/settings.json
~/.config/devilspie2/d2wc.lua
```

`~/.cache/d2wc/` stores the copied source archive cache.

`~/.local/share/d2wc/source/` stores the extracted local installation source.

`~/.config/d2wc/lua/` stores user-owned `d2wc` managed Lua files.

`~/.config/d2wc/settings.json` stores user UI preferences, such as toast timeout and toast opacity.

`~/.config/devilspie2/d2wc.lua` is the Devilspie2-facing integration symlink. It points to the active managed file under `~/.config/d2wc/lua/`.

The default managed file is:

```text
~/.config/d2wc/lua/d2wc.lua
```

The default Devilspie2 integration path is:

```text
~/.config/devilspie2/d2wc.lua -> ~/.config/d2wc/lua/d2wc.lua
```

## Ownership rules

`d2wc` owns managed Lua files under:

```text
~/.config/d2wc/lua/
```

`d2wc` also owns its own UI settings file:

```text
~/.config/d2wc/settings.json
```

`d2wc` does not own arbitrary Lua scripts under:

```text
~/.config/devilspie2/
```

The installer and configurator must not overwrite unrelated Devilspie2 scripts or unrelated symlinks.

## Managed Lua marker

A managed Lua file must contain this executable marker:

```lua
local D2WC_MANAGED = true
```

This replaces the earlier comment-based marker.

The marker is executable Lua state because comments are reasonably treated by users as removable notes. Removing `local D2WC_MANAGED = true` means the file is no longer accepted as a `d2wc` managed Lua file.

Files without this marker are skipped by runtime migrations and rejected by managed-file loading.

The missing-marker load message is:

```text
could not load config file: missing D2WC_MANAGED marker
```

The GTK configurator shows this case as a toast.

## Active managed file selection

The configurator tracks the currently open managed Lua file.

When launched without `--config`, startup uses this order:

1. Open the target of `~/.config/devilspie2/d2wc.lua` when that path is a safe symlink into `~/.config/d2wc/lua/`.
2. Fall back to `~/.config/d2wc/lua/d2wc.lua`.

When launched with `--config`, the supplied managed Lua file is opened directly.

All edit operations, validation, guarded writes, and backups target the currently open managed file.

The active managed file name is shown in the window title.

The configurator does not currently auto-reload when the managed Lua file changes on disk. Users can edit managed Lua files by hand, but they should reopen the configurator or reopen the file after external edits to avoid stale UI state.

Normal `d2wc` and `d2wc configure` launches use empty event data. The built-in example event fixture is used only when explicitly requested with `--event-fixture`.

## File Open

The configurator provides `File Open` from the menu.

`File Open`:

1. Defaults to `~/.config/d2wc/lua/`.
2. Lets the user choose a `*.lua` file.
3. Loads only files that contain `local D2WC_MANAGED = true` and can be parsed and validated as `d2wc` managed Lua files.
4. Leaves the current file open if the selected file cannot be loaded.
5. Updates the window title to show the active managed file.
6. Updates the Devilspie2 integration symlink to the selected managed file when safe.

The open workflow is for `d2wc` managed Lua files only. It must not become a generic Devilspie2 Lua editor.

## Save As

The configurator provides `Save As` from the menu.

`Save As`:

1. Defaults to `~/.config/d2wc/lua/`.
2. Requires a safe `.lua` filename.
3. Rejects empty names, names containing `/`, and names containing `..`.
4. Preserves the managed-file validation and safe-save model.
5. Reloads the saved file as the currently open managed file.
6. Updates the window title to show the new active managed file.
7. Updates the Devilspie2 integration symlink to the saved managed file when safe.
8. Shows success with a toast notification.

## Devilspie2 symlink updates

When the active managed file changes through `File Open` or `Save As`, the configurator updates:

```text
~/.config/devilspie2/d2wc.lua
```

The symlink may be updated only when safe.

Safe cases include:

1. The path does not exist.
2. The path is already a symlink into `~/.config/d2wc/lua/`.

Unsafe cases include:

1. The path is a regular file.
2. The path is a symlink outside `~/.config/d2wc/lua/`.

Unsafe cases produce a clear warning and leave the existing Devilspie2 file or symlink unchanged.

## Apply-after-save runtime behavior

After a successful row-level `Apply`, the configurator may run a transient Devilspie2 helper so the saved rule affects currently open windows immediately.

This helper is deliberately not a long-running Devilspie2 process manager.

The transient helper:

1. Builds a minimal managed `d2wc.lua` from the saved active file.
2. Includes only the saved Add/Modify rule and the minimum supporting context it needs.
3. Writes the temporary `d2wc.lua` into a temporary folder.
4. Runs `devilspie2 --folder <temporary-folder>`.
5. Gives Devilspie2 a short time to read and execute the temporary script.
6. Terminates and reaps only the process group it started.
7. Removes the temporary folder.

The helper does not run the user's full managed config. This prevents unrelated windows from being moved back to saved positions when the user only wanted to apply one changed row.

The helper is skipped for `Delete` actions and pure `GEOM` actions.

`WORKSPACE_PLACEMENT` transient apply includes the selected placement rule and the referenced geometry profile.

`LEFT_EDGE_CORRECTION` transient apply includes the selected correction rule, the matching placement rule, and the geometry profile referenced by that placement rule. The Lua runtime checks left-edge correction only after geometry has been resolved, so this supporting context is required for the transient correction to have an effect.

Transient apply warnings are reported separately from save success. A transient runtime warning must not turn an already successful managed-file save into a failed save.

## UI settings file

The configurator stores UI settings in:

```text
~/.config/d2wc/settings.json
```

The settings file is user-owned runtime configuration and must not be overwritten by installer updates.

The current settings view and user-facing settings behavior are documented in [UI Flow](ui-flow.md).

## Backup relationship

Backups follow the currently open managed file.

For example:

```text
~/.config/d2wc/lua/d2wc.lua
~/.config/d2wc/lua/d2wc.lua.bak.tgz
~/.config/d2wc/lua/work.lua
~/.config/d2wc/lua/work.lua.bak.tgz
```

Detailed backup behavior is documented in [Backup Archives](backup-archives.md).
