# d2wc Runtime Architecture

Runtime architecture records how the active pieces of `d2wc` fit together and where future runtime responsibilities should land.

Detailed implemented behavior belongs in the focused references below:

1. [Lua Event Handoff](lua-event-handoff.md) documents automatic window-event launching, prompt mode, recursion suppression, configured-window suppression, and managed Lua runtime migrations.
2. [Lua Configurables](lua-configurables.md) documents the internal managed Lua rule grammar and rule-section behavior.
3. [Managed Config Workflow](managed-config-workflow.md) documents active managed-file ownership, path selection, File Open, Save As, and Devilspie2 symlink safety.
4. [Installation Workflow](installation-workflow.md) documents installer behavior and managed Lua runtime refreshes.
5. [Backup Archives](backup-archives.md) documents backup archive creation and safe-save ordering.
6. [UI Flow](ui-flow.md) documents the user-facing configurator behavior.
7. [Event Monitoring](event-monitoring.md) documents later post-resize/event-monitoring work.
8. [Implementation Plan](implementation-plan.md) tracks completed stages and future roadmap work.

## Current runtime shape

The current runtime uses three main pieces:

1. Devilspie2 runs the active managed Lua file for window events.
2. The managed Lua runtime applies window rules and can optionally launch `d2wc` for unconfigured normal windows.
3. The Python `d2wc` command opens the configurator or prompt and performs managed-file operations.

There is no separate long-running `d2wc` daemon yet.

## Runtime responsibilities

### Devilspie2

Devilspie2 remains the active window-rule engine.

It receives window events from the desktop/window-manager environment, runs the active managed Lua file, exposes window information to Lua, and applies workspace, pinning, and geometry operations through Devilspie2 functions.

Devilspie2 does not present the user-facing configurator.

### Managed Lua runtime

The managed Lua runtime is the active window-rule execution layer.

It currently handles:

1. filtering to normal application windows,
2. reading the Qubes domain when `_QUBES_VMNAME` is available,
3. treating an empty `_QUBES_VMNAME` value as `dom0`,
4. reading and normalizing the application class,
5. applying managed rules,
6. applying left-edge correction when configured,
7. optionally launching `d2wc` for unconfigured normal windows.

The managed Lua runtime is documented in [Lua Configurables](lua-configurables.md) and [Lua Event Handoff](lua-event-handoff.md).

### Python `d2wc` command

The Python command is the user-facing and file-management layer.

It currently provides:

1. `d2wc` as the normal configurator launch command,
2. `d2wc configure` as the explicit configurator subcommand,
3. `d2wc prompt` as the optional event-handoff prompt,
4. parser, validator, renderer, backup, and safe-save logic,
5. GTK configurator workflows for managed rules,
6. File Open and Save As for managed Lua files,
7. settings persistence under `~/.config/d2wc/settings.json`.

User-facing UI behavior is documented in [UI Flow](ui-flow.md). Managed-file behavior is documented in [Managed Config Workflow](managed-config-workflow.md).

### Future daemon/helper process

A future daemon or helper process may be needed for behavior that should not live inside Devilspie2 Lua or the transient configurator process.

Potential responsibilities:

1. starting, verifying, or restarting the managed Devilspie2 process,
2. owning only the `d2wc`-managed Devilspie2 instance,
3. post-resize detection,
4. suppression of resize events caused by `d2wc` itself,
5. optional tray or status entry points,
6. pointer-anchored prompt/menu behavior if prompt mode is expanded,
7. debug logging for runtime behavior.

This future process should not require a permanently visible tray icon. The stable user entry point should remain command-based so users can launch it directly or bind it to a keyboard shortcut.

## Managed file boundary

`d2wc` manages Lua files under:

```text
~/.config/d2wc/lua/
```

Devilspie2 reads the active managed file through:

```text
~/.config/devilspie2/d2wc.lua
```

When managed by `d2wc`, that path is a symlink into `~/.config/d2wc/lua/`.

`d2wc` must not become a generic Devilspie2 Lua editor. It edits managed files that pass the managed-marker and managed-block validation rules.

The active managed-file model is documented in [Managed Config Workflow](managed-config-workflow.md).

## Write safety boundary

All real writes should go through the guarded managed-file path.

The runtime safety model is:

1. parse the managed file,
2. apply the requested change in memory,
3. validate the result,
4. render deterministic Lua,
5. create or update the backup archive,
6. replace the target file only after staging succeeds,
7. report success or failure clearly.

Backup archive behavior and safe-save ordering are documented in [Backup Archives](backup-archives.md).

## Current non-goals

The current public beta baseline does not require:

1. a separate long-running daemon,
2. post-resize automation,
3. ownership of arbitrary user Devilspie2 scripts,
4. a permanently visible tray icon,
5. Wayland-first behavior,
6. a Qt/KDE-specific front end.

Those remain future design areas or compatibility work.

## Future runtime work

Future runtime work should focus on the areas that are not solved by the current command-driven configurator and Lua event handoff.

### Managed Devilspie2 process ownership

The cleanest long-term model is that `d2wc` owns the Devilspie2 instance that runs the managed `d2wc` Lua file.

That would allow `d2wc` to reload or restart only its own managed runtime instead of guessing which arbitrary Devilspie2 process belongs to the user.

Packaging direction for this is documented in [Packaging](packaging.md).

### Post-resize event monitoring

Post-resize behavior remains future work.

A future implementation needs to detect user-initiated resize completion, capture final geometry, apply thresholds, and avoid treating `d2wc`-initiated geometry changes as user edits.

That work is documented in [Event Monitoring](event-monitoring.md).

### Generated split profiles

Generated split profiles remain future work.

A future implementation should generate profiles such as `half_left` and `half_right` from current screen or monitor geometry, preview generated values before writing, and keep generated profiles editable as normal `GEOM` profiles.

The roadmap entry is documented in [Implementation Plan](implementation-plan.md).

### Managed grammar expansion

Current managed rule strings are whitespace-separated prefixed tokens.

Values containing whitespace need a future grammar decision before they can be safely edited or rendered.

The roadmap entry is documented in [Implementation Plan](implementation-plan.md).

## Open architecture questions

Open questions that still need testing or design decisions:

1. How should `d2wc` own and restart only its managed Devilspie2 instance?
2. Which event source best identifies user-initiated resize completion?
3. How should resize-event suppression distinguish user changes from `d2wc` placement changes?
4. Whether optional tray behavior is useful after the command/shortcut entry point is established.
5. How generated split profiles should account for panels, usable work area, and monitor-specific geometry.
6. Whether a later Qt/KDE front end is worth implementing once the core behavior is stable.
