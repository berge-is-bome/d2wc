# Managed Config Workflow

The managed-config model keeps `d2wc` managed Lua files separate from arbitrary user Devilspie2 scripts while still letting Devilspie2 load the active managed file normally.

Installer behavior is documented separately in [Installation Workflow](installation-workflow.md).

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

## Default managed Lua header

The bundled managed Lua template now uses a compact top header:

```lua
------------------------------------------------------------
-- devilspie2 workspace configurator
-- version 0.1.13
------------------------------------------------------------

local D2WC_MANAGED = true
```

Only the version line should change when the managed Lua runtime version changes.

Historical per-version change notes belong in Git history and project documentation, not in the top of the user-managed Lua file.

## Managed Lua runtime migrations

Installer runtime migrations are targeted insertions into marked managed Lua files.

The migration helper requires this managed marker:

```lua
local D2WC_MANAGED = true
```

Files without that marker are skipped.

For marked managed files, the migration may add missing runtime pieces such as:

1. latest header version comments,
2. `D2WC_EVENT_HANDOFF_ENABLED`,
3. `D2WC_EVENT_HANDOFF_ENTRY_POINT`,
4. `D2WC_CONFIGURATOR_CLASS`,
5. `D2WC_ACTION_PROMPT_CLASS`,
6. Lua event handoff helper code,
7. already-configured window suppression helper code,
8. the Lua event handoff call.

The migration must not rewrite the full bundled template. It must preserve user rules, user comments, spacing, and existing toggle values.

For example, if a user has already set:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = false
```

an installer update must not change it back to `true`.

If a user has already set:

```lua
local D2WC_EVENT_HANDOFF_ENTRY_POINT = "prompt"
```

an installer update must not change it back to `"configurator"`.

## Configurator behavior

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

## UI settings

The configurator stores UI settings in:

```text
~/.config/d2wc/settings.json
```

Current settings file values:

1. Toast timeout seconds.
2. Toast opacity.

`Menu -> Configure` replaces the main editor area with an in-window settings view.

The settings view has a left navigation column with:

1. `Behavior`
2. `Notifications`

`Behavior` controls these active managed Lua settings:

```lua
local D2WC_EVENT_HANDOFF_ENABLED = true
local D2WC_EVENT_HANDOFF_ENTRY_POINT = "configurator" -- values: "configurator", "prompt"
```

`D2WC_EVENT_HANDOFF_ENABLED` controls whether Devilspie2 opens `d2wc` automatically on new window events, for unconfigured windows.

`D2WC_EVENT_HANDOFF_ENTRY_POINT` selects whether automatic opening opens the configurator directly or shows the Cancel/Configure prompt button first.

Supported entry-point values:

1. `configurator`
2. `prompt`

Visible choices:

1. `Open configurator directly`
2. `Show Cancel/Configure button first`

`Notifications` controls the persisted toast timeout and toast opacity values.

The `Back` button returns to the managed rule editor.

The settings file is user-owned runtime configuration and must not be overwritten by installer updates.

## Prompt entry point

The prompt entry point is launched with:

```bash
d2wc prompt
```

The prompt appears near the bottom-right corner of the window that triggered the event when event geometry is available.

The prompt has two actions:

1. `Cancel`
2. `Configure`

The pointer is centered on `Cancel` when the prompt opens.

Choosing `Configure` opens the normal configurator for that event context.

The prompt publishes this GTK/X11 class:

```text
d2wc-action-prompt
```

The managed Lua runtime suppresses that class to avoid recursive prompt launches.

## Dropdown display rules

Machine, Application, and similar target dropdowns use `All` to display an empty match component.

For example, if Machine is `All`, the generated rule has no `d:` component. This keeps the Lua rule format unchanged while making the UI clearer.

Normal command launches do not add the built-in example fixture values to Machine/Application dropdowns. Example fixture values appear only when `--event-fixture` is explicitly requested or when real event data is supplied through Lua handoff arguments.

## Backup behavior

Backups follow the currently open managed file.

For example:

```text
~/.config/d2wc/lua/d2wc.lua
~/.config/d2wc/lua/d2wc.lua.bak.tgz
~/.config/d2wc/lua/work.lua
~/.config/d2wc/lua/work.lua.bak.tgz
```

Detailed backup behavior is documented in [Backup Archives](backup-archives.md).

## Current implementation notes

The installer and configurator now use the current path model.

The active managed Lua file may optionally open `d2wc` automatically for unconfigured normal windows through the Lua event handoff flow documented in [Lua Event Handoff](lua-event-handoff.md).
