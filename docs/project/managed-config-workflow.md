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
~/.config/devilspie2/d2wc.lua
```

`~/.cache/d2wc/` stores the copied source archive cache.

`~/.local/share/d2wc/source/` stores the extracted local installation source.

`~/.config/d2wc/lua/` stores user-owned `d2wc` managed Lua files.

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

## Configurator direction

The configurator must move from the old dedicated test-config terminology to a real managed-config workflow.

The configurator should track the currently open managed Lua file.

The default open file should be:

```text
~/.config/d2wc/lua/d2wc.lua
```

All edit operations, validation, guarded writes, and backups should target the currently open managed file.

## File Open

The configurator should provide `File Open` from the menu.

`File Open` should:

1. Default to `~/.config/d2wc/lua/`.
2. Let the user choose a `*.lua` file.
3. Load only files that can be parsed and validated as `d2wc` managed Lua files.
4. Leave the current file open if the selected file cannot be loaded.
5. Update the window title, header, or status area to show the active managed file.
6. Update the Devilspie2 integration symlink to the selected managed file when safe.

The open workflow is for `d2wc` managed Lua files only. It must not become a generic Devilspie2 Lua editor.

## Save As

The configurator should provide `Save As` from the menu.

`Save As` should:

1. Default to `~/.config/d2wc/lua/`.
2. Require a safe `.lua` filename.
3. Reject empty names, names containing `/`, and names containing `..`.
4. Preserve the managed-file validation and safe-save model.
5. Reload the saved file as the currently open managed file.
6. Update the window title, header, or status area to show the new active managed file.
7. Update the Devilspie2 integration symlink to the saved managed file when safe.

## Devilspie2 symlink updates

When the active managed file changes through `File Open` or `Save As`, the configurator should update:

```text
~/.config/devilspie2/d2wc.lua
```

The symlink may be updated only when safe.

Safe cases include:

1. The path does not exist.
2. The path is already a symlink into `~/.config/d2wc/lua/`.

Unsafe cases include:

1. The path is a regular unmanaged file.
2. The path is a symlink outside `~/.config/d2wc/lua/`.

Unsafe cases should produce a clear warning and leave the existing Devilspie2 file or symlink unchanged.

## Backup behavior

Backups should follow the currently open managed file.

For example:

```text
~/.config/d2wc/lua/d2wc.lua
~/.config/d2wc/lua/d2wc.lua.bak.tgz
~/.config/d2wc/lua/work.lua
~/.config/d2wc/lua/work.lua.bak.tgz
```

## Current implementation gap

The installer already uses the new path model.

The configurator still needs plumbing updates:

1. Replace test-config naming with managed-config naming in the UI plumbing.
2. Track the current managed file in GTK state.
3. Add `File Open`.
4. Add `Save As`.
5. Refresh all editor rows after changing the current managed file.
6. Make all actions apply to the current managed file.
7. Update visible window title, header, or status text with the active managed file path.
8. Keep test-only helpers separate from public managed-config behavior.
