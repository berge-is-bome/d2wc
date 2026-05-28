# Managed Config Workflow

## Purpose

This document captures the current managed-config model for `d2wc`.

The goal is to keep `d2wc` managed Lua files separate from arbitrary user Devilspie2 scripts while still letting Devilspie2 load the active managed file normally.

## Current path model

The Qubes/dom0 installer uses these user paths:

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

## Installer behavior

Before replacing the extracted source tree in `~/.local/share/d2wc/source`, the installer copies and validates `/tmp/d2wc.tgz` from the selected source VM.

The installer then:

1. Extracts the local source tree under `~/.local/share/d2wc/source/`.
2. Installs the Python package with the user-site pip flow.
3. Creates `~/.config/d2wc/lua/` if needed.
4. Creates `~/.config/d2wc/lua/d2wc.lua` from the bundled template if a managed file is needed.
5. Creates or updates `~/.config/devilspie2/d2wc.lua` as a symlink only when safe.
6. Leaves unrelated `~/.config/devilspie2/` files and symlinks unchanged.
7. Leaves existing `~/.config/d2wc/settings.json` user settings unchanged.

On update, the installer preserves the active managed file selection when `~/.config/devilspie2/d2wc.lua` is already a safe symlink into `~/.config/d2wc/lua/`.

On update, if one or more `d2wc` configurator instances are running, the installer warns the user to close them and waits before continuing. The update continues only after no running `d2wc` process candidates remain.

## Configurator behavior

The configurator tracks the currently open managed Lua file.

When launched without `--config`, startup uses this order:

1. Open the target of `~/.config/devilspie2/d2wc.lua` when that path is a safe symlink into `~/.config/d2wc/lua/`.
2. Fall back to `~/.config/d2wc/lua/d2wc.lua`.

When launched with `--config`, the supplied managed Lua file is opened directly.

All edit operations, validation, guarded writes, and backups target the currently open managed file.

The active managed file name is shown in the window title.

The configurator does not currently auto-reload when the managed Lua file changes on disk. Users can edit managed Lua files by hand, but they should reopen the configurator or reopen the file after external edits to avoid stale UI state.

## File Open

The configurator provides `File Open` from the menu.

`File Open`:

1. Defaults to `~/.config/d2wc/lua/`.
2. Lets the user choose a `*.lua` file.
3. Loads only files that can be parsed and validated as `d2wc` managed Lua files.
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

## UI settings

The configurator stores UI settings in:

```text
~/.config/d2wc/settings.json
```

Current settings:

1. Toast timeout seconds.
2. Toast opacity.

The settings file is user-owned runtime configuration and must not be overwritten by installer updates.

## Dropdown display rules

Machine, Application, and similar target dropdowns use `All` to display an empty match component.

For example, if Machine is `All`, the generated rule has no `d:` component. This keeps the Lua rule format unchanged while making the UI clearer.

## Backup behavior

Backups follow the currently open managed file.

For example:

```text
~/.config/d2wc/lua/d2wc.lua
~/.config/d2wc/lua/d2wc.lua.bak.tgz
~/.config/d2wc/lua/work.lua
~/.config/d2wc/lua/work.lua.bak.tgz
```

## Current implementation notes

The installer and configurator now use the new path model.

The remaining intentional distinction is that test-only helpers still exist for development and automated tests, while public user workflows use managed-config language and paths.
